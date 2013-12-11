"""Changes to user roles

Revision ID: 1cdbdd936df8
Revises: 573c88e973e
Create Date: 2013-12-11 13:28:46.774534

"""

# revision identifiers, used by Alembic.
revision = '1cdbdd936df8'
down_revision = '573c88e973e'

from alembic import op
import sqlalchemy as sa
from sqlalchemy import INTEGER


def upgrade():
    op.add_column('Enrollment', sa.Column('usertype', Integer, ForeignKey('UserRole.id')))
    op.drop_column('User', 'usertype')
    op.add_column('User', sa.Column('usertype', INTEGER, ForeignKey('UserRole.id')))


def downgrade():
    op.drop_column('Enrollment', 'usertype')
    op.drop_column('User', 'usertype')
    op.add_column('User', sa.Column('usertype', String(100)))
