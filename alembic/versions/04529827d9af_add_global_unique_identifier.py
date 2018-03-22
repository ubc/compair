"""Add global unique identifier

Revision ID: 04529827d9af
Revises: 907993a4de86
Create Date: 2018-03-28 21:08:44.860260

"""

# revision identifiers, used by Alembic.
revision = '04529827d9af'
down_revision = '907993a4de86'

from alembic import op
import sqlalchemy as sa

from compair.models import convention

def upgrade():
    # Step 1: Update db
    op.create_index(op.f('ix_answer_comparable'), 'answer', ['comparable'], unique=False)

    # rename user_id_override to global_unique_identifier_param
    with op.batch_alter_table('lti_consumer', naming_convention=convention) as batch_op:
        batch_op.alter_column('user_id_override', new_column_name='global_unique_identifier_param',
            nullable=True, existing_type=sa.String(255))

    with op.batch_alter_table('lti_user', naming_convention=convention) as batch_op:
        batch_op.add_column(sa.Column('global_unique_identifier', sa.String(length=255), nullable=True))

    with op.batch_alter_table('user', naming_convention=convention) as batch_op:
        batch_op.add_column(sa.Column('global_unique_identifier', sa.String(length=255), nullable=True))
        batch_op.create_unique_constraint('_unique_global_unique_identifier', ['global_unique_identifier'])


    lti_consumer_table = sa.table('lti_consumer',
        sa.column('id', sa.Integer),
        sa.Column('global_unique_identifier_param', sa.String)
    )

    lti_user_table = sa.table('lti_user',
        sa.column('id', sa.Integer),
        sa.column('lti_consumer_id', sa.Integer),
        sa.column('compair_user_id', sa.Integer),
        sa.column('user_id', sa.String)
    )

    user_table = sa.table('user',
        sa.column('id', sa.Integer),
        sa.column('global_unique_identifier', sa.String),
    )

    # Step 2: Remove invalid lti users
    # remove all lti_user entries associated with lti_consumers that were using user_id_override
    connection = op.get_bind()

    lti_consumer_ids = []
    lti_consumers = connection.execute(lti_consumer_table.select().where(
        lti_consumer_table.c.global_unique_identifier_param != None
    ))
    for lti_consumer in lti_consumers:
        lti_consumer_ids.append(lti_consumer.id)

    if len(lti_consumer_ids) > 0:
        lti_users = connection.execute(lti_user_table.select().where(sa.and_(
            lti_user_table.c.lti_consumer_id.in_(lti_consumer_ids),
            lti_user_table.c.compair_user_id != None
        )))

        # set global_unique_identifier for existing links
        for lti_user in lti_users:
            connection.execute(user_table.update().where(
                    user_table.c.id == lti_user.compair_user_id
                ).values(
                    global_unique_identifier=lti_user.user_id
                )
            )

        # remove old lti user links
        connection.execute(
            lti_user_table.delete().where(
                lti_user_table.c.lti_consumer_id.in_(lti_consumer_ids)
            )
        )

    # Step 3: Notify user that it is strongly recommended to run
    # `python manage.py user generate_global_unique_identifiers`

    print("*"*50)
    print("""
DB Revision 04529827d9af adds global unique identifiers and removes lti users from the database that were using
the `user_id_override` field. Removed lti users will set their linked user's `global_unique_identifier` automatically
allowing automatic re-linking on the next LTI launch. It is also strongly recommended to run:

\tpython manage.py user generate_global_unique_identifiers\n

In order to automatically generate global unique identifiers for existing accounts if they are available in your
CAS and/or SAML attributes.
    """)
    print("*"*50)

def downgrade():
    with op.batch_alter_table('user', naming_convention=convention) as batch_op:
        batch_op.drop_constraint('_unique_global_unique_identifier', type_='unique')
        batch_op.drop_column('global_unique_identifier')

    with op.batch_alter_table('lti_user', naming_convention=convention) as batch_op:
        batch_op.drop_column('global_unique_identifier')

    # rename global_unique_identifier_param to user_id_override
    with op.batch_alter_table('lti_consumer', naming_convention=convention) as batch_op:
        batch_op.alter_column('global_unique_identifier_param', new_column_name='user_id_override',
            nullable=True, existing_type=sa.String(255))

    with op.batch_alter_table('answer', naming_convention=convention) as batch_op:
        batch_op.drop_index('ix_answer_comparable')
