"""Add student number to lti user

Revision ID: a91d59c2cfd5
Revises: 2561c39ac4d9
Create Date: 2018-03-19 20:38:57.068934

"""

# revision identifiers, used by Alembic.
revision = 'a91d59c2cfd5'
down_revision = '2561c39ac4d9'

from alembic import op
import sqlalchemy as sa

from compair.models import convention

def upgrade():
    with op.batch_alter_table('lti_consumer', naming_convention=convention) as batch_op:
        batch_op.add_column(sa.Column('student_number_param', sa.String(length=255), nullable=True))

    with op.batch_alter_table('lti_user', naming_convention=convention) as batch_op:
        batch_op.add_column(sa.Column('student_number', sa.String(length=255), nullable=True))


def downgrade():
    with op.batch_alter_table('lti_user', naming_convention=convention) as batch_op:
        batch_op.drop_column('student_number')

    with op.batch_alter_table('lti_consumer', naming_convention=convention) as batch_op:
        batch_op.drop_column('student_number_param')