"""remove group name unique constraint

Remove the db unique constraint added by b492a8f2132c.
Group name can repeat if only one of the records is active.
Will use program logic to check uniqueness of active group name.
There maybe a race condition causing duplicate group name in case of concurrent group creation.
But the chance is small and impact is minimal.

Revision ID: 1e4cb64dd9b5
Revises: b492a8f2132c
Create Date: 2019-01-24 20:26:56.722350

"""

# revision identifiers, used by Alembic.
revision = '1e4cb64dd9b5'
down_revision = 'b492a8f2132c'

from alembic import op
import sqlalchemy as sa
from sqlalchemy import func

from compair.models import convention

group_table = sa.table('group',
    sa.Column('id', sa.Integer), sa.Column('course_id', sa.Integer),
    sa.Column('name', sa.String), sa.Column('active', sa.Boolean),
    sa.Column('modified', sa.DateTime), sa.Column('created', sa.DateTime),
    sa.Column('uuid', sa.CHAR(22))
)

def upgrade():
    with op.batch_alter_table('group', naming_convention=convention) as batch_op:
        batch_op.drop_constraint('uq_course_and_group_name', type_='unique')

def downgrade():
    connection = op.get_bind()

    groups = connection.execute(group_table.select())

    # {course_id}{group_name} - counts how many have been updated so far
    counter = {}

    for group in groups:
        counter.setdefault(group.course_id, {})
        counter[group.course_id].setdefault(group.name, 0)

        counter[group.course_id][group.name] += 1

        if counter[group.course_id][group.name] > 1:
            count = counter[group.course_id][group.name]
            new_group_name = "{} [{}]".format(group.name, count)
            # while loop is necessary in case there is an existing group with the same name and number e.g. Example Group [2]
            while connection.execute(group_table.count().where(sa.and_(
                    group_table.c.name == new_group_name,
                    group_table.c.course_id == group.course_id
                ))).scalar() > 0:
                    count += 1
                    new_group_name = "{} [{}]".format(group.name, count)
            connection.execute(
                group_table \
                .update() \
                .where(group_table.c.id == group.id) \
                .values(name=new_group_name)
            )
            counter[group.course_id][group.name] = count

    with op.batch_alter_table('group', naming_convention=convention) as batch_op:
        batch_op.create_unique_constraint('uq_course_and_group_name', ['course_id', 'name'])