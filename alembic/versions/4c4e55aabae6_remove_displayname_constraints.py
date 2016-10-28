"""remove displayname constraints

Revision ID: 4c4e55aabae6
Revises: ac2bd4b2c95
Create Date: 2015-01-14 09:39:10.403476

"""

# revision identifiers, used by Alembic.
revision = '4c4e55aabae6'
down_revision = 'ac2bd4b2c95'

from alembic import op
import sqlalchemy as sa

from compair.models import convention
import logging
from sqlalchemy import UniqueConstraint, exc


def upgrade():
    try:
        with op.batch_alter_table(
                'Users', naming_convention=convention,
                table_args=(UniqueConstraint('displayname'))) as batch_op:
            batch_op.drop_constraint('uq_Users_displayname', 'unique')
            batch_op.alter_column('displayname', nullable=False, existing_type=sa.String(length=255))
    except exc.InternalError:
        with op.batch_alter_table(
                'Users', naming_convention=convention,
                table_args=(UniqueConstraint('displayname'))) as batch_op:
            batch_op.drop_constraint('displayname', type_='unique')
            batch_op.alter_column('displayname', nullable=False, existing_type=sa.String(length=255))
    except ValueError:
        logging.warning('Drop unique constraint is not support for SQLite, dropping uq_Users_displayname ignored!')


def downgrade():
    with op.batch_alter_table(
            'Users', naming_convention=convention) as batch_op:
        batch_op.create_unique_constraint('uq_Users_displayname', ['displayname'])
        batch_op.alter_column('displayname', nullable=True, existing_type=sa.String(length=255))
