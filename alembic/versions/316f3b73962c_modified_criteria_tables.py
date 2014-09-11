"""modified criteria tables

Revision ID: 316f3b73962c
Revises: 2fe3d8183c34
Create Date: 2014-09-10 15:42:55.963855

"""

# revision identifiers, used by Alembic.
revision = '316f3b73962c'
down_revision = '2fe3d8183c34'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text

def upgrade():

	op.drop_constraint('name', 'Criteria', type_='unique')
	# set existing criteria's active attribute to True using server_default
	op.add_column('CriteriaAndCourses', sa.Column('active', sa.Boolean(), default=True, server_default='1', nullable=False))
	op.add_column('Criteria', sa.Column('public', sa.Boolean, default=False, server_default='0', nullable=False))

	# set the first criteria as public
	t = {"name": "Which is better?", "public": True }
	op.get_bind().execute(text("Update Criteria set public=:public where name=:name ORDER BY Criteria.id LIMIT 1"), **t)

def downgrade():
	op.drop_column('CriteriaAndCourses', 'active')
	op.create_unique_constraint(u'name', 'Criteria', ['name'])
	op.drop_column('Criteria', 'public')