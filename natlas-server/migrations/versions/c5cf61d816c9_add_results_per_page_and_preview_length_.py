"""Add results_per_page and preview_length to user

Revision ID: c5cf61d816c9
Revises: 997bbd9a505a
Create Date: 2019-02-05 17:28:14.965988

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "c5cf61d816c9"
down_revision = "997bbd9a505a"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "user",
        sa.Column("preview_length", sa.Integer(), server_default="100", nullable=True),
    )
    op.add_column(
        "user",
        sa.Column(
            "results_per_page", sa.Integer(), server_default="100", nullable=True
        ),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("user", "results_per_page")
    op.drop_column("user", "preview_length")
    # ### end Alembic commands ###
