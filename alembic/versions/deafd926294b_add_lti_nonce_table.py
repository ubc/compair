"""Add lti_nonce table

Revision ID: deafd926294b
Revises: 485ff3eedf19
Create Date: 2016-08-11 11:59:18.546501

"""

# revision identifiers, used by Alembic.
revision = 'deafd926294b'
down_revision = '485ff3eedf19'

from alembic import op
import sqlalchemy as sa

def upgrade():
    op.create_table('lti_nonce',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('lti_consumer_id', sa.Integer(), nullable=False),
        sa.Column('oauth_nonce', sa.String(length=255), nullable=False),
        sa.Column('oauth_timestamp', sa.TIMESTAMP(), nullable=False),
        sa.Column('modified_user_id', sa.Integer(), nullable=True),
        sa.Column('modified', sa.DateTime(), nullable=False),
        sa.Column('created_user_id', sa.Integer(), nullable=True),
        sa.Column('created', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['created_user_id'], ['user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['lti_consumer_id'], ['lti_consumer.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['modified_user_id'], ['user.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('lti_consumer_id', 'oauth_nonce', 'oauth_timestamp', name='_unique_lti_consumer_nonce_and_timestamp'),
        mysql_charset='utf8',
        mysql_collate='utf8_unicode_ci',
        mysql_engine='InnoDB'
    )

def downgrade():
    op.drop_table('lti_nonce')