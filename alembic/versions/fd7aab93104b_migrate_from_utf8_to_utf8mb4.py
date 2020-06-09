"""migrate charset from utf8 to utf8mb4 for mysql

Revision ID: fd7aab93104b
Revises: 153384f69a82
Create Date: 2020-06-08 17:50:54.948692

"""

# revision identifiers, used by Alembic.
revision = 'fd7aab93104b'
down_revision = '153384f69a82'

from alembic import op
import sqlalchemy as sa

from compair.models import convention

"""
This revision is targeted for MySQL/MariaDB only and hence with lots of SQLs that are MySQL-specific.
"""

def _check_data_legnth(conn, test_tuples):
    # check data for field length
    for (table, column, length) in test_tuples:
        query = 'select count(1) from `{}` where char_length(`{}`) > {}'.format(table, column, length)
        res = conn.execute(query)
        results = res.fetchone()
        res.close()
        if results[0] > 0:
            raise Exception('Data in column `{}` of table `{}` is longer than {}. Aborting migration'.format(column, table, length))

def upgrade():
    conn = op.get_bind()

    # this change is for mysql only
    if not conn.dialect.name == 'mysql':
        return

    # make sure we are not truncating any existing data.
    # possible race-condition. better run during system is offline.
    # TINYTEXT will be auto-promoted to TEXT.  TEXT will be auto-promoted to MEDIUMTEXT.
    # So no checks needed for TEXT-based columns.
    test_tuples = [
        # tuples of (table, column name, max number of characters)
        ('file', 'name', 191),
        ('kaltura_media', 'upload_token_id', 191),
        ('lti_consumer', 'oauth_consumer_key', 191),
        ('lti_consumer', 'tool_consumer_instance_guid', 191),
        ('lti_context', 'context_id', 191),
        ('lti_nonce', 'oauth_nonce', 191),
        ('lti_resource_link', 'resource_link_id', 191),
        ('lti_user', 'user_id', 191),
        ('third_party_user', 'unique_identifier', 191),
        ('user', 'username', 191),
        ('user', 'global_unique_identifier', 191),
    ]
    _check_data_legnth(conn, test_tuples)

    # ref: https://mathiasbynens.be/notes/mysql-utf8mb4
    """
    We needed to resize some varchar/char columns to be less than or equal to 191 if they are used in indexes.
    That is because MySQL has a limit of max bytes of indexed columns.
    """

    """
    -- Generate code for tables
    SELECT CONCAT('conn.execute(sa.sql.text("ALTER TABLE `',
      T.table_name,
      '` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))')
    FROM information_schema.`TABLES` T,
      information_schema.`COLLATION_CHARACTER_SET_APPLICABILITY` CCSA
    WHERE CCSA.collation_name = T.table_collation
      AND T.table_schema = "compair"
      AND CCSA.character_set_name='utf8';
    """
    conn.execute(sa.sql.text("ALTER TABLE `activity_log` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `answer` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `answer_comment` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `answer_criterion_score` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `answer_score` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `assignment` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `assignment_criterion` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `assignment_grade` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `caliper_log` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `comparison` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `comparison_criterion` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `comparison_example` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `course` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `course_grade` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `criterion` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
    with op.batch_alter_table('file', naming_convention=convention) as batch_op:
        batch_op.alter_column('name', type_=sa.String(length=191))
    conn.execute(sa.sql.text("ALTER TABLE `file` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `group` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
    with op.batch_alter_table('kaltura_media', naming_convention=convention) as batch_op:
        batch_op.alter_column('upload_token_id', type_=sa.String(length=191))
    conn.execute(sa.sql.text("ALTER TABLE `kaltura_media` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
    with op.batch_alter_table('lti_consumer', naming_convention=convention) as batch_op:
        batch_op.alter_column('oauth_consumer_key', type_=sa.String(length=191))
        batch_op.alter_column('tool_consumer_instance_guid', type_=sa.String(length=191))
    conn.execute(sa.sql.text("ALTER TABLE `lti_consumer` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
    with op.batch_alter_table('lti_context', naming_convention=convention) as batch_op:
        batch_op.alter_column('context_id', type_=sa.String(length=191))
    conn.execute(sa.sql.text("ALTER TABLE `lti_context` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `lti_membership` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
    with op.batch_alter_table('lti_nonce', naming_convention=convention) as batch_op:
        batch_op.alter_column('oauth_nonce', type_=sa.String(length=191))
    conn.execute(sa.sql.text("ALTER TABLE `lti_nonce` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
    with op.batch_alter_table('lti_resource_link', naming_convention=convention) as batch_op:
        batch_op.alter_column('resource_link_id', type_=sa.String(length=191))
    conn.execute(sa.sql.text("ALTER TABLE `lti_resource_link` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
    with op.batch_alter_table('lti_user', naming_convention=convention) as batch_op:
        batch_op.alter_column('user_id', type_=sa.String(length=191))
    conn.execute(sa.sql.text("ALTER TABLE `lti_user` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `lti_user_resource_link` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
    with op.batch_alter_table('third_party_user', naming_convention=convention) as batch_op:
        batch_op.alter_column('unique_identifier', type_=sa.String(length=191))
    conn.execute(sa.sql.text("ALTER TABLE `third_party_user` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
    with op.batch_alter_table('user', naming_convention=convention) as batch_op:
        batch_op.alter_column('username', type_=sa.String(length=191))
        batch_op.alter_column('global_unique_identifier', type_=sa.String(length=191))
    conn.execute(sa.sql.text("ALTER TABLE `user` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `user_course` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `xapi_log` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))

    # repair and optimize tables
    conn.execute(sa.sql.text("REPAIR TABLE `activity_log`"))
    conn.execute(sa.sql.text("OPTIMIZE TABLE `activity_log`"))
    conn.execute(sa.sql.text("REPAIR TABLE `answer`"))
    conn.execute(sa.sql.text("OPTIMIZE TABLE `answer`"))
    conn.execute(sa.sql.text("REPAIR TABLE `answer_comment`"))
    conn.execute(sa.sql.text("OPTIMIZE TABLE `answer_comment`"))
    conn.execute(sa.sql.text("REPAIR TABLE `answer_criterion_score`"))
    conn.execute(sa.sql.text("OPTIMIZE TABLE `answer_criterion_score`"))
    conn.execute(sa.sql.text("REPAIR TABLE `answer_score`"))
    conn.execute(sa.sql.text("OPTIMIZE TABLE `answer_score`"))
    conn.execute(sa.sql.text("REPAIR TABLE `assignment`"))
    conn.execute(sa.sql.text("OPTIMIZE TABLE `assignment`"))
    conn.execute(sa.sql.text("REPAIR TABLE `assignment_criterion`"))
    conn.execute(sa.sql.text("OPTIMIZE TABLE `assignment_criterion`"))
    conn.execute(sa.sql.text("REPAIR TABLE `assignment_grade`"))
    conn.execute(sa.sql.text("OPTIMIZE TABLE `assignment_grade`"))
    conn.execute(sa.sql.text("REPAIR TABLE `caliper_log`"))
    conn.execute(sa.sql.text("OPTIMIZE TABLE `caliper_log`"))
    conn.execute(sa.sql.text("REPAIR TABLE `comparison`"))
    conn.execute(sa.sql.text("OPTIMIZE TABLE `comparison`"))
    conn.execute(sa.sql.text("REPAIR TABLE `comparison_criterion`"))
    conn.execute(sa.sql.text("OPTIMIZE TABLE `comparison_criterion`"))
    conn.execute(sa.sql.text("REPAIR TABLE `comparison_example`"))
    conn.execute(sa.sql.text("OPTIMIZE TABLE `comparison_example`"))
    conn.execute(sa.sql.text("REPAIR TABLE `course`"))
    conn.execute(sa.sql.text("OPTIMIZE TABLE `course`"))
    conn.execute(sa.sql.text("REPAIR TABLE `course_grade`"))
    conn.execute(sa.sql.text("OPTIMIZE TABLE `course_grade`"))
    conn.execute(sa.sql.text("REPAIR TABLE `criterion`"))
    conn.execute(sa.sql.text("OPTIMIZE TABLE `criterion`"))
    conn.execute(sa.sql.text("REPAIR TABLE `file`"))
    conn.execute(sa.sql.text("OPTIMIZE TABLE `file`"))
    conn.execute(sa.sql.text("REPAIR TABLE `group`"))
    conn.execute(sa.sql.text("OPTIMIZE TABLE `group`"))
    conn.execute(sa.sql.text("REPAIR TABLE `kaltura_media`"))
    conn.execute(sa.sql.text("OPTIMIZE TABLE `kaltura_media`"))
    conn.execute(sa.sql.text("REPAIR TABLE `lti_consumer`"))
    conn.execute(sa.sql.text("OPTIMIZE TABLE `lti_consumer`"))
    conn.execute(sa.sql.text("REPAIR TABLE `lti_context`"))
    conn.execute(sa.sql.text("OPTIMIZE TABLE `lti_context`"))
    conn.execute(sa.sql.text("REPAIR TABLE `lti_membership`"))
    conn.execute(sa.sql.text("OPTIMIZE TABLE `lti_membership`"))
    conn.execute(sa.sql.text("REPAIR TABLE `lti_nonce`"))
    conn.execute(sa.sql.text("OPTIMIZE TABLE `lti_nonce`"))
    conn.execute(sa.sql.text("REPAIR TABLE `lti_resource_link`"))
    conn.execute(sa.sql.text("OPTIMIZE TABLE `lti_resource_link`"))
    conn.execute(sa.sql.text("REPAIR TABLE `lti_user`"))
    conn.execute(sa.sql.text("OPTIMIZE TABLE `lti_user`"))
    conn.execute(sa.sql.text("REPAIR TABLE `lti_user_resource_link`"))
    conn.execute(sa.sql.text("OPTIMIZE TABLE `lti_user_resource_link`"))
    conn.execute(sa.sql.text("REPAIR TABLE `third_party_user`"))
    conn.execute(sa.sql.text("OPTIMIZE TABLE `third_party_user`"))
    conn.execute(sa.sql.text("REPAIR TABLE `user`"))
    conn.execute(sa.sql.text("OPTIMIZE TABLE `user`"))
    conn.execute(sa.sql.text("REPAIR TABLE `user_course`"))
    conn.execute(sa.sql.text("OPTIMIZE TABLE `user_course`"))
    conn.execute(sa.sql.text("REPAIR TABLE `xapi_log`"))
    conn.execute(sa.sql.text("OPTIMIZE TABLE `xapi_log`"))

def downgrade():
    conn = op.get_bind()

    # this change is for mysql only
    if not conn.dialect.name == 'mysql':
        return

    # revert changes to tables
    conn.execute(sa.sql.text("ALTER TABLE `activity_log` CONVERT TO CHARACTER SET utf8 COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `answer` CONVERT TO CHARACTER SET utf8 COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `answer_comment` CONVERT TO CHARACTER SET utf8 COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `answer_criterion_score` CONVERT TO CHARACTER SET utf8 COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `answer_score` CONVERT TO CHARACTER SET utf8 COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `assignment` CONVERT TO CHARACTER SET utf8 COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `assignment_criterion` CONVERT TO CHARACTER SET utf8 COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `assignment_grade` CONVERT TO CHARACTER SET utf8 COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `caliper_log` CONVERT TO CHARACTER SET utf8 COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `comparison` CONVERT TO CHARACTER SET utf8 COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `comparison_criterion` CONVERT TO CHARACTER SET utf8 COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `comparison_example` CONVERT TO CHARACTER SET utf8 COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `course` CONVERT TO CHARACTER SET utf8 COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `course_grade` CONVERT TO CHARACTER SET utf8 COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `criterion` CONVERT TO CHARACTER SET utf8 COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `file` CONVERT TO CHARACTER SET utf8 COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `group` CONVERT TO CHARACTER SET utf8 COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `kaltura_media` CONVERT TO CHARACTER SET utf8 COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `lti_consumer` CONVERT TO CHARACTER SET utf8 COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `lti_context` CONVERT TO CHARACTER SET utf8 COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `lti_membership` CONVERT TO CHARACTER SET utf8 COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `lti_nonce` CONVERT TO CHARACTER SET utf8 COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `lti_resource_link` CONVERT TO CHARACTER SET utf8 COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `lti_user` CONVERT TO CHARACTER SET utf8 COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `lti_user_resource_link` CONVERT TO CHARACTER SET utf8 COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `third_party_user` CONVERT TO CHARACTER SET utf8 COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `user` CONVERT TO CHARACTER SET utf8 COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `user_course` CONVERT TO CHARACTER SET utf8 COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `xapi_log` CONVERT TO CHARACTER SET utf8 COLLATE utf8_unicode_ci"))

    # revert changes to columns
    conn.execute(sa.sql.text("ALTER TABLE `activity_log` CHANGE `event` `event` varchar(50) CHARACTER SET utf8 COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `activity_log` CHANGE `data` `data` text CHARACTER SET utf8 COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `activity_log` CHANGE `status` `status` varchar(20) CHARACTER SET utf8 COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `activity_log` CHANGE `message` `message` text CHARACTER SET utf8 COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `activity_log` CHANGE `session_id` `session_id` varchar(100) CHARACTER SET utf8 COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `answer` CHANGE `uuid` `uuid` char(22) CHARACTER SET utf8 NOT NULL COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `answer` CHANGE `content` `content` text CHARACTER SET utf8 COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `answer` CHANGE `attempt_uuid` `attempt_uuid` char(36) CHARACTER SET utf8 NOT NULL COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `answer_comment` CHANGE `uuid` `uuid` char(22) CHARACTER SET utf8 NOT NULL COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `answer_comment` CHANGE `content` `content` text CHARACTER SET utf8 COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `answer_comment` CHANGE `comment_type` `comment_type` enum('Public','Private','Evaluation','Self Evaluation') CHARACTER SET utf8 NOT NULL COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `answer_comment` CHANGE `attempt_uuid` `attempt_uuid` char(36) CHARACTER SET utf8 NOT NULL COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `answer_criterion_score` CHANGE `scoring_algorithm` `scoring_algorithm` enum('comparative_judgement','elo_rating','true_skill_rating') CHARACTER SET utf8 COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `answer_score` CHANGE `scoring_algorithm` `scoring_algorithm` enum('comparative_judgement','elo_rating','true_skill_rating') CHARACTER SET utf8 COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `assignment` CHANGE `uuid` `uuid` char(22) CHARACTER SET utf8 NOT NULL COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `assignment` CHANGE `name` `name` varchar(255) CHARACTER SET utf8 COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `assignment` CHANGE `description` `description` text CHARACTER SET utf8 COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `assignment` CHANGE `self_eval_instructions` `self_eval_instructions` text CHARACTER SET utf8 COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `assignment` CHANGE `scoring_algorithm` `scoring_algorithm` enum('comparative_judgement','elo_rating','true_skill_rating') CHARACTER SET utf8 COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `assignment` CHANGE `pairing_algorithm` `pairing_algorithm` enum('adaptive','random','adaptive_min_delta') CHARACTER SET utf8 COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `assignment` CHANGE `peer_feedback_prompt` `peer_feedback_prompt` text CHARACTER SET utf8 COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `caliper_log` CHANGE `event` `event` text CHARACTER SET utf8 COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `comparison` CHANGE `uuid` `uuid` char(22) CHARACTER SET utf8 NOT NULL COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `comparison` CHANGE `winner` `winner` enum('answer1','answer2','draw') CHARACTER SET utf8 COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `comparison` CHANGE `pairing_algorithm` `pairing_algorithm` enum('adaptive','random','adaptive_min_delta') CHARACTER SET utf8 COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `comparison` CHANGE `attempt_uuid` `attempt_uuid` char(36) CHARACTER SET utf8 NOT NULL COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `comparison_criterion` CHANGE `uuid` `uuid` char(22) CHARACTER SET utf8 NOT NULL COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `comparison_criterion` CHANGE `winner` `winner` enum('answer1','answer2','draw') CHARACTER SET utf8 COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `comparison_criterion` CHANGE `content` `content` text CHARACTER SET utf8 COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `comparison_example` CHANGE `uuid` `uuid` char(22) CHARACTER SET utf8 NOT NULL COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `course` CHANGE `uuid` `uuid` char(22) CHARACTER SET utf8 NOT NULL COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `course` CHANGE `name` `name` varchar(255) CHARACTER SET utf8 NOT NULL COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `course` CHANGE `term` `term` varchar(255) CHARACTER SET utf8 NOT NULL COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `criterion` CHANGE `uuid` `uuid` char(22) CHARACTER SET utf8 NOT NULL COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `criterion` CHANGE `name` `name` varchar(255) CHARACTER SET utf8 NOT NULL COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `criterion` CHANGE `description` `description` text CHARACTER SET utf8 COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `file` CHANGE `uuid` `uuid` char(22) CHARACTER SET utf8 NOT NULL COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `file` CHANGE `name` `name` varchar(255) CHARACTER SET utf8 NOT NULL COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `group` CHANGE `uuid` `uuid` char(22) CHARACTER SET utf8 NOT NULL COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `group` CHANGE `name` `name` varchar(255) CHARACTER SET utf8 COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `kaltura_media` CHANGE `service_url` `service_url` varchar(255) CHARACTER SET utf8 NOT NULL COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `kaltura_media` CHANGE `upload_ks` `upload_ks` varchar(1024) CHARACTER SET utf8 NOT NULL COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `kaltura_media` CHANGE `upload_token_id` `upload_token_id` varchar(255) CHARACTER SET utf8 NOT NULL COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `kaltura_media` CHANGE `file_name` `file_name` varchar(255) CHARACTER SET utf8 COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `kaltura_media` CHANGE `entry_id` `entry_id` varchar(255) CHARACTER SET utf8 COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `kaltura_media` CHANGE `download_url` `download_url` varchar(255) CHARACTER SET utf8 COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `lti_consumer` CHANGE `uuid` `uuid` char(22) CHARACTER SET utf8 NOT NULL COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `lti_consumer` CHANGE `oauth_consumer_key` `oauth_consumer_key` varchar(255) CHARACTER SET utf8 NOT NULL COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `lti_consumer` CHANGE `oauth_consumer_secret` `oauth_consumer_secret` varchar(255) CHARACTER SET utf8 NOT NULL COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `lti_consumer` CHANGE `lti_version` `lti_version` varchar(20) CHARACTER SET utf8 COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `lti_consumer` CHANGE `tool_consumer_instance_guid` `tool_consumer_instance_guid` varchar(255) CHARACTER SET utf8 COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `lti_consumer` CHANGE `tool_consumer_instance_name` `tool_consumer_instance_name` varchar(255) CHARACTER SET utf8 COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `lti_consumer` CHANGE `tool_consumer_instance_url` `tool_consumer_instance_url` text CHARACTER SET utf8 COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `lti_consumer` CHANGE `lis_outcome_service_url` `lis_outcome_service_url` text CHARACTER SET utf8 COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `lti_consumer` CHANGE `global_unique_identifier_param` `global_unique_identifier_param` varchar(255) CHARACTER SET utf8 COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `lti_consumer` CHANGE `student_number_param` `student_number_param` varchar(255) CHARACTER SET utf8 COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `lti_context` CHANGE `uuid` `uuid` char(22) CHARACTER SET utf8 NOT NULL COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `lti_context` CHANGE `context_id` `context_id` varchar(255) CHARACTER SET utf8 NOT NULL COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `lti_context` CHANGE `context_type` `context_type` varchar(255) CHARACTER SET utf8 COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `lti_context` CHANGE `context_title` `context_title` varchar(255) CHARACTER SET utf8 COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `lti_context` CHANGE `ext_ims_lis_memberships_id` `ext_ims_lis_memberships_id` varchar(255) CHARACTER SET utf8 COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `lti_context` CHANGE `ext_ims_lis_memberships_url` `ext_ims_lis_memberships_url` text CHARACTER SET utf8 COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `lti_context` CHANGE `custom_context_memberships_url` `custom_context_memberships_url` text CHARACTER SET utf8 COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `lti_context` CHANGE `lis_course_offering_sourcedid` `lis_course_offering_sourcedid` varchar(255) CHARACTER SET utf8 COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `lti_context` CHANGE `lis_course_section_sourcedid` `lis_course_section_sourcedid` varchar(255) CHARACTER SET utf8 COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `lti_membership` CHANGE `roles` `roles` varchar(255) CHARACTER SET utf8 COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `lti_membership` CHANGE `lis_result_sourcedid` `lis_result_sourcedid` varchar(255) CHARACTER SET utf8 COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `lti_membership` CHANGE `lis_result_sourcedids` `lis_result_sourcedids` text CHARACTER SET utf8 COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `lti_membership` CHANGE `course_role` `course_role` enum('Dropped','Instructor','Teaching Assistant','Student') CHARACTER SET utf8 NOT NULL COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `lti_nonce` CHANGE `oauth_nonce` `oauth_nonce` varchar(255) CHARACTER SET utf8 NOT NULL COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `lti_resource_link` CHANGE `resource_link_id` `resource_link_id` varchar(255) CHARACTER SET utf8 NOT NULL COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `lti_resource_link` CHANGE `resource_link_title` `resource_link_title` varchar(255) CHARACTER SET utf8 COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `lti_resource_link` CHANGE `launch_presentation_return_url` `launch_presentation_return_url` text CHARACTER SET utf8 COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `lti_resource_link` CHANGE `custom_param_assignment_id` `custom_param_assignment_id` varchar(255) CHARACTER SET utf8 COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `lti_user` CHANGE `uuid` `uuid` char(22) CHARACTER SET utf8 NOT NULL COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `lti_user` CHANGE `user_id` `user_id` varchar(255) CHARACTER SET utf8 NOT NULL COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `lti_user` CHANGE `lis_person_name_given` `lis_person_name_given` varchar(255) CHARACTER SET utf8 COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `lti_user` CHANGE `lis_person_name_family` `lis_person_name_family` varchar(255) CHARACTER SET utf8 COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `lti_user` CHANGE `lis_person_name_full` `lis_person_name_full` varchar(255) CHARACTER SET utf8 COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `lti_user` CHANGE `lis_person_contact_email_primary` `lis_person_contact_email_primary` varchar(255) CHARACTER SET utf8 COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `lti_user` CHANGE `global_unique_identifier` `global_unique_identifier` varchar(255) CHARACTER SET utf8 COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `lti_user` CHANGE `system_role` `system_role` enum('Student','Instructor','System Administrator') CHARACTER SET utf8 NOT NULL COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `lti_user` CHANGE `student_number` `student_number` varchar(255) CHARACTER SET utf8 COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `lti_user` CHANGE `lis_person_sourcedid` `lis_person_sourcedid` varchar(255) CHARACTER SET utf8 COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `lti_user_resource_link` CHANGE `roles` `roles` varchar(255) CHARACTER SET utf8 COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `lti_user_resource_link` CHANGE `lis_result_sourcedid` `lis_result_sourcedid` varchar(255) CHARACTER SET utf8 COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `lti_user_resource_link` CHANGE `course_role` `course_role` enum('Dropped','Instructor','Teaching Assistant','Student') CHARACTER SET utf8 NOT NULL COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `third_party_user` CHANGE `uuid` `uuid` char(22) CHARACTER SET utf8 NOT NULL COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `third_party_user` CHANGE `third_party_type` `third_party_type` enum('CAS','SAML') CHARACTER SET utf8 NOT NULL COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `third_party_user` CHANGE `unique_identifier` `unique_identifier` varchar(255) CHARACTER SET utf8 NOT NULL COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `third_party_user` CHANGE `_params` `_params` text CHARACTER SET utf8 COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `user` CHANGE `uuid` `uuid` char(22) CHARACTER SET utf8 NOT NULL COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `user` CHANGE `global_unique_identifier` `global_unique_identifier` varchar(255) CHARACTER SET utf8 COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `user` CHANGE `username` `username` varchar(255) CHARACTER SET utf8 COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `user` CHANGE `_password` `_password` varchar(255) CHARACTER SET utf8 COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `user` CHANGE `system_role` `system_role` enum('Student','Instructor','System Administrator') CHARACTER SET utf8 NOT NULL COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `user` CHANGE `displayname` `displayname` varchar(255) CHARACTER SET utf8 NOT NULL COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `user` CHANGE `email` `email` varchar(254) CHARACTER SET utf8 COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `user` CHANGE `firstname` `firstname` varchar(255) CHARACTER SET utf8 COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `user` CHANGE `lastname` `lastname` varchar(255) CHARACTER SET utf8 COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `user` CHANGE `student_number` `student_number` varchar(50) CHARACTER SET utf8 COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `user` CHANGE `email_notification_method` `email_notification_method` enum('enable','disable') CHARACTER SET utf8 NOT NULL COLLATE utf8_unicode_ci DEFAULT 'enable'"))
    conn.execute(sa.sql.text("ALTER TABLE `user_course` CHANGE `course_role` `course_role` enum('Dropped','Instructor','Teaching Assistant','Student') CHARACTER SET utf8 NOT NULL COLLATE utf8_unicode_ci"))
    conn.execute(sa.sql.text("ALTER TABLE `xapi_log` CHANGE `statement` `statement` text CHARACTER SET utf8 COLLATE utf8_unicode_ci"))

    # repair and optimize tables
    conn.execute(sa.sql.text("REPAIR TABLE `activity_log`"))
    conn.execute(sa.sql.text("OPTIMIZE TABLE `activity_log`"))
    conn.execute(sa.sql.text("REPAIR TABLE `answer`"))
    conn.execute(sa.sql.text("OPTIMIZE TABLE `answer`"))
    conn.execute(sa.sql.text("REPAIR TABLE `answer_comment`"))
    conn.execute(sa.sql.text("OPTIMIZE TABLE `answer_comment`"))
    conn.execute(sa.sql.text("REPAIR TABLE `answer_criterion_score`"))
    conn.execute(sa.sql.text("OPTIMIZE TABLE `answer_criterion_score`"))
    conn.execute(sa.sql.text("REPAIR TABLE `answer_score`"))
    conn.execute(sa.sql.text("OPTIMIZE TABLE `answer_score`"))
    conn.execute(sa.sql.text("REPAIR TABLE `assignment`"))
    conn.execute(sa.sql.text("OPTIMIZE TABLE `assignment`"))
    conn.execute(sa.sql.text("REPAIR TABLE `assignment_criterion`"))
    conn.execute(sa.sql.text("OPTIMIZE TABLE `assignment_criterion`"))
    conn.execute(sa.sql.text("REPAIR TABLE `assignment_grade`"))
    conn.execute(sa.sql.text("OPTIMIZE TABLE `assignment_grade`"))
    conn.execute(sa.sql.text("REPAIR TABLE `caliper_log`"))
    conn.execute(sa.sql.text("OPTIMIZE TABLE `caliper_log`"))
    conn.execute(sa.sql.text("REPAIR TABLE `comparison`"))
    conn.execute(sa.sql.text("OPTIMIZE TABLE `comparison`"))
    conn.execute(sa.sql.text("REPAIR TABLE `comparison_criterion`"))
    conn.execute(sa.sql.text("OPTIMIZE TABLE `comparison_criterion`"))
    conn.execute(sa.sql.text("REPAIR TABLE `comparison_example`"))
    conn.execute(sa.sql.text("OPTIMIZE TABLE `comparison_example`"))
    conn.execute(sa.sql.text("REPAIR TABLE `course`"))
    conn.execute(sa.sql.text("OPTIMIZE TABLE `course`"))
    conn.execute(sa.sql.text("REPAIR TABLE `course_grade`"))
    conn.execute(sa.sql.text("OPTIMIZE TABLE `course_grade`"))
    conn.execute(sa.sql.text("REPAIR TABLE `criterion`"))
    conn.execute(sa.sql.text("OPTIMIZE TABLE `criterion`"))
    conn.execute(sa.sql.text("REPAIR TABLE `file`"))
    conn.execute(sa.sql.text("OPTIMIZE TABLE `file`"))
    conn.execute(sa.sql.text("REPAIR TABLE `group`"))
    conn.execute(sa.sql.text("OPTIMIZE TABLE `group`"))
    conn.execute(sa.sql.text("REPAIR TABLE `kaltura_media`"))
    conn.execute(sa.sql.text("OPTIMIZE TABLE `kaltura_media`"))
    conn.execute(sa.sql.text("REPAIR TABLE `lti_consumer`"))
    conn.execute(sa.sql.text("OPTIMIZE TABLE `lti_consumer`"))
    conn.execute(sa.sql.text("REPAIR TABLE `lti_context`"))
    conn.execute(sa.sql.text("OPTIMIZE TABLE `lti_context`"))
    conn.execute(sa.sql.text("REPAIR TABLE `lti_membership`"))
    conn.execute(sa.sql.text("OPTIMIZE TABLE `lti_membership`"))
    conn.execute(sa.sql.text("REPAIR TABLE `lti_nonce`"))
    conn.execute(sa.sql.text("OPTIMIZE TABLE `lti_nonce`"))
    conn.execute(sa.sql.text("REPAIR TABLE `lti_resource_link`"))
    conn.execute(sa.sql.text("OPTIMIZE TABLE `lti_resource_link`"))
    conn.execute(sa.sql.text("REPAIR TABLE `lti_user`"))
    conn.execute(sa.sql.text("OPTIMIZE TABLE `lti_user`"))
    conn.execute(sa.sql.text("REPAIR TABLE `lti_user_resource_link`"))
    conn.execute(sa.sql.text("OPTIMIZE TABLE `lti_user_resource_link`"))
    conn.execute(sa.sql.text("REPAIR TABLE `third_party_user`"))
    conn.execute(sa.sql.text("OPTIMIZE TABLE `third_party_user`"))
    conn.execute(sa.sql.text("REPAIR TABLE `user`"))
    conn.execute(sa.sql.text("OPTIMIZE TABLE `user`"))
    conn.execute(sa.sql.text("REPAIR TABLE `user_course`"))
    conn.execute(sa.sql.text("OPTIMIZE TABLE `user_course`"))
    conn.execute(sa.sql.text("REPAIR TABLE `xapi_log`"))
    conn.execute(sa.sql.text("OPTIMIZE TABLE `xapi_log`"))

