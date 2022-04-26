"""replace sqlalchemy-enum34.EnumType with more standard sqlalchemy.Enum

sqlalchemy-enum34.EnumType has incompatible behaviour with sqlalchemy.Enum:

* sqlalchemy-enum34's EnumType stores the enum's value to the database.
* sqlalchemy's Enum stores the enum's key to the database.

I initially thought that this meant we'd have a unreversible migration as a
result, but some experimentation was able to reverse the migration.

Note that the frontend is still working with the enum values, it's only the
backend that has to be worry about this change. Luckily, this means that we can
keep the code changes to a minimum, as initially, I was trying to edit multiple
js files for the new behaviour and was encountering a lot of issues.
Interestingly, since the enum translation to the database was handled by the
respective libraries, we didn't have to change much code either on the backend
side.


Revision ID: 23944543dc01
Revises: bb705e95c6dc
Create Date: 2022-03-23 23:02:29.910656

"""

# revision identifiers, used by Alembic.
revision = '23944543dc01'
down_revision = 'bb705e95c6dc'

from alembic import op
from compair.models import convention
from enum import Enum
import sqlalchemy as sa
from sqlalchemy_enum34 import EnumType


def upgrade():
    # AnswerCommentType
    upgradeEnum('answer_comment', 'comment_type', OldAnswerCommentType,
                RenameTmpAnswerCommentType, RenameNewAnswerCommentType)
    # CourseRole
    upgradeEnum('user_course', 'course_role', OldCourseRole,
                RenameTmpCourseRole, RenameNewCourseRole)
    upgradeEnum('lti_membership', 'course_role', OldCourseRole,
                RenameTmpCourseRole, RenameNewCourseRole)
    upgradeEnum('lti_user_resource_link', 'course_role', OldCourseRole,
                RenameTmpCourseRole, RenameNewCourseRole)
    # SystemRole
    upgradeEnum('user', 'system_role', OldSystemRole, RenameTmpSystemRole,
                RenameNewSystemRole)
    upgradeEnum('lti_user', 'system_role', OldSystemRole, RenameTmpSystemRole,
                RenameNewSystemRole)
    # ScoringAlgorithm
    upgradeEnum('assignment', 'scoring_algorithm', OldScoringAlgorithm,
                RenameTmpScoringAlgorithm, RenameNewScoringAlgorithm)
    upgradeEnum('answer_score', 'scoring_algorithm', OldScoringAlgorithm,
                RenameTmpScoringAlgorithm, RenameNewScoringAlgorithm)
    upgradeEnum('answer_criterion_score', 'scoring_algorithm',
                OldScoringAlgorithm, RenameTmpScoringAlgorithm,
                RenameNewScoringAlgorithm)
    # ThirdPartyType
    upgradeEnum('third_party_user', 'third_party_type', OldThirdPartyType,
                RenameTmpThirdPartyType, RenameNewThirdPartyType)


def downgrade():
    # ThirdPartyType
    downgradeEnum('third_party_user', 'third_party_type', OldThirdPartyType,
                  RenameTmpThirdPartyType, RenameNewThirdPartyType)
    # ScoringAlgorithm
    downgradeEnum('answer_criterion_score', 'scoring_algorithm',
                  OldScoringAlgorithm, RenameTmpScoringAlgorithm,
                  RenameNewScoringAlgorithm)
    downgradeEnum('answer_score', 'scoring_algorithm', OldScoringAlgorithm,
                  RenameTmpScoringAlgorithm, RenameNewScoringAlgorithm)
    downgradeEnum('assignment', 'scoring_algorithm', OldScoringAlgorithm,
                  RenameTmpScoringAlgorithm, RenameNewScoringAlgorithm)
    # SystemRole
    downgradeEnum('lti_user', 'system_role', OldSystemRole, RenameTmpSystemRole,
                  RenameNewSystemRole)
    downgradeEnum('user', 'system_role', OldSystemRole, RenameTmpSystemRole,
                  RenameNewSystemRole)
    # CourseRole
    downgradeEnum('lti_user_resource_link', 'course_role', OldCourseRole,
                  RenameTmpCourseRole, RenameNewCourseRole)
    downgradeEnum('lti_membership', 'course_role', OldCourseRole,
                  RenameTmpCourseRole, RenameNewCourseRole)
    downgradeEnum('user_course', 'course_role', OldCourseRole,
                  RenameTmpCourseRole, RenameNewCourseRole)
    # AnswerCommentTYpe
    downgradeEnum('answer_comment', 'comment_type', OldAnswerCommentType,
                  RenameTmpAnswerCommentType, RenameNewAnswerCommentType)


