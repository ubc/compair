"""Add uuid to lti_consumer table

Revision ID: 6802122e6f53
Revises: 12167f268066
Create Date: 2017-01-06 00:54:17.258870

"""

# revision identifiers, used by Alembic.
revision = '6802122e6f53'
down_revision = '12167f268066'

from alembic import op
import sqlalchemy as sa
import uuid
import base64

from compair.models import convention

def upgrade():
    # step 1, add new uuid column
    op.add_column('lti_consumer', sa.Column('uuid', sa.CHAR(22), nullable=False, server_default=''))

    connection = op.get_bind()
    # step 2, fill in unique uuids (base64 url safe strings)
    lti_consumer_table = sa.table('lti_consumer', sa.Column('id', sa.Integer()), sa.Column('uuid', sa.CHAR(22)))
    for record in connection.execute(lti_consumer_table.select()):
        connection.execute(
            lti_consumer_table.update()
            .where(lti_consumer_table.c.id == record.id)
            .values(uuid=base64.urlsafe_b64encode(uuid.uuid4().bytes).decode('ascii').replace('=', ''))
        )

    # step 3, apply unique constraint on generated table
    with op.batch_alter_table('lti_consumer', naming_convention=convention) as batch_op:
        batch_op.create_unique_constraint("uq_lti_consumer_uuid", ['uuid'])
        batch_op.alter_column('lti_version',
               existing_type=sa.String(20),
               nullable=True)

def downgrade():
    with op.batch_alter_table('lti_consumer', naming_convention=convention) as batch_op:
        batch_op.drop_constraint("uq_lti_consumer_uuid", type_='unique')
        batch_op.drop_column('uuid')
        batch_op.alter_column('lti_version',
               existing_type=sa.String(20),
               nullable=False)