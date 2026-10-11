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
    conn = op.get_bind()
    existing_issue_cols = [c['name'] for c in sa.inspect(conn).get_columns('issues')]
    with op.batch_alter_table('issues') as batch_op:
        if 'assigned_officer_id' not in existing_issue_cols:
            batch_op.add_column(sa.Column('assigned_officer_id', sa.Integer(), nullable=True))
        if 'assigned_at' not in existing_issue_cols:
            batch_op.add_column(sa.Column('assigned_at', sa.DateTime(), nullable=True))
        if 'progress_percentage' not in existing_issue_cols:
            batch_op.add_column(sa.Column('progress_percentage', sa.Integer(), server_default='0', nullable=False))
        if 'latest_update' not in existing_issue_cols:
            batch_op.add_column(sa.Column('latest_update', sa.Text(), nullable=True))
        if 'estimated_completion_date' not in existing_issue_cols:
            batch_op.add_column(sa.Column('estimated_completion_date', sa.DateTime(), nullable=True))
        if 'resolved_at' not in existing_issue_cols:
            batch_op.add_column(sa.Column('resolved_at', sa.DateTime(), nullable=True))
        if 'closed_at' not in existing_issue_cols:
            batch_op.add_column(sa.Column('closed_at', sa.DateTime(), nullable=True))

    existing_history_cols = [c['name'] for c in sa.inspect(conn).get_columns('issue_status_history')]
    with op.batch_alter_table('issue_status_history') as batch_op:
        if 'progress_percentage' not in existing_history_cols:
            batch_op.add_column(sa.Column('progress_percentage', sa.Integer(), nullable=True))

def downgrade():
    with op.batch_alter_table('issue_status_history') as batch_op:
        batch_op.drop_column('progress_percentage')
    with op.batch_alter_table('issues') as batch_op:
        for c in ['closed_at', 'resolved_at', 'estimated_completion_date', 'latest_update', 'progress_percentage', 'assigned_at', 'assigned_officer_id']:
            batch_op.drop_column(c)

