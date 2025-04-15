"""Add name_pinyin column to shops

Revision ID: 080d6fed4883
Revises: 8a6edd25c287
Create Date: 2025-04-15 14:21:53.924528

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '080d6fed4883'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column('shops', sa.Column('name_pinyin', sa.String(length=100), nullable=True))
    op.create_index(op.f('ix_shops_name_pinyin'), 'shops', ['name_pinyin'], unique=False)

def downgrade():
    op.drop_index(op.f('ix_shops_name_pinyin'), table_name='shops')
    op.drop_column('shops', 'name_pinyin')
