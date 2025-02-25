"""scopetags

Revision ID: e59d726ef9c1
Revises: b9aebd0a8593
Create Date: 2019-03-26 12:31:44.187235

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "e59d726ef9c1"
down_revision = "b9aebd0a8593"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "tag",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_tag_name"), "tag", ["name"], unique=True)
    op.create_table(
        "scopetags",
        sa.Column("scope_id", sa.Integer(), nullable=False),
        sa.Column("tag_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["scope_id"], ["scope_item.id"]),
        sa.ForeignKeyConstraint(["tag_id"], ["tag.id"]),
        sa.PrimaryKeyConstraint("scope_id", "tag_id"),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("scopetags")
    op.drop_index(op.f("ix_tag_name"), table_name="tag")
    op.drop_table("tag")
    # ### end Alembic commands ###
