from collections.abc import Iterable
from typing import Literal, TypedDict

from netaddr import IPAddress, IPNetwork
from netaddr.core import AddrFormatError
from sqlalchemy import LargeBinary, String, insert, select
from sqlalchemy.orm import Mapped, backref, mapped_column, relationship

from app import NatlasBase, db
from app.models.dict_serializable import DictSerializable
from app.models.tag import Tag

# Many to many table that ties tags and scopes together
scopetags = db.Table(
    "scopetags",
    db.Column("scope_id", db.Integer, db.ForeignKey("scope_item.id"), primary_key=True),
    db.Column("tag_id", db.Integer, db.ForeignKey("tag.id"), primary_key=True),
)


class ScopeImportResults(TypedDict):
    fail: list[str]
    success: int
    exist: int


class ScopeItem(NatlasBase, DictSerializable):
    __tablename__ = "scope_item"

    id: Mapped[int] = mapped_column(primary_key=True)
    target: Mapped[str | None] = mapped_column(String(128), index=True, unique=True)
    blacklist: Mapped[bool | None] = mapped_column(index=True)
    tags: Mapped[list[Tag]] = relationship(
        secondary=scopetags,
        primaryjoin=(scopetags.c.scope_id == id),
        backref=backref("scope", lazy="select"),
        lazy="select",
    )
    addr_family: Mapped[int | None]
    start_addr: Mapped[bytes | None] = mapped_column(LargeBinary(16))
    stop_addr: Mapped[bytes | None] = mapped_column(LargeBinary(16))

    def __init__(self, target: str, blacklist: bool) -> None:
        self.target = target
        self.blacklist = blacklist
        self.parse_network_range(target)

    def parse_network_range(self, network: str) -> None:
        net = IPNetwork(network)
        self.addr_family = net.version
        size = 4 if net.version == 4 else 16
        self.start_addr = net.first.to_bytes(size, byteorder="big")
        self.stop_addr = net.last.to_bytes(size, byteorder="big")

    @staticmethod
    def get_overlapping_ranges(addr: str) -> list["ScopeItem"]:
        ipaddr = IPAddress(addr)
        size = 4 if ipaddr.version == 4 else 16
        binval = ipaddr.value.to_bytes(size, byteorder="big")
        return list(
            db.session.scalars(
                select(ScopeItem).where(
                    ScopeItem.addr_family == ipaddr.version,
                    ScopeItem.start_addr <= binval,
                    ScopeItem.stop_addr >= binval,
                )
            ).all()
        )

    def addTag(self, tag: Tag) -> None:
        if not self.is_tagged(tag):
            self.tags.append(tag)

    def delTag(self, tag: Tag) -> None:
        if self.is_tagged(tag):
            self.tags.remove(tag)

    def is_tagged(self, tag: Tag) -> bool:
        return tag in self.tags

    def get_tag_names(self) -> list[str]:
        return [tag.name for tag in self.tags]

    @staticmethod
    def getBlacklist() -> list["ScopeItem"]:
        return list(
            db.session.scalars(
                select(ScopeItem).where(ScopeItem.blacklist == True)
            ).all()
        )

    @staticmethod
    def getScope() -> list["ScopeItem"]:
        return list(
            db.session.scalars(
                select(ScopeItem).where(ScopeItem.blacklist == False)
            ).all()
        )

    @staticmethod
    def addTags(scopeitem: "ScopeItem", tags: Iterable[str]) -> None:
        from app.models import Tag

        for tag in tags:
            if tag.strip() == "":  # If the tag is an empty string then don't use it
                continue
            tag_obj = Tag.create_if_none(tag)
            scopeitem.addTag(tag_obj)

    @staticmethod
    def parse_tags(tags: Iterable[str]) -> list[str]:
        out = []
        for t in tags:
            if t.strip() == "":
                continue
            out.append(t)
        return out

    @staticmethod
    def parse_import_line(line: str) -> tuple[IPNetwork, list[str]]:
        splitline = line.split(",")
        tags = []
        if len(splitline) > 1:
            ip = splitline[0]
            tags = ScopeItem.parse_tags(splitline[1:])
        else:
            ip = line
        validated_ip = ScopeItem.validate_ip(ip)
        return validated_ip, tags

    @staticmethod
    def extract_import_tags(import_list: list[str]) -> Iterable[str]:
        out = set()
        for line in import_list:
            split = line.split(",")
            if len(split) > 1:
                tags = ScopeItem.parse_tags(split[1:])
                out.update(tags)
        return out

    @staticmethod
    def validate_ip(ip: str) -> IPNetwork | Literal[False]:
        try:
            return IPNetwork(ip)
        except AddrFormatError:
            return False

    @staticmethod
    def import_scope_list(
        address_list: Iterable[str], blacklist: bool
    ) -> ScopeImportResults:
        result: ScopeImportResults = {"fail": [], "success": 0, "exist": 0}
        prefixes = {"sqlite": " OR IGNORE", "mysql": " IGNORE"}
        selected_prefix = prefixes.get(db.engine.dialect.name)
        scope_import = {}
        scope_tag_import = {}
        address_list = [line.strip() for line in address_list]
        tags = ScopeItem.extract_import_tags(address_list)
        tag_dict = {}
        from app.models import Tag

        for tag in tags:
            tag_dict[tag] = Tag.create_if_none(tag)
        db.session.commit()
        for line in address_list:
            ip, tags = ScopeItem.parse_import_line(line)
            if not ip:
                result["fail"].append(line)
                continue
            tags = [tag_dict[tag] for tag in tags]  # type: ignore[misc]
            item = ScopeItem(target=str(ip), blacklist=blacklist).as_dict()
            scope_tag_import[item["target"]] = tags
            scope_import[item["target"]] = item
        import_list = [v for _, v in scope_import.items()]
        chunk_size = 10000
        import_chunks = [
            import_list[i : i + chunk_size]
            for i in range(0, len(import_list), chunk_size)
        ]
        for chunk in import_chunks:
            ins_stmt = (
                insert(ScopeItem)
                .prefix_with(selected_prefix)  # type: ignore[arg-type]
                .values(chunk)
            )
            ins_result = db.session.execute(ins_stmt)
            result["success"] = int(result["success"]) + ins_result.rowcount
        result["exist"] = len(address_list) - len(result["fail"]) - result["success"]
        all_scope = {
            item.target: item.id for item in db.session.scalars(select(ScopeItem)).all()
        }
        tags_to_import = []
        for k, v in scope_tag_import.items():
            for tag in v:
                tags_to_import.append({"scope_id": all_scope[k], "tag_id": tag.id})  # type: ignore[attr-defined]
        import_chunks = [
            tags_to_import[i : i + chunk_size]
            for i in range(0, len(tags_to_import), chunk_size)
        ]
        for chunk in import_chunks:
            tag_stmt = scopetags.insert().prefix_with(selected_prefix).values(chunk)  # type: ignore[arg-type]
            db.session.execute(tag_stmt)
        db.session.commit()
        return result
