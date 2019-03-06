# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import pytz

from tincan import Result, Extensions, Score

from compair.learning_records.learning_record import LearningRecord
from compair.learning_records.resource_iri import ResourceIRI
from compair.learning_records.xapi.activity import XAPIActivity

from compair.models import WinningAnswer

class XAPIResult(object):
    @classmethod
    def basic(cls, **kwargs):
        result = Result()

        if kwargs:
            if kwargs.get('success') != None:
                result.success = kwargs.get('success')
            if kwargs.get('completion') != None:
                result.completion = kwargs.get('completion')
            if kwargs.get('changes') != None:
                result.extensions = Extensions() if not result.extensions else result.extensions
                result.extensions['http://xapi.learninganalytics.ubc.ca/extension/changes'] = kwargs.get('changes')

        return result

    @classmethod
    def basic_content(cls, content, **kwargs):
        result = cls.basic(**kwargs)

        if content:
            result.response = LearningRecord.trim_text_to_size_limit(content)
            result.extensions = Extensions() if not result.extensions else result.extensions

            character_count = LearningRecord.character_count(content)
            result.extensions['http://xapi.learninganalytics.ubc.ca/extension/character-count'] = character_count

            word_count = LearningRecord.word_count(content)
            result.extensions['http://xapi.learninganalytics.ubc.ca/extension/word-count'] = word_count

        return result

    @classmethod
    def basic_attempt(cls, attempt_mixin_object, content, **kwargs):
        result = cls.basic_content(content, **kwargs)

        if attempt_mixin_object.attempt_duration:
            result.duration = attempt_mixin_object.attempt_duration

        return result


    @classmethod
    def answer_score(cls, answer, score, **kwargs):
        from compair.models import ScoringAlgorithm

        result = cls.basic(**kwargs)
        result.extensions = Extensions() if not result.extensions else result.extensions

        result.score = Score(raw=score.score)

        score_details = {
            'score': score.score,
            'algorithm': score.scoring_algorithm.value,
            'wins': score.wins,
            'loses': score.loses,
            'rounds': score.rounds,
            'opponents': score.opponents,
            'criteria': {}
        }

        if score.scoring_algorithm == ScoringAlgorithm.true_skill:
            score_details['mu'] = score.variable1
            score_details['sigma'] = score.variable2

        for criterion_score in answer.criteria_scores:
            criterion_score_details = {
                'score': criterion_score.score,
                'wins': criterion_score.wins,
                'loses': criterion_score.loses,
                'rounds': criterion_score.rounds,
                'opponents': criterion_score.opponents,
            }

            if criterion_score.scoring_algorithm == ScoringAlgorithm.true_skill:
                criterion_score_details['mu'] = criterion_score.variable1
                criterion_score_details['sigma'] = criterion_score.variable2

            score_details['criteria'][ResourceIRI.criterion(criterion_score.criterion_uuid)] = criterion_score_details

        result.extensions['http://xapi.learninganalytics.ubc.ca/extension/score-details'] = score_details

        return result

    @classmethod
    def comparison(cls, comparison, **kwargs):
        result = cls.basic_attempt(comparison, None, **kwargs)
        result.extensions = Extensions() if not result.extensions else result.extensions

        winner = "Undecided"
        if comparison.winner == WinningAnswer.draw:
            winner = "Draw"
        elif comparison.winner == WinningAnswer.answer1:
            winner = ResourceIRI.answer(comparison.course_uuid, comparison.assignment_uuid, comparison.answer1_uuid)
        elif comparison.winner == WinningAnswer.answer2:
            winner = ResourceIRI.answer(comparison.course_uuid, comparison.assignment_uuid, comparison.answer2_uuid)
        result.response = winner

        result.extensions['http://xapi.learninganalytics.ubc.ca/extension/criteria'] = {}
        for comparison_criterion in comparison.comparison_criteria:
            winner = "Undecided"
            if comparison_criterion.winner == WinningAnswer.answer1:
                winner = ResourceIRI.answer(comparison.course_uuid, comparison.assignment_uuid, comparison.answer1_uuid)
            elif comparison_criterion.winner == WinningAnswer.answer2:
                winner = ResourceIRI.answer(comparison.course_uuid, comparison.assignment_uuid, comparison.answer2_uuid)

            result.extensions['http://xapi.learninganalytics.ubc.ca/extension/criteria'][
                ResourceIRI.criterion(comparison_criterion.criterion_uuid)] = winner

        return result

