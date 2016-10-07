from requests.utils import quote

from .xapi import XAPI

class XAPIResourceIRI(object):
    @classmethod
    def _get_app_url(cls):
        return XAPI.get_base_url()+'app/xapi/'

    @classmethod
    def _get_attachment_url(cls):
        return XAPI.get_base_url()+'app/pdf/'

    @classmethod
    def _get_report_url(cls):
        return XAPI.get_base_url()+'app/report/'

    @classmethod
    def actor_homepage(cls):
        return XAPI.get_base_url()

    # xapi resource urls
    @classmethod
    def compair(cls):
        return XAPI.get_base_url()

    @classmethod
    def user_profile(cls, user_uuid):
        return XAPI.get_base_url()+'app/#/user/'+user_uuid

    @classmethod
    def course(cls, course_uuid):
        return cls._get_app_url()+'course/'+course_uuid

    @classmethod
    def criterion(cls, criterion_uuid):
        return cls._get_app_url()+'criterion/'+criterion_uuid

    @classmethod
    def assignment(cls, assignment_uuid):
        return cls._get_app_url()+'assignment/'+assignment_uuid

    @classmethod
    def assignment_question(cls, assignment_uuid):
        return cls._get_app_url()+'assignment/'+assignment_uuid+"/question"

    @classmethod
    def comparison_question(cls, assignment_uuid, answer1_uuid, answer2_uuid):
        uuids = [answer1_uuid, answer2_uuid]
        uuids.sort()
        return cls._get_app_url()+'assignment/'+assignment_uuid+"/comparison?pair="+uuids[0]+","+uuids[1]

    @classmethod
    def self_evaluation_question(cls, assignment_uuid):
        return cls._get_app_url()+'assignment/'+assignment_uuid+"/self-evaluation"

    @classmethod
    def answer(cls, answer_uuid):
        return cls._get_app_url()+'answer/'+answer_uuid

    @classmethod
    def answer_criterion(cls, answer_uuid, criterion_uuid):
        return cls._get_app_url()+'answer/'+answer_uuid+"?criterion="+criterion_uuid

    @classmethod
    def answer_comment(cls, answer_comment_uuid):
        return cls._get_app_url()+'answer/comment/'+answer_comment_uuid

    @classmethod
    def assignment_comment(cls, assignment_comment_uuid):
        return cls._get_app_url()+'assignment/comment/'+assignment_comment_uuid

    @classmethod
    def comparison(cls, comparison_uuid):
        return cls._get_app_url()+'comparison/'+comparison_uuid

    @classmethod
    def attachment(cls, file_name):
        return cls._get_attachment_url()+quote(file_name)

    @classmethod
    def report(cls, file_name):
        return cls._get_report_url()+quote(file_name)