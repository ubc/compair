"""Add custom_param_regex_sanitizer to lti_consumer

Revision ID: bb705e95c6dc
Revises: fd7aab93104b
Create Date: 2021-07-09 16:51:06.901761

"""

# revision identifiers, used by Alembic.
revision = 'bb705e95c6dc'
down_revision = 'fd7aab93104b'

from alembic import op
import sqlalchemy as sa

from compair.models import convention


def upgrade():
    with op.batch_alter_table('lti_consumer', naming_convention=convention) as batch_op:
        batch_op.add_column(sa.Column('custom_param_regex_sanitizer', sa.String(length=255), nullable=True))


def downgrade():
    with op.batch_alter_table('lti_consumer', naming_convention=convention) as batch_op:
        batch_op.drop_column('custom_param_regex_sanitizer')
