from tincan import Verb, LanguageMap

class XAPIVerb(object):
    verbs = {
        'viewed': 'http://id.tincanapi.com/verb/viewed',
        'commented': 'http://adlnet.gov/expapi/verbs/commented',
        'authored': 'http://activitystrea.ms/schema/1.0/author',
        'removed': 'https://w3id.org/xapi/dod-isd/verbs/removed',
        'archived': 'https://w3id.org/xapi/dod-isd/verbs/archived',
        'updated': 'http://activitystrea.ms/schema/1.0/update',

        'initialized': 'http://adlnet.gov/expapi/verbs/initialized',
        'resumed': 'http://adlnet.gov/expapi/verbs/resumed',
        'interacted': 'http://adlnet.gov/expapi/verbs/interacted',
        'completed': 'http://adlnet.gov/expapi/verbs/completed',
        'suspended': 'http://adlnet.gov/expapi/verbs/suspended',
        'exited': 'http://adlnet.gov/expapi/verbs/exited',

        'attached': 'http://activitystrea.ms/schema/1.0/attach',
        'submitted': 'http://activitystrea.ms/schema/1.0/submit',
        'ranked': 'https://w3id.org/xapi/dod-isd/verbs/ranked',
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