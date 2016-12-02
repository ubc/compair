import re

from tincan import Result, Extensions, Score

from .resource_iri import XAPIResourceIRI
from .activity import XAPIActivity
from .extension import XAPIExtension

class XAPIResult(object):
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
        text = re.sub('<[^>]+>', '', str(text))
        text = text.replace('&nbsp;', ' ')
        return cls._unescape(text)

    @classmethod
    def _character_count(cls, text):
        text = cls._strip_html(text)
        text = re.sub('(\r\n|\n|\r)', ' ', text)
        return len(text)

    @classmethod
    def _word_count(cls, text):
        text = cls._strip_html(text)
        text = re.sub('(\r\n|\n|\r)', ' ', text)
        words = [word for word in re.split("\s+", text) if len(word) > 0]
        return len(words)

    @classmethod
    def basic(cls, **kwargs):
        result = Result()

        if kwargs:
            if kwargs.get('duration') != None:
                result.duration = kwargs.get('duration')
            if kwargs.get('success') != None:
                result.success = kwargs.get('success')
            if kwargs.get('completion') != None:
                result.completion = kwargs.get('completion')
            if kwargs.get('changes') != None:
                result.extensions = Extensions() if not result.extensions else result.extensions
                fields_changed_key = XAPIExtension.result_extensions.get('fields changed')
                result.extensions[fields_changed_key] = kwargs.get('changes')

        return result

    @classmethod
    def basic_content(cls, content, **kwargs):
        result = cls.basic(**kwargs)

        result.response = content
        result.extensions = Extensions() if not result.extensions else result.extensions

        character_count = cls._character_count(content) if content else 0
        result.extensions[XAPIExtension.result_extensions.get('character count')] = character_count

        word_count = cls._word_count(content) if content else 0
        result.extensions[XAPIExtension.result_extensions.get('word count')] = word_count

        return result

    @classmethod
    def answer(cls, answer, **kwargs):
        result = cls.basic_content(answer.content, **kwargs)

        if kwargs:
            if kwargs.get('includeAttachment') != None and answer.file:
                result.extensions = Extensions() if not result.extensions else result.extensions
                file_iri = XAPIResourceIRI.attachment(answer.file.name)
                result.extensions[XAPIExtension.result_extensions.get('attachment response')] = file_iri

        return result

    @classmethod
    def answer_evaluation(cls, answer, score, **kwargs):
        from compair.models import ScoringAlgorithm

        result = cls.basic(**kwargs)
        result.extensions = Extensions() if not result.extensions else result.extensions

        result.score = Score(raw=score.score)

        score_details = {
            'algorithm': score.scoring_algorithm.value,
            'wins': score.wins,
            'loses': score.loses,
            'rounds': score.rounds,
            'opponents': score.opponents,
        }

        if score.scoring_algorithm == ScoringAlgorithm.comparative_judgement:
            result.score.min = 0.0
            result.score.max = 1.0
            score_details['expected score'] = score.variable1

        elif score.scoring_algorithm == ScoringAlgorithm.true_skill:
            score_details['mu'] = score.variable1
            score_details['sigma'] = score.variable2

        result.extensions[XAPIExtension.result_extensions.get('score details')] = score_details

        return result

    @classmethod
    def answer_comment(cls, answer_comment, **kwargs):
        result = cls.basic_content(answer_comment.content, **kwargs)

        return result

    @classmethod
    def self_evaluation(cls, answer_comment, **kwargs):
        result = cls.basic_content(answer_comment.content, **kwargs)

        return result

    @classmethod
    def assignment_comment(cls, assignment_comment, **kwargs):
        result = cls.basic_content(assignment_comment.content, **kwargs)

        return result

    @classmethod
    def comparison(cls, comparison, **kwargs):
        result = cls.basic(**kwargs)

        if comparison.winner_id:
            result.response = XAPIResourceIRI.answer(comparison.winner_uuid)
        else:
            result.response = "Undecided"

        return result