"""Migrate user_course groups to groups table

Revision ID: c8d5a5c16f59
Revises: e453164951b5
Create Date: 2018-06-05 22:28:53.085433

"""

# revision identifiers, used by Alembic.
revision = 'c8d5a5c16f59'
down_revision = 'e453164951b5'

from alembic import op
import sqlalchemy as sa
from datetime import datetime
import uuid
import base64

from compair.models import convention

user_course_table = sa.table('user_course',
    sa.Column('id', sa.Integer), sa.Column('course_id', sa.Integer),
    sa.Column('user_id', sa.Integer), sa.Column('group_id', sa.Integer),
    sa.Column('group_name', sa.String),
)

group_table = sa.table('group',
    sa.Column('id', sa.Integer), sa.Column('course_id', sa.Integer),
    sa.Column('name', sa.String), sa.Column('active', sa.Boolean),
    sa.Column('modified', sa.DateTime), sa.Column('created', sa.DateTime),
    sa.Column('uuid', sa.CHAR(22))
)

def upgrade():
    # STEP 1: migrate existing groups over to group table

    connection = op.get_bind()
    # store existing groups
    user_courses = connection.execute(user_course_table.select().where(sa.and_(
        user_course_table.c.group_name != "",
        user_course_table.c.group_name != None
    )))

    # {course_id}{group_name}[list of user ids]
    course_list = {}
    for user_course in user_courses:
        course_groups = course_list.setdefault(user_course.course_id, {})
        user_ids = course_groups.setdefault(user_course.group_name, [])
        user_ids.append(user_course.user_id)

    for course_id, course_groups in course_list.items():
        for group_name, user_ids in course_groups.items():
            result = connection.execute(
                group_table.insert().values(
                    course_id=course_id, name=group_name, active=True,
                    modified=datetime.utcnow(), created=datetime.utcnow(),
                    uuid=base64.urlsafe_b64encode(uuid.uuid4().bytes).decode('ascii').replace('=', '')
                )
            )
            group_id = result.lastrowid

            connection.execute(
                user_course_table.update().where(sa.and_(
                    user_course_table.c.user_id.in_(user_ids),
                    user_course_table.c.course_id == course_id
                )).values(
                    group_id=group_id
                )
            )

    # STEP 2: drop group_name column

    with op.batch_alter_table('user_course', naming_convention=convention) as batch_op:
        batch_op.drop_index('ix_user_course_group_name')
        batch_op.drop_column('group_name')


def downgrade():
    # STEP 1: create group_name column

    with op.batch_alter_table('user_course', naming_convention=convention) as batch_op:
        batch_op.add_column(sa.Column('group_name', sa.String(length=255), nullable=True))
    op.create_index('ix_user_course_group_name', 'user_course', ['group_name'], unique=False)

    # STEP 2: migrate existing groups over to user_course table

    connection = op.get_bind()
    # get existing groups
    groups = connection.execute(group_table.select().where(sa.and_(
        group_table.c.name != "",
        group_table.c.name != None
    )))

    # go one group at a time
    for group in groups:
        connection.execute(
            user_course_table.update().where(sa.and_(
                user_course_table.c.group_id == group.id
            )).values(
                group_name=group.name
            )
        )