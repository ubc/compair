"""Add uuid to lti_user, lti_context, and third_party_user

Revision ID: 20381bf0bd54
Revises: 82ed8fc51745
Create Date: 2017-10-05 23:02:57.724462

"""

# revision identifiers, used by Alembic.
revision = '20381bf0bd54'
down_revision = '82ed8fc51745'

from alembic import op
import sqlalchemy as sa
import uuid
import base64

from compair.models import convention

table_names = ['lti_context', 'lti_user', 'third_party_user']

def upgrade():
    connection = op.get_bind()

    # add uuid column and unique constraint for each table
    for table_name in table_names:
        # step 1, add new uuid column
        op.add_column(table_name, sa.Column('uuid', sa.CHAR(22), nullable=False, server_default=''))

        # step 2, fill in unique uuids (base64 url safe strings)
        table = sa.table(table_name, sa.Column('id', sa.Integer()), sa.Column('uuid', sa.CHAR(22)))
        for record in connection.execute(table.select()):
            connection.execute(
                table.update()
                .where(table.c.id == record.id)
                .values(uuid=base64.urlsafe_b64encode(uuid.uuid4().bytes).decode('ascii').replace('=', ''))
            )

        # step 3, apply unique constraint on generated table
        with op.batch_alter_table(table_name, naming_convention=convention) as batch_op:
            batch_op.create_unique_constraint("uq_"+table_name+"_uuid", ['uuid'])

def downgrade():
    # drop uuid unique constraint and column for each table
    for table_name in table_names:
        with op.batch_alter_table(table_name, naming_convention=convention) as batch_op:
            batch_op.drop_constraint("uq_"+table_name+"_uuid", type_='unique')
            batch_op.drop_column('uuid')