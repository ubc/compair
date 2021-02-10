from requests.utils import quote

from .learning_record import LearningRecord

class ResourceIRI(object):
    @classmethod
    def _get_app_url(cls):
        return LearningRecord.get_base_url()+'/app/'

    @classmethod
    def _get_attachment_url(cls):
        return LearningRecord.get_base_url()+'/app/attachment/'

    @classmethod
    def _get_report_url(cls):
        return LearningRecord.get_base_url()+'/app/report/'

    @classmethod
    def actor_homepage(cls):
        return LearningRecord.get_base_url()+'/'

    # resource urls
    @classmethod
    def compair(cls):
        return LearningRecord.get_base_url()

    @classmethod
    def user_membership(cls, course_uuid, user_uuid):
        return cls.course(course_uuid)+'/user/'+user_uuid

    @classmethod
    def user_session(cls, session_id):
        return LearningRecord.get_base_url()+'/session/'+session_id

    @classmethod
    def user_client(cls, session_id):
        return cls.user_session(session_id)+'/client'

    @classmethod
    def course(cls, course_uuid):
        return cls._get_app_url()+'course/'+course_uuid

    @classmethod
    def criterion(cls, criterion_uuid):
        return cls._get_app_url()+'criterion/'+criterion_uuid


    @classmethod
    def group(cls, course_uuid, group_uuid):
        return cls.course(course_uuid)+'/group/'+group_uuid

    @classmethod
    def assignment(cls, course_uuid, assignment_uuid):
        return cls.course(course_uuid)+'/assignment/'+assignment_uuid

    @classmethod
    def assignment_attempt(cls, course_uuid, assignment_uuid, attempt_uuid):
        return cls.assignment(course_uuid, assignment_uuid)+'/attempt/'+attempt_uuid


    @classmethod
    def assignment_question(cls, course_uuid, assignment_uuid):
        return cls.assignment(course_uuid, assignment_uuid)+'/question'

    @classmethod
    def answer(cls, course_uuid, assignment_uuid, answer_uuid):
        return cls.assignment(course_uuid, assignment_uuid)+'/answer/'+answer_uuid

    @classmethod
    def answer_attempt(cls, course_uuid, assignment_uuid, attempt_uuid):
        return cls.assignment_question(course_uuid, assignment_uuid)+'/attempt/'+attempt_uuid



    @classmethod
    def comparison_question(cls, course_uuid, assignment_uuid, comparison_number):
        return cls.assignment(course_uuid, assignment_uuid)+'/comparison/question/'+str(comparison_number)

    @classmethod
    def comparison(cls, course_uuid, assignment_uuid, comparison_uuid):
        return cls.assignment(course_uuid, assignment_uuid)+'/comparison/'+comparison_uuid

    @classmethod
    def comparison_attempt(cls, course_uuid, assignment_uuid, comparison_number, attempt_uuid):
        return cls.comparison_question(course_uuid, assignment_uuid, comparison_number)+'/attempt/'+attempt_uuid



    @classmethod
    def evaluation_question(cls, course_uuid, assignment_uuid, evaluation_number):
        return cls.assignment(course_uuid, assignment_uuid)+'/evaluation/question/'+str(evaluation_number)

    @classmethod
    def evaluation_response(cls, course_uuid, assignment_uuid, answer_uuid, answer_comment_uuid):
        return cls.answer_comment(course_uuid, assignment_uuid, answer_uuid, answer_comment_uuid)+'/evaluation'

    @classmethod
    def evaluation_attempt(cls, course_uuid, assignment_uuid, evaluation_number, attempt_uuid):
        return cls.evaluation_question(course_uuid, assignment_uuid, evaluation_number)+'/attempt/'+attempt_uuid



    @classmethod
    def self_evaluation_question(cls, course_uuid, assignment_uuid):
        return cls.assignment(course_uuid, assignment_uuid)+'/self-evaluation/question'

    @classmethod
    def self_evaluation_response(cls, course_uuid, assignment_uuid, answer_uuid, answer_comment_uuid):
        return cls.answer_comment(course_uuid, assignment_uuid, answer_uuid, answer_comment_uuid)+'/self-evaluation'

    @classmethod
    def self_evaluation_attempt(cls, course_uuid, assignment_uuid, attempt_uuid):
        return cls.self_evaluation_question(course_uuid, assignment_uuid)+'/attempt/'+attempt_uuid



    @classmethod
    def answer_comment(cls, course_uuid, assignment_uuid, answer_uuid, answer_comment_uuid):
        return cls.answer(course_uuid, assignment_uuid, answer_uuid)+'/comment/'+answer_comment_uuid


    @classmethod
    def attachment(cls, file_name):
        return cls._get_attachment_url()+quote(file_name)

    @classmethod
    def report(cls, file_name):
        return cls._get_report_url()+quote(file_name)