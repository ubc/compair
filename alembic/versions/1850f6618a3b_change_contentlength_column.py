"""Change_contentLength_column

Revision ID: 1850f6618a3b
Revises: 1cdbdd936df8
Create Date: 2013-12-12 12:59:03.879099

"""

# revision identifiers, used by Alembic.
revision = '1850f6618a3b'
down_revision = '1cdbdd936df8'

from alembic import op
import sqlalchemy as sa
from sqlalchemy import INTEGER
from sqlalchemy.sql import table, column

def upgrade():
    op.drop_column('Question', 'contentLength')
    op.add_column('Course', sa.Column('contentLength', INTEGER, default=0))
    course = table('Course', column("contentLength", INTEGER))
    op.execute(course.update().values(contentLength = 0))

def downgrade():
    op.drop_column('Course', 'contentLength')
    op.add_column('Question', sa.Column('contentLength', INTEGER, default=0))
