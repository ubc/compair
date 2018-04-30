from tincan import Verb, LanguageMap

class XAPIVerb(object):
    verbs = {
        'earned': 'http://specification.openbadges.org/xapi/verbs/earned',
        'viewed': 'http://id.tincanapi.com/verb/viewed',
        'commented': 'http://adlnet.gov/expapi/verbs/commented',
        'up voted': 'http://id.tincanapi.com/verb/voted-up',
        'down voted': 'http://id.tincanapi.com/verb/voted-down',
        'vote canceled': 'http://id.tincanapi.com/verb/voted-cancel',
        'favorited': 'http://activitystrea.ms/schema/1.0/favorite',
        'unfavorited': 'http://activitystrea.ms/schema/1.0/unfavorite',
        'authored': 'http://activitystrea.ms/schema/1.0/author',
        'deleted': 'http://activitystrea.ms/schema/1.0/delete',
        'updated': 'http://activitystrea.ms/schema/1.0/update',
        'retracted': 'http://activitystrea.ms/schema/1.0/retract',

        'initialized': 'http://adlnet.gov/expapi/verbs/initialized',
        'resumed': 'http://adlnet.gov/expapi/verbs/resumed',
        'interacted': 'http://adlnet.gov/expapi/verbs/interacted',
        'completed': 'http://adlnet.gov/expapi/verbs/completed',
        'suspended': 'http://adlnet.gov/expapi/verbs/suspended',
        'exited': 'http://adlnet.gov/expapi/verbs/exited',

        'attached': 'http://activitystrea.ms/schema/1.0/attach',
        'submitted': 'http://activitystrea.ms/schema/1.0/submit',
        'evaluated': 'http://www.tincanapi.co.uk/verbs/evaluated',
        'downloaded': 'http://id.tincanapi.com/verb/downloaded',

        'logged in': 'https://brindlewaye.com/xAPITerms/verbs/loggedin/',
        'logged out': 'https://brindlewaye.com/xAPITerms/verbs/loggedout/',
        'opened': 'http://activitystrea.ms/schema/1.0/open',
        'closed': 'http://activitystrea.ms/schema/1.0/close',
        'drafted': 'http://xapi.learninganalytics.ubc.ca/verb/draft',
        'filtered': 'http://xapi.learninganalytics.ubc.ca/verb/filter',
        'sorted': 'http://xapi.learninganalytics.ubc.ca/verb/sort'
    }

    @classmethod
    def _validate_verb(cls, verb):
        return verb in cls.verbs.keys()

    @classmethod
    def generate(cls, verb):
        if cls._validate_verb(verb):
            verb_id = cls.verbs.get(verb)
            return Verb(
                id=verb_id,
                display=LanguageMap({ 'en-US': verb })
            )

        return None