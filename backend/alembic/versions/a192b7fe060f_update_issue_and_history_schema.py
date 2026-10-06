"""add workflow fields

Revision ID: a192b7fe060f
Revises: 042df7e1d76d
"""
from alembic import op
import sqlalchemy as sa
revision='a192b7fe060f'
down_revision='042df7e1d76d'
branch_labels=None
depends_on=None
def upgrade():
    op.add_column('issues',sa.Column('assigned_officer_id',sa.Integer(),sa.ForeignKey('users.id'),nullable=True))
    op.add_column('issues',sa.Column('assigned_at',sa.DateTime(),nullable=True))
    op.add_column('issues',sa.Column('progress_percentage',sa.Integer(),server_default='0',nullable=False))
    op.add_column('issues',sa.Column('latest_update',sa.Text(),nullable=True))
    op.add_column('issues',sa.Column('estimated_completion_date',sa.DateTime(),nullable=True))
    op.add_column('issues',sa.Column('resolved_at',sa.DateTime(),nullable=True))
    op.add_column('issues',sa.Column('closed_at',sa.DateTime(),nullable=True))
    op.add_column('issue_status_history',sa.Column('progress_percentage',sa.Integer(),nullable=True))
def downgrade():
    op.drop_column('issue_status_history','progress_percentage')
    for c in ['closed_at','resolved_at','estimated_completion_date','latest_update','progress_percentage','assigned_at','assigned_officer_id']:
        op.drop_column('issues',c)
