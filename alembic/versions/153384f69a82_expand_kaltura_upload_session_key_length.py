"""Expand Kaltura upload session key length

Revision ID: 153384f69a82
Revises: 895826c6c1ce
Create Date: 2020-02-10 20:37:17.126127

"""

# revision identifiers, used by Alembic.
revision = '153384f69a82'
down_revision = '895826c6c1ce'

from alembic import op
import sqlalchemy as sa

from compair.models import convention

def upgrade():
    with op.batch_alter_table('kaltura_media', naming_convention=convention) as batch_op:
        batch_op.alter_column('upload_ks',
                   existing_type=sa.String(length=255),
                   type_=sa.String(length=1024))

def downgrade():
    with op.batch_alter_table('kaltura_media', naming_convention=convention) as batch_op:
        batch_op.alter_column('upload_ks',
                   existing_type=sa.String(length=1024),
                   type_=sa.String(length=255))
