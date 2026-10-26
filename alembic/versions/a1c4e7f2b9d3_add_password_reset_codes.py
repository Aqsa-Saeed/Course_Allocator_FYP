"""add password reset codes

Revision ID: a1c4e7f2b9d3
Revises: 6bfce982bdab
Create Date: 2026-10-24 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1c4e7f2b9d3'
down_revision = '6bfce982bdab'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('password_reset_codes',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('code_hash', sa.String(length=64), nullable=False),
    sa.Column('expires_at', sa.DateTime(), nullable=False),
    sa.Column('attempts', sa.Integer(), server_default='0', nullable=False),
    sa.Column('used_at', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_password_reset_codes_user_id', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_password_reset_codes_user_id', 'password_reset_codes', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_password_reset_codes_user_id', table_name='password_reset_codes')
    op.drop_table('password_reset_codes')
