"""Added custom_context_memberships_url column to lti_context table

Revision ID: 2a19cb1ab324
Revises: 852abaee3a25
Create Date: 2017-06-23 19:10:05.295553

"""

# revision identifiers, used by Alembic.
revision = '2a19cb1ab324'
down_revision = '852abaee3a25'

from alembic import op
import sqlalchemy as sa

from compair.models import convention

def upgrade():
    with op.batch_alter_table('lti_consumer', naming_convention=convention) as batch_op:
        batch_op.add_column(sa.Column('canvas_consumer', sa.Boolean(), nullable=False, default=False, server_default='0'))
        batch_op.add_column(sa.Column('canvas_api_token', sa.String(255), nullable=True))

    with op.batch_alter_table('lti_context', naming_convention=convention) as batch_op:
        batch_op.add_column(sa.Column('custom_context_memberships_url', sa.Text(), nullable=True))

def downgrade():
    with op.batch_alter_table('lti_context', naming_convention=convention) as batch_op:
        batch_op.drop_column('custom_context_memberships_url')

    with op.batch_alter_table('lti_consumer', naming_convention=convention) as batch_op:
        batch_op.drop_column('canvas_api_token')
        batch_op.drop_column('canvas_consumer')