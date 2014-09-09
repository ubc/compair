"""Remove rounds from AnswerPairings

Revision ID: 2fe3d8183c34
Revises: 1c7acaadfcfc
Create Date: 2014-09-09 14:13:29.979783

"""

# revision identifiers, used by Alembic.
revision = '2fe3d8183c34'
down_revision = '1c7acaadfcfc'

from alembic import op
import sqlalchemy as sa


def upgrade():
	op.drop_column('AnswerPairings', 'round')


def downgrade():
	op.add_column('AnswerPairings',
		sa.Column('round', sa.Integer, default=1)
	)
