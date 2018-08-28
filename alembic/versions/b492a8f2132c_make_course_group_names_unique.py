"""make course group names unique

Revision ID: b492a8f2132c
Revises: d6c88adfe909
Create Date: 2018-08-29 15:50:58.479621

"""

# revision identifiers, used by Alembic.
revision = 'b492a8f2132c'
down_revision = 'd6c88adfe909'

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

def downgrade():
    with op.batch_alter_table('group', naming_convention=convention) as batch_op:
        batch_op.drop_constraint('uq_course_and_group_name', type_='unique')
