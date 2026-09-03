"""Adicionando etapas de tarefas

Revision ID: 9681bf3a0dab
Revises: 938590e18b88
Create Date: 2026-09-05 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9681bf3a0dab'
down_revision: Union[str, Sequence[str], None] = '938590e18b88'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'etapas',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('descricao', sa.String(length=300), nullable=False),
        sa.Column('concluida', sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=False),
        sa.Column('tarefa_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['tarefa_id'], ['tarefas.id'], name='fk_etapas_tarefa_id', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('etapas')
    # ### end Alembic commands ###
