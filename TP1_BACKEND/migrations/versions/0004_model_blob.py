"""contenido del modelo en la BD (el Champion sobrevive a discos efímeros)

Revision ID: 0004
Revises: 0003
Create Date: 2026-11-16 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0004'
down_revision: Union[str, Sequence[str], None] = '0003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('ml_model_versions', sa.Column('model_blob', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('ml_model_versions', 'model_blob')