# We need to change to 2 different tmp enums before changing to the final
# new enum due to 2 factors:
#
# 1. there needs to be an enum that has both the old & new values, or the db
#   will complain about consistency issues.
# 2. db case insensitivity, values like "Public" and "public" are treated the
#   same. This is a problem since many of our new enums are just lower case
#   versions of the old enum, causing the db to complain about duplicate values.
#
# Note that the final enum is the same as the old enum but using sqlalchemy's
# Enum instead of sqlalchemy_enum34's EnumType.
def upgradeEnum(
    tableName,
    colName,
    oldEnum,
    renameTmpEnum,
    renameNewEnum
):
    # convert column to the rename tmp enum
    with op.batch_alter_table(tableName, naming_convention=convention) as batch_op:
        # renameTmpEnum just tacks on a 'tmp_' prefix to the values, to avoid
        # the case insensitivity duplicate issues
        batch_op.alter_column(colName,
                              nullable=False,
                              type_=EnumType(renameTmpEnum),
                              existing_type=EnumType(oldEnum))
    # update existing data from old enum to the tmp values in the tmp enum
    conn = op.get_bind()
    table = sa.table(tableName, sa.column(colName, sa.Enum(renameTmpEnum)))
    for entry in oldEnum:
        conn.execute(table.update()
                     .where(getattr(table.c, colName) == entry.value)
                     .values({colName: 'tmp_' + entry.name}))

    # convert column to the rename new enum
    with op.batch_alter_table(tableName, naming_convention=convention) as batch_op:
        # renameNewEnum contains the new & tmp enum values
        batch_op.alter_column(colName,
                              nullable=False,
                              type_=EnumType(renameNewEnum),
                              existing_type=EnumType(renameTmpEnum))
    # update existing data from the tmp enum to new enum
    conn = op.get_bind()
    table = sa.table(tableName, sa.column(colName, sa.Enum(renameNewEnum)))
    for entry in oldEnum:
        conn.execute(table.update()
                     .where(getattr(table.c, colName) == 'tmp_' + entry.name)
                     .values({colName: entry.name}))

    # finally, can set the column type to just the new enum
    with op.batch_alter_table(tableName, naming_convention=convention) as batch_op:
        batch_op.alter_column(colName,
                              nullable=False,
                              type_=sa.Enum(oldEnum),
                              existing_type=EnumType(renameNewEnum))


def downgradeEnum(
    tableName,
    colName,
    oldEnum,
    renameTmpEnum,
    renameNewEnum
):
    # undo the new enum conversion, change column to rename new enum
    with op.batch_alter_table(tableName, naming_convention=convention) as batch_op:
        # renameNewEnum contains the new & tmp enum values
        batch_op.alter_column(colName,
                              nullable=False,
                              type_=EnumType(renameNewEnum),
                              existing_type=sa.Enum(oldEnum))

    # undo rename to new enum, so we rename from new enum to tmp enum
    conn = op.get_bind()
    table = sa.table(tableName, sa.column(colName, sa.Enum(renameNewEnum)))
    for entry in oldEnum:
        conn.execute(table.update()
                     .where(getattr(table.c, colName) == entry.name)
                     .values({colName: 'tmp_' + entry.name}))
    # convert column back to tmp enum
    with op.batch_alter_table(tableName, naming_convention=convention) as batch_op:
        batch_op.alter_column(colName,
                              nullable=False,
                              type_=EnumType(renameTmpEnum),
                              existing_type=EnumType(renameNewEnum))

    conn = op.get_bind()
    # undo rename to tmp enum, so we rename from tmp enum to old enum
    table = sa.table(tableName, sa.column(colName, sa.Enum(renameTmpEnum)))
    for entry in oldEnum:
        conn.execute(table.update()
                     .where(getattr(table.c, colName) == 'tmp_' + entry.name)
                     .values({colName: entry.value}))
    # can now ditch tmp enum and convert the column back to old enum
    with op.batch_alter_table(tableName, naming_convention=convention) as batch_op:
        batch_op.alter_column(colName,
                              nullable=False,
                              type_=EnumType(oldEnum),
                              existing_type=EnumType(renameTmpEnum))


