from tincan import  Activity, ActivityDefinition

class XAPIActivity(object):
    activity_types = {
        'page': 'http://activitystrea.ms/schema/1.0/page',
        'comment': 'http://activitystrea.ms/schema/1.0/comment',

        'attempt': 'http://adlnet.gov/expapi/activities/attempt',
        'course': 'http://adlnet.gov/expapi/activities/course',
        'group': 'http://activitystrea.ms/schema/1.0/group',
        'assessment': 'http://adlnet.gov/expapi/activities/assessment',
        'question': 'http://adlnet.gov/expapi/activities/question',
        'solution': 'http://id.tincanapi.com/activitytype/solution',
        'file': 'http://activitystrea.ms/schema/1.0/file',
        'review': 'http://activitystrea.ms/schema/1.0/review',
        'section': 'http://id.tincanapi.com/activitytype/section',
        'modal': 'http://xapi.learninganalytics.ubc.ca/activitytype/modal',
        'user profile': 'http://id.tincanapi.com/activitytype/user-profile',
        'service': 'http://activitystrea.ms/schema/1.0/service'
    }

    @classmethod
    def compair_source(cls):
        return Activity(
            id='http://xapi.learninganalytics.ubc.ca/category/compair',
            definition=ActivityDefinition(
                type='http://id.tincanapi.com/activitytype/source'
            )
        )