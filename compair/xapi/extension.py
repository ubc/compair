from tincan import  Activity, ActivityDefinition, LanguageMap


class XAPIExtension(object):
    context_extensions = {
        'browser information': 'http://id.tincanapi.com/extension/browser-info',
        'referer': 'http://nextsoftwaresolutions.com/xapi/extensions/referer',
        'filters': 'http://xapi.learninganalytics.ubc.ca/extension/filters',
        'sort order': 'http://xapi.learninganalytics.ubc.ca/extension/sort-order',
        'login method': 'http://xapi.learninganalytics.ubc.ca/extension/login-method',
        'impersonating as': 'http://xapi.learninganalytics.ubc.ca/extension/impersonating-as'
    }

    object_extensions = {
        'badgeclass': 'http://standard.openbadges.org/xapi/extensions/badgeclass',
        'comparison': 'http://xapi.learninganalytics.ubc.ca/extension/comparison',
        'pair algorithm': 'http://xapi.learninganalytics.ubc.ca/extension/score-algorithm'
    }

    result_extensions = {
        'fields changed': 'http://xapi.learninganalytics.ubc.ca/extension/fields-changed',
        'character count': 'http://xapi.learninganalytics.ubc.ca/extension/character-count',
        'word count': 'http://xapi.learninganalytics.ubc.ca/extension/word-count',
        'attachment response': 'http://xapi.learninganalytics.ubc.ca/extension/attachment-response',
        'score details': 'http://xapi.learninganalytics.ubc.ca/extension/score-details'
    }