from flask import current_app, request
from six import text_type
import datetime
import pytz
import re

class LearningRecord(object):
    _version = None

    @classmethod
    def enabled(cls):
        return False

    @classmethod
    def get_base_url(cls):
        base_url = current_app.config.get('LRS_APP_BASE_URL')

        if not base_url:
            base_url = request.url_root if request else ''

        return base_url.rstrip('/')

    @classmethod
    def get_sis_course_id_uri_template(cls):
        return current_app.config.get('LRS_SIS_COURSE_ID_URI_TEMPLATE')

    @classmethod
    def get_sis_section_id_uri_template(cls):
        return current_app.config.get('LRS_SIS_SECTION_ID_URI_TEMPLATE')

    @classmethod
    def emit(cls, record):
        return

    @classmethod
    def generate_timestamp(cls):
        return datetime.datetime.utcnow().replace(tzinfo=pytz.utc).isoformat()

    @classmethod
    def _unescape(cls, text):
        # equivalent to lodash's _.unescape()
        text = text.replace('&amp;', '&')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = text.replace('&quot;', '"')
        text = text.replace('&#39;', '\'')
        return text

    @classmethod
    def _strip_html(cls, text):
        text = re.sub('<[^>]+>', '', text_type(text))
        text = text.replace('&nbsp;', ' ')
        return cls._unescape(text)

    @classmethod
    def character_count(cls, text):
        text = cls._strip_html(text)
        text = re.sub('(\r\n|\n|\r)', ' ', text)
        return len(text)

    @classmethod
    def word_count(cls, text):
        text = cls._strip_html(text)
        text = re.sub('(\r\n|\n|\r)', ' ', text)
        words = [word for word in re.split('\s+', text) if len(word) > 0]
        return len(words)

    @classmethod
    def trim_text_to_size_limit(cls, text):
        if not text:
            return ''

        if current_app.config.get('LRS_USER_INPUT_FIELD_SIZE_LIMIT'):
            size_limit = current_app.config.get('LRS_USER_INPUT_FIELD_SIZE_LIMIT')
            encoded_text = text.encode('utf-8')

            # if encoded_text is larger than size_limit, trim it
            if len(encoded_text) > size_limit:
                encoded_text = encoded_text[:size_limit]
                return text_type(encoded_text.decode('utf-8', 'ignore'))+" [TEXT TRIMMED]..."

        return text

    @classmethod
    def _emit_to_lrs(cls, record_json):
        return
