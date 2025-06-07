"""Add length to content fields

Revision ID: 98b4d364bd2e
Revises: bed23f19817a
Create Date: 2025-06-04 08:43:32.641101

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '98b4d364bd2e'
down_revision: Union[str, None] = 'bed23f19817a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 检查 reviews 表是否存在
    if not op.get_bind().dialect.has_table(op.get_bind(), 'reviews'):
        op.create_table('reviews',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('shop_id', sa.Integer(), nullable=False),
            sa.Column('content', sa.String(length=255), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['shop_id'], ['shops.id'], ),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        with op.batch_alter_table('reviews', schema=None) as batch_op:
            batch_op.create_index(batch_op.f('ix_reviews_id'), ['id'], unique=False)
    else:
        # 如果表存在，检查 content 字段是否需要更新
        op.alter_column('reviews', 'content', existing_type=sa.String(255), nullable=False)

    # 检查 review_replies 表是否存在
    if not op.get_bind().dialect.has_table(op.get_bind(), 'review_replies'):
        op.create_table('review_replies',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('review_id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('content', sa.String(length=255), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('parent_reply_id', sa.Integer(), nullable=True),
            sa.ForeignKeyConstraint(['parent_reply_id'], ['review_replies.id'], ),
            sa.ForeignKeyConstraint(['review_id'], ['reviews.id'], ),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        with op.batch_alter_table('review_replies', schema=None) as batch_op:
            batch_op.create_index(batch_op.f('ix_review_replies_id'), ['id'], unique=False)

    with op.batch_alter_table('users', schema=None) as batch_op:
        if not batch_op.get_column('invitation_code'):
            batch_op.add_column(sa.Column('invitation_code', sa.String(length=6), nullable=False))
            batch_op.create_unique_constraint(None, ['invitation_code'])
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='unique')
        batch_op.drop_column('invitation_code')

    if op.get_bind().dialect.has_table(op.get_bind(), 'review_replies'):
        with op.batch_alter_table('review_replies', schema=None) as batch_op:
            batch_op.drop_index(batch_op.f('ix_review_replies_id'))
        op.drop_table('review_replies')

    if op.get_bind().dialect.has_table(op.get_bind(), 'reviews'):
        with op.batch_alter_table('reviews', schema=None) as batch_op:
            batch_op.drop_index(batch_op.f('ix_reviews_id'))
        op.drop_table('reviews')
        # ### end Alembic commands ###
