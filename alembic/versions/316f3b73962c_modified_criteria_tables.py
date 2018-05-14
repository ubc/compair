"""modified criteria tables

Revision ID: 316f3b73962c
Revises: 2fe3d8183c34
Create Date: 2014-09-10 15:42:55.963855

"""

# revision identifiers, used by Alembic.
revision = '316f3b73962c'
down_revision = '2fe3d8183c34'

import logging
from alembic import op
import sqlalchemy as sa
from sqlalchemy import UniqueConstraint, exc
from sqlalchemy.sql import text

from compair.models import convention


def upgrade():
    try:
        with op.batch_alter_table('Criteria', naming_convention=convention,
                                  table_args=(UniqueConstraint('name'))) as batch_op:
            batch_op.drop_constraint('uq_Criteria_name', type_='unique')
    except exc.InternalError:
        with op.batch_alter_table('Criteria', naming_convention=convention,
                                  table_args=(UniqueConstraint('name'))) as batch_op:
            batch_op.drop_constraint('name', type_='unique')
    except ValueError:
        logging.warning('Drop unique constraint is not support for SQLite, dropping uq_Critiera_name ignored!')

    # set existing criteria's active attribute to True using server_default
    with op.batch_alter_table('CriteriaAndCourses', naming_convention=convention) as batch_op:
        batch_op.add_column(sa.Column('active', sa.Boolean(), default=True, server_default='1', nullable=False))
    with op.batch_alter_table('Criteria', naming_convention=convention) as batch_op:
        batch_op.add_column(sa.Column('public', sa.Boolean(), default=False, server_default='0', nullable=False))

    # set the first criteria as public
    t = {"name": "Which is better?", "public": True}
    op.get_bind().execute(text("Update Criteria set public=:public where name=:name"), **t)


def downgrade():
    with op.batch_alter_table('Criteria', naming_convention=convention,
                              table_args=(UniqueConstraint('name'))) as batch_op:
        batch_op.create_unique_constraint('uq_Criteria_name', ['name'])
        batch_op.drop_column('public')
    with op.batch_alter_table('CriteriaAndCourses', naming_convention=convention) as batch_op:
        batch_op.drop_column('active')
