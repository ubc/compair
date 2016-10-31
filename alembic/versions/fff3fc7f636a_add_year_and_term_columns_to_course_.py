"""Add year and term columns to course table

Revision ID: fff3fc7f636a
Revises: 144167b8fb35
Create Date: 2016-07-12 11:09:13.082366

"""

# revision identifiers, used by Alembic.
revision = 'fff3fc7f636a'
down_revision = '144167b8fb35'

from alembic import op
import sqlalchemy as sa
from sqlalchemy import UniqueConstraint, exc
from sqlalchemy.dialects import mysql

from compair.models import convention

def upgrade():
    op.add_column('course', sa.Column('year', sa.Integer(), nullable=False, default='2015', server_default='2015'))
    op.add_column('course', sa.Column('term', sa.String(length=255), nullable=False, default='', server_default=''))

    try:
        with op.batch_alter_table('course', naming_convention=convention,
                table_args=(UniqueConstraint('name'))) as batch_op:
            batch_op.drop_constraint('uq_course_name', type_='unique')
    except exc.InternalError:
        with op.batch_alter_table('course', naming_convention=convention,
                table_args=(UniqueConstraint('name'))) as batch_op:
            batch_op.drop_constraint('name', type_='unique')
    except ValueError:
        logging.warning('Drop unique constraint is not support for SQLite, dropping uq_course_name ignored!')

def downgrade():
    with op.batch_alter_table('course', naming_convention=convention,
            table_args=(UniqueConstraint('name'))) as batch_op:
        batch_op.drop_column('term')
        batch_op.drop_column('year')
        batch_op.create_unique_constraint('uq_course_name', ['name'])