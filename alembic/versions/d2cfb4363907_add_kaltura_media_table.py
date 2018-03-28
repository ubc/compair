"""add kaltura_media table

Revision ID: d2cfb4363907
Revises: 0e88581a5e5b
Create Date: 2017-03-09 21:47:02.523071

"""

# revision identifiers, used by Alembic.
revision = 'd2cfb4363907'
down_revision = '0e88581a5e5b'

from alembic import op
import sqlalchemy as sa

from compair.models import convention

def upgrade():
    op.create_table('kaltura_media',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('service_url', sa.String(length=255), nullable=False),
        sa.Column('partner_id', sa.Integer(), nullable=False),
        sa.Column('player_id', sa.Integer(), nullable=False),
        sa.Column('upload_ks', sa.String(length=255), nullable=False),
        sa.Column('upload_token_id', sa.String(length=255), nullable=False),
        sa.Column('file_name', sa.String(length=255), nullable=True),
        sa.Column('entry_id', sa.String(length=255), nullable=True),
        sa.Column('download_url', sa.String(length=255), nullable=True),
        sa.Column('modified_user_id', sa.Integer(), nullable=True),
        sa.Column('modified', sa.DateTime(), nullable=False),
        sa.Column('created_user_id', sa.Integer(), nullable=True),
        sa.Column('created', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['created_user_id'], ['user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['modified_user_id'], ['user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        mysql_charset='utf8',
        mysql_collate='utf8_unicode_ci',
        mysql_engine='InnoDB'
    )
    op.create_index(op.f('ix_kaltura_media_upload_token_id'), 'kaltura_media', ['upload_token_id'], unique=False)

    with op.batch_alter_table('file', naming_convention=convention) as batch_op:
        batch_op.add_column(sa.Column('kaltura_media_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_file_kaltura_media_id_kaltura_media',
            'kaltura_media', ['kaltura_media_id'], ['id'], ondelete="SET NULL")

def downgrade():
    with op.batch_alter_table('file', naming_convention=convention) as batch_op:
        batch_op.drop_constraint('fk_file_kaltura_media_id_kaltura_media', 'foreignkey')
        batch_op.drop_column('kaltura_media_id')

    op.drop_table('kaltura_media')