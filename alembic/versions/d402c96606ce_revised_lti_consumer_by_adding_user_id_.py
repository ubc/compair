"""Revised LTI consumer by adding user_id_override and removing canvas_consumer and canvas_api_token

Revision ID: d402c96606ce
Revises: 2a19cb1ab324
Create Date: 2017-07-14 00:02:05.424665

"""

# revision identifiers, used by Alembic.
revision = 'd402c96606ce'
down_revision = '2a19cb1ab324'

from alembic import op
import sqlalchemy as sa

from compair.models import convention

def upgrade():
    with op.batch_alter_table('lti_consumer', naming_convention=convention) as batch_op:
        batch_op.drop_column('canvas_api_token')
        batch_op.drop_column('canvas_consumer')
        batch_op.add_column(sa.Column('user_id_override', sa.String(255), nullable=True))

def downgrade():
    with op.batch_alter_table('lti_consumer', naming_convention=convention) as batch_op:
        batch_op.add_column(sa.Column('canvas_consumer', sa.Boolean(), nullable=False, default=False, server_default='0'))
        batch_op.add_column(sa.Column('canvas_api_token', sa.String(255), nullable=True))
        batch_op.drop_column('user_id_override')
