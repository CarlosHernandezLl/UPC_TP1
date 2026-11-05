"""impacto SHAP por variable en ml_model_versions

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-04 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0002'
down_revision: Union[str, Sequence[str], None] = '0001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('ml_model_versions', sa.Column('feature_importance', sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column('ml_model_versions', 'feature_importance')
