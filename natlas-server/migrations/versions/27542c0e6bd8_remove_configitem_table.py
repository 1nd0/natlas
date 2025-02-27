"""Remove ConfigItem table

Revision ID: 27542c0e6bd8
Revises: 7099debf8cda
Create Date: 2025-01-16 06:14:21.220004

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "27542c0e6bd8"
down_revision = "7099debf8cda"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("config_item")

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "config_item",
        sa.Column("id", sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column("name", sa.VARCHAR(length=256), autoincrement=False, nullable=True),
        sa.Column("type", sa.VARCHAR(length=256), autoincrement=False, nullable=True),
        sa.Column("value", sa.VARCHAR(length=256), autoincrement=False, nullable=True),
        sa.PrimaryKeyConstraint("id", name="config_item_pkey"),
        sa.UniqueConstraint("name", name="config_item_name_key"),
    )
    # ### end Alembic commands ###
