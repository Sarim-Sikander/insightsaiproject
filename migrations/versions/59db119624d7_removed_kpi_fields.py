"""Removed kpi fields

Revision ID: 59db119624d7
Revises: 16d029ce15c8
Create Date: 2025-01-17 16:58:14.123320

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = "59db119624d7"
down_revision: Union[str, None] = "16d029ce15c8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("documents", "revenue_growth_rate")
    op.drop_column("documents", "operational_cost_reduction")
    op.drop_column("documents", "revenue")
    op.drop_column("documents", "net_profit")
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("documents", sa.Column("net_profit", mysql.FLOAT(), nullable=True))
    op.add_column("documents", sa.Column("revenue", mysql.FLOAT(), nullable=True))
    op.add_column(
        "documents",
        sa.Column("operational_cost_reduction", mysql.FLOAT(), nullable=True),
    )
    op.add_column(
        "documents", sa.Column("revenue_growth_rate", mysql.FLOAT(), nullable=True)
    )
    # ### end Alembic commands ###
