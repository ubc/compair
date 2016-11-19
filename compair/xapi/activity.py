from tincan import  Activity, ActivityDefinition, LanguageMap

class XAPIActivity(object):
    activity_types = {
        'badge': 'http://activitystrea.ms/schema/1.0/badge',
        'page': 'http://activitystrea.ms/schema/1.0/page',
        'comment': 'http://activitystrea.ms/schema/1.0/comment',

        'course': 'http://adlnet.gov/expapi/activities/course',
        'assessment': 'http://adlnet.gov/expapi/activities/assessment',
        'question': 'http://adlnet.gov/expapi/activities/question',
        'solution': 'http://id.tincanapi.com/activitytype/solution',
        'file': 'http://activitystrea.ms/schema/1.0/file',
        'review': 'http://activitystrea.ms/schema/1.0/review',
        'section': 'http://id.tincanapi.com/activitytype/section',
        'modal': 'http://xapi.ubc.ca/activitytype/modal',
        'user profile': 'http://id.tincanapi.com/activitytype/user-profile',
        'service': 'http://activitystrea.ms/schema/1.0/service'
    }

    @classmethod
    def compair_source(cls):
        return Activity(
            id='http://xapi.ubc.ca/category/compair',
            definition=ActivityDefinition(
                type='http://id.tincanapi.com/activitytype/source'
            )
        )

    @classmethod
    def ubc_profile(cls):
        return Activity(
            id='http://xapi.ubc.ca/',
            definition=ActivityDefinition(
                type='http://id.tincanapi.com/activitytype/recipe'
            )
        )