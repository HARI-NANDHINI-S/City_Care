"""add CLOSED issue status

Revision ID: b7d8c1e2f3a4
Revises: 9a73caef4e09
"""
from alembic import op
import sqlalchemy as sa
revision='b7d8c1e2f3a4'
down_revision='9a73caef4e09'
branch_labels=None
depends_on=None
def upgrade():
    bind=op.get_bind()
    if bind.dialect.name=='postgresql':
        op.execute("ALTER TYPE issuestatus ADD VALUE IF NOT EXISTS 'CLOSED'")
def downgrade():
    pass
