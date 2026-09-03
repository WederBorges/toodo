"""Adicionando verificação de email e redefinição de senha

Revision ID: 938590e18b88
Revises: 7616f4216e24
Create Date: 2026-09-03 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '938590e18b88'
down_revision: Union[str, Sequence[str], None] = '7616f4216e24'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('user_account', schema=None) as batch_op:
        # server_default=true() garante que contas já existentes fiquem
        # marcadas como verificadas (não exige re-confirmação retroativa).
        # Cadastros novos passam email_verified=False explicitamente no código.
        batch_op.add_column(sa.Column('email_verified', sa.Boolean(), server_default=sa.true(), nullable=False))

    op.create_table(
        'email_tokens',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('token_hash', sa.String(length=64), nullable=False),
        sa.Column('purpose', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=False),
        sa.Column('expires_at', sa.TIMESTAMP(), nullable=False),
        sa.Column('used_at', sa.TIMESTAMP(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['user_account.id'], name='fk_email_tokens_user_id', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token_hash', name='uq_email_tokens_token_hash'),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('email_tokens')

    with op.batch_alter_table('user_account', schema=None) as batch_op:
        batch_op.drop_column('email_verified')
    # ### end Alembic commands ###