######### Enums for AnswerCommentType #########
class OldAnswerCommentType(Enum):
    public = "Public"
    private = "Private"
    evaluation = "Evaluation"
    self_evaluation = "Self Evaluation"


# used for renaming from old enum vals to a tmp enum val, needs to be temp
# cause the collation for our db is case insensitive, so values like
# "Public" and "public" confict, so we can't use them at the same time.
# We need to have the old values or sqlalchemy will fail validation on them.
class RenameTmpAnswerCommentType(Enum):
    public = "Public"
    private = "Private"
    evaluation = "Evaluation"
    self_evaluation = "Self Evaluation"
    tmp_public = "tmp_public"
    tmp_private = "tmp_private"
    tmp_evaluation = "tmp_evaluation"
    tmp_self_evaluation = "tmp_self_evaluation"


# used to rename from the tmp enum val to the new enum val, the actual string
# stored in the database is now the enum key instead of the value.
class RenameNewAnswerCommentType(Enum):
    tmp_public = "tmp_public"
    tmp_private = "tmp_private"
    tmp_evaluation = "tmp_evaluation"
    tmp_self_evaluation = "tmp_self_evaluation"
    public = "public"
    private = "private"
    evaluation = "evaluation"
    self_evaluation = "self_evaluation"


######### Enums for CourseRole #########
class OldCourseRole(Enum):
    dropped = "Dropped"
    instructor = "Instructor"
    teaching_assistant = "Teaching Assistant"
    student = "Student"


class RenameTmpCourseRole(Enum):
    dropped = "Dropped"
    instructor = "Instructor"
    teaching_assistant = "Teaching Assistant"
    student = "Student"
    tmp_dropped = "tmp_dropped"
    tmp_instructor = "tmp_instructor"
    tmp_teaching_assistant = "tmp_teaching_assistant"
    tmp_student = "tmp_student"


class RenameNewCourseRole(Enum):
    tmp_dropped = "tmp_dropped"
    tmp_instructor = "tmp_instructor"
    tmp_teaching_assistant = "tmp_teaching_assistant"
    tmp_student = "tmp_student"
    dropped = "dropped"
    instructor = "instructor"
    teaching_assistant = "teaching_assistant"
    student = "student"


######### Enums for SystemRole #########
class OldSystemRole(Enum):
    student = "Student"
    instructor = "Instructor"
    sys_admin = "System Administrator"


class RenameTmpSystemRole(Enum):
    student = "Student"
    instructor = "Instructor"
    sys_admin = "System Administrator"
    tmp_student = "tmp_student"
    tmp_instructor = "tmp_instructor"
    tmp_sys_admin = "tmp_sys_admin"


class RenameNewSystemRole(Enum):
    tmp_student = "tmp_student"
    tmp_instructor = "tmp_instructor"
    tmp_sys_admin = "tmp_sys_admin"
    student = "student"
    instructor = "instructor"
    sys_admin = "sys_admin"


######### Enums for ScoringAlgorithm #########
class OldScoringAlgorithm(Enum):
    comparative_judgement = "comparative_judgement"
    elo = "elo_rating" # note the '_rating' not present in key
    true_skill = "true_skill_rating"


class RenameTmpScoringAlgorithm(Enum):
    comparative_judgement = "comparative_judgement"
    elo = "elo_rating"
    true_skill = "true_skill_rating"
    tmp_comparative_judgement = "tmp_comparative_judgement"
    tmp_elo = "tmp_elo"
    tmp_true_skill = "tmp_true_skill"


class RenameNewScoringAlgorithm(Enum):
    tmp_comparative_judgement = "tmp_comparative_judgement"
    tmp_elo = "tmp_elo"
    tmp_true_skill = "tmp_true_skill"
    comparative_judgement = "comparative_judgement"
    elo = "elo"
    true_skill = "true_skill"


######### Enums for ThirdPartyType #########
class OldThirdPartyType(Enum):
    cas = "CAS"
    saml = "SAML"


class RenameTmpThirdPartyType(Enum):
    cas = "CAS"
    saml = "SAML"
    tmp_cas = "tmp_cas"
    tmp_saml = "tmp_saml"


class RenameNewThirdPartyType(Enum):
    tmp_cas = "tmp_cas"
    tmp_saml = "tmp_saml"
    cas = "cas"
    saml = "saml"
