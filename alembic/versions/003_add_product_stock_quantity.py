"""add product stock_quantity

Revision ID: 003
Revises: 002
Create Date: 2026-05-26

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "products",
        sa.Column("stock_quantity", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_check_constraint("ck_products_stock_quantity_non_negative", "products", "stock_quantity >= 0")


def downgrade() -> None:
    op.drop_constraint("ck_products_stock_quantity_non_negative", "products", type_="check")
    op.drop_column("products", "stock_quantity")
