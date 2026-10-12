"""add defect tracking provenance and verification columns

Revision ID: c8e9f1a2b3c4
Revises: b7d8c1e2f3a4
"""
from alembic import op
import sqlalchemy as sa

revision = 'c8e9f1a2b3c4'
down_revision = 'b7d8c1e2f3a4'
branch_labels = None
depends_on = None

def upgrade():
    # Safe inspection for SQLite or PostgreSQL
    conn = op.get_bind()
    insp = sa.inspect(conn)
    existing_cols = [c['name'] for c in insp.get_columns('issues')]
    
    if 'detected_defects_json' not in existing_cols:
        op.add_column('issues', sa.Column('detected_defects_json', sa.Text(), nullable=True))
    if 'model_provenance_json' not in existing_cols:
        op.add_column('issues', sa.Column('model_provenance_json', sa.Text(), nullable=True))
    if 'verified_category' not in existing_cols:
        op.add_column('issues', sa.Column('verified_category', sa.String(length=100), nullable=True))
    if 'ai_analysis_status' not in existing_cols:
        op.add_column('issues', sa.Column('ai_analysis_status', sa.String(length=50), nullable=True))

def downgrade():
    pass
