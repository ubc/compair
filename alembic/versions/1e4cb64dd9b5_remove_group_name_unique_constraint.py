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
from sqlalchemy import create_engine
from sqlalchemy.engine.reflection import Inspector
from compair.models import convention

group_table = sa.table('group',
    sa.Column('id', sa.Integer), sa.Column('course_id', sa.Integer),
    sa.Column('name', sa.String), sa.Column('active', sa.Boolean),
    sa.Column('modified', sa.DateTime), sa.Column('created', sa.DateTime),
    sa.Column('uuid', sa.CHAR(22))
)

def upgrade():
    # Drop the foreign key on course_id and recreate it.
    # Otherwise may encounter issues when dropping unique constraint (e.g. on mysql with certain data).
    # Seems the unittest/demo site/prod are using diff naming convention for the foreign key,
    # so use inspector to try to find it
    insp = Inspector.from_engine(op.get_bind())
    foreign_keys = insp.get_foreign_keys('group')
    filtered_keys = [k for k in foreign_keys if \
        k['referred_table']=='course' and \
        len(k['constrained_columns'])==1 and \
        k['constrained_columns'][0]=='course_id']
    if filtered_keys:
        foreign_key_name = filtered_keys[0]['name']
        with op.batch_alter_table('group', naming_convention=convention) as batch_op:
            batch_op.drop_constraint(foreign_key_name, type_='foreignkey')

    with op.batch_alter_table('group', naming_convention=convention) as batch_op:
        batch_op.drop_constraint('uq_course_and_group_name', type_='unique')

    if filtered_keys:
        foreign_key_name = filtered_keys[0]['name']
        with op.batch_alter_table('group', naming_convention=convention) as batch_op:
            batch_op.create_foreign_key(foreign_key_name, 'course', ['course_id'], ['id'], ondelete='CASCADE')

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