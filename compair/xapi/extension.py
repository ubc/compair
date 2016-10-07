from tincan import  Activity, ActivityDefinition, LanguageMap


class XAPIExtension(object):
    context_extensions = {
        'browser information': 'http://id.tincanapi.com/extension/browser-info',
        'referer': 'http://nextsoftwaresolutions.com/xapi/extensions/referer',
        'filters': 'http://xapi.ubc.ca/extension/filters',
        'sort order': 'http://xapi.ubc.ca/extension/sort-order',
        'login method': 'http://xapi.ubc.ca/extension/login-method'
    }

    object_extensions = {
        'badgeclass': 'http://standard.openbadges.org/xapi/extensions/badgeclass',
        'comparison': 'http://xapi.ubc.ca/extension/comparison',
        'pair algorithm': 'http://xapi.ubc.ca/extension/score-algorithm'
    }

    result_extensions = {
        'fields changed': 'http://xapi.ubc.ca/extension/fields-changed',
        'character count': 'http://xapi.ubc.ca/extension/character-count',
        'word count': 'http://xapi.ubc.ca/extension/word-count',
        'attachment response': 'http://xapi.ubc.ca/extension/attachment-response',
        'score details': 'http://xapi.ubc.ca/extension/score-details'
    }