"""Add email_notification_method to user table

Revision ID: 852abaee3a25
Revises: d2cfb4363907
Create Date: 2017-04-27 18:34:51.728465

"""

# revision identifiers, used by Alembic.
revision = '852abaee3a25'
down_revision = 'd2cfb4363907'

from alembic import op
import sqlalchemy as sa
from sqlalchemy_enum34 import EnumType

from compair.models import convention, EmailNotificationMethod

def upgrade():
    op.add_column('user', sa.Column('email_notification_method',
        EnumType(EmailNotificationMethod, name='email_notification_method'),
        default=EmailNotificationMethod.enable, server_default=EmailNotificationMethod.enable.value,
        nullable=False, index=True))


def downgrade():
    with op.batch_alter_table('user', naming_convention=convention) as batch_op:
        batch_op.drop_index('ix_user_email_notification_method')
        batch_op.drop_column('email_notification_method')