# sqlalchemy
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import load_only
from sqlalchemy import func, select, and_, or_
from sqlalchemy.ext.hybrid import hybrid_property
from flask import current_app
from sqlalchemy_enum34 import EnumType

from . import *
from importlib import import_module

from compair.core import db
from compair.algorithms import ScoredObject, ComparisonPair, ComparisonWinner
from compair.algorithms.pair import generate_pair
from compair.algorithms.score import calculate_score, calculate_score_1vs1


class Comparison(DefaultTableMixin, UUIDMixin, WriteTrackingMixin):
    __tablename__ = 'comparison'

    # table columns
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignment.id', ondelete="CASCADE"),
        nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete="CASCADE"),
        nullable=False)
    answer1_id = db.Column(db.Integer, db.ForeignKey('answer.id', ondelete="CASCADE"),
        nullable=False)
    answer2_id = db.Column(db.Integer, db.ForeignKey('answer.id', ondelete="CASCADE"),
        nullable=False)
    winner = db.Column(EnumType(WinningAnswer, name="winner"), nullable=True)
    comparison_example_id = db.Column(db.Integer, db.ForeignKey('comparison_example.id', ondelete="SET NULL"),
        nullable=True)
    round_compared = db.Column(db.Integer, default=0, nullable=False)
    completed = db.Column(db.Boolean(name='completed'), default=False,
        nullable=False, index=True)
    pairing_algorithm = db.Column(EnumType(PairingAlgorithm, name="pairing_algorithm"),
        nullable=True, default=PairingAlgorithm.random)

    # relationships
    # assignment via Assignment Model
    # user via User Model
    # comparison_example via ComparisonExample Model

    comparison_criteria = db.relationship("ComparisonCriterion", backref="comparison", lazy='immediate')

    answer1 = db.relationship("Answer", foreign_keys=[answer1_id])
    answer2 = db.relationship("Answer", foreign_keys=[answer2_id])

    # hyprid and other functions
    course_id = association_proxy('assignment', 'course_id', creator=lambda course_id:
        import_module('compair.models.assignment').Assignment(course_id=course_id))
    course_uuid = association_proxy('assignment', 'course_uuid')

    assignment_uuid = association_proxy('assignment', 'uuid')

    answer1_uuid = association_proxy('answer1', 'uuid')
    answer2_uuid = association_proxy('answer2', 'uuid')

    user_avatar = association_proxy('user', 'avatar')
    user_uuid = association_proxy('user', 'uuid')
    user_displayname = association_proxy('user', 'displayname')
    user_fullname = association_proxy('user', 'fullname')
    user_system_role = association_proxy('user', 'system_role')

    @classmethod
    def get_by_uuid_or_404(cls, model_uuid, joinedloads=[], title=None, message=None):
        if not title:
            title = "Comparison Unavailable"
        if not message:
            message = "Sorry, this comparison was deleted or is no longer accessible."
        return super(cls, cls).get_by_uuid_or_404(model_uuid, joinedloads, title, message)

    @classmethod
    def __declare_last__(cls):
        super(cls, cls).__declare_last__()

    def comparison_pair_winner(self):
        from . import WinningAnswer
        winner = None
        if self.winner == WinningAnswer.answer1:
            winner = ComparisonWinner.key1
        elif self.winner == WinningAnswer.answer2:
            winner = ComparisonWinner.key2
        elif self.winner == WinningAnswer.draw:
            winner = ComparisonWinner.draw
        return winner

    def convert_to_comparison_pair(self):
        return ComparisonPair(
            key1=self.answer1_id,
            key2=self.answer2_id,
            winner=self.comparison_pair_winner()
        )

    @classmethod
    def _get_new_comparison_pair(cls, course_id, assignment_id, user_id, pairing_algorithm, comparisons):
        from . import Assignment, UserCourse, CourseRole, Answer, AnswerScore, \
            PairingAlgorithm, AnswerCriterionScore, AssignmentCriterion

        # ineligible authors - eg. instructors, TAs, dropped student, current user
        non_students = UserCourse.query \
            .filter(and_(
                UserCourse.course_id == course_id,
                UserCourse.course_role != CourseRole.student
            ))
        ineligible_user_ids = [non_student.user_id \
            for non_student in non_students]
        ineligible_user_ids.append(user_id)

        answers_with_score = Answer.query \
            .with_entities(Answer, AnswerScore.score ) \
            .outerjoin(AnswerScore) \
            .filter(and_(
                Answer.user_id.notin_(ineligible_user_ids),
                Answer.assignment_id == assignment_id,
                Answer.active == True,
                Answer.practice == False,
                Answer.draft == False
            )) \
            .all()

        scored_objects = []
        for answer_with_score in answers_with_score:
            scored_objects.append(ScoredObject(
                key=answer_with_score.Answer.id,
                score=answer_with_score.score,
                rounds=answer_with_score.Answer.round,
                variable1=None, variable2=None,
                wins=None, loses=None, opponents=None
            ))

        comparison_pairs = [comparison.convert_to_comparison_pair() for comparison in comparisons]

        # adaptive min delta algo requires extra criterion specific parameters
        if pairing_algorithm == PairingAlgorithm.adaptive_min_delta:
            # retreive extra criterion score data
            answers_with_criterion_score = Answer.query \
                .with_entities(Answer, AnswerCriterionScore.criterion_id, AnswerCriterionScore.score) \
                .join(AnswerCriterionScore) \
                .filter(and_(
                    Answer.user_id.notin_(ineligible_user_ids),
                    Answer.assignment_id == assignment_id,
                    Answer.active == True,
                    Answer.practice == False,
                    Answer.draft == False
                )) \
                .all()

            assignment_criterion_weights = AssignmentCriterion.query \
                .with_entities(AssignmentCriterion.criterion_id, AssignmentCriterion.weight) \
                .filter(and_(
                    AssignmentCriterion.assignment_id == assignment_id,
                    AssignmentCriterion.active == True
                )) \
                .all()

            criterion_scores = {}
            for answer_with_criterion_score in answers_with_criterion_score:
                key = answer_with_criterion_score.Answer.id
                scores = criterion_scores.setdefault(key, {})
                scores[answer_with_criterion_score.criterion_id] = \
                    answer_with_criterion_score.score

            criterion_weights = {}
            for the_weight in assignment_criterion_weights:
                criterion_weights[the_weight.criterion_id] = \
                    the_weight.weight

            comparison_pair = generate_pair(
                package_name=pairing_algorithm.value,
                scored_objects=scored_objects,
                comparison_pairs=comparison_pairs,
                criterion_scores=criterion_scores,
                criterion_weights=criterion_weights,
                log=current_app.logger
            )
        else:
            comparison_pair = generate_pair(
                package_name=pairing_algorithm.value,
                scored_objects=scored_objects,
                comparison_pairs=comparison_pairs,
                log=current_app.logger
            )

        return comparison_pair

    @classmethod
    def create_new_comparison(cls, assignment_id, user_id, skip_comparison_examples):
        from . import Assignment, ComparisonExample, ComparisonCriterion

        # get all comparisons for the user
        comparisons = Comparison.query \
            .filter_by(
                user_id=user_id,
                assignment_id=assignment_id
            ) \
            .all()

        is_comparison_example_set = False
        answer1 = None
        answer2 = None
        comparison_example_id = None
        round_compared = 0

        assignment = Assignment.query.get(assignment_id)
        pairing_algorithm = assignment.pairing_algorithm
        if pairing_algorithm == None:
            pairing_algorithm = PairingAlgorithm.random

        if not skip_comparison_examples:
            # check comparison examples first
            comparison_examples = ComparisonExample.query \
                .filter_by(
                    assignment_id=assignment_id,
                    active=True
                ) \
                .all()

            # check if user has not completed all comparison examples
            for comparison_example in comparison_examples:
                comparison = next(
                    (c for c in comparisons if c.comparison_example_id == comparison_example.id),
                    None
                )
                if comparison == None:
                    is_comparison_example_set = True
                    answer1 = comparison_example.answer1
                    answer2 = comparison_example.answer2
                    comparison_example_id = comparison_example.id
                    break

        if not is_comparison_example_set:
            comparison_pair = Comparison._get_new_comparison_pair(assignment.course_id,
                assignment_id, user_id, pairing_algorithm, comparisons)
            answer1 = Answer.query.get(comparison_pair.key1)
            answer2 = Answer.query.get(comparison_pair.key2)
            round_compared = min(answer1.round+1, answer2.round+1)

            # update round counters
            answers = [answer1, answer2]
            for answer in answers:
                answer.round += 1
                db.session.add(answer)

        comparison = Comparison(
            assignment_id=assignment_id,
            user_id=user_id,
            answer1_id=answer1.id,
            answer2_id=answer2.id,
            winner=None,
            round_compared=round_compared,
            comparison_example_id=comparison_example_id,
            pairing_algorithm=pairing_algorithm
        )
        db.session.add(comparison)

        for criterion in assignment.criteria:
            comparison_criterion = ComparisonCriterion(
                comparison=comparison,
                criterion_id=criterion.id,
                winner=None,
                content=None,
            )
        db.session.commit()

        return comparison

    @classmethod
    def update_scores_1vs1(cls, comparison):
        from . import AnswerScore, AnswerCriterionScore, \
            ComparisonCriterion, ScoringAlgorithm

        assignment_id = comparison.assignment_id
        answer1_id = comparison.answer1_id
        answer2_id = comparison.answer2_id

        # get all other comparisons for the answers not including the ones being calculated
        other_comparisons = Comparison.query \
            .options(load_only('winner', 'answer1_id', 'answer2_id')) \
            .filter(and_(
                Comparison.assignment_id == assignment_id,
                Comparison.id != comparison.id,
                or_(
                    Comparison.answer1_id.in_([answer1_id, answer2_id]),
                    Comparison.answer2_id.in_([answer1_id, answer2_id])
                )
            )) \
            .all()

        scores = AnswerScore.query \
            .filter( AnswerScore.answer_id.in_([answer1_id, answer2_id]) ) \
            .all()

        # get all other criterion comparisons for the answers not including the ones being calculated
        other_criterion_comparisons = ComparisonCriterion.query \
            .join("comparison") \
            .filter(and_(
                Comparison.assignment_id == assignment_id,
                ~Comparison.id == comparison.id,
                or_(
                    Comparison.answer1_id.in_([answer1_id, answer2_id]),
                    Comparison.answer2_id.in_([answer1_id, answer2_id])
                )
            )) \
            .all()

        criteria_scores = AnswerCriterionScore.query \
            .filter( AnswerCriterionScore.answer_id.in_([answer1_id, answer2_id]) ) \
            .all()

        #update answer criterion scores
        updated_criteria_scores = []
        for comparison_criterion in comparison.comparison_criteria:
            criterion_id = comparison_criterion.criterion_id

            score1 = next((criterion_score for criterion_score in criteria_scores
                if criterion_score.answer_id == answer1_id and criterion_score.criterion_id == criterion_id),
                AnswerCriterionScore(assignment_id=assignment_id, answer_id=answer1_id, criterion_id=criterion_id)
            )
            updated_criteria_scores.append(score1)
            key1_scored_object = score1.convert_to_scored_object() if score1 != None else ScoredObject(
                key=answer1_id, score=None, variable1=None, variable2=None,
                rounds=0, wins=0, opponents=0, loses=0,
            )

            score2 = next((criterion_score for criterion_score in criteria_scores
                if criterion_score.answer_id == answer2_id and criterion_score.criterion_id == criterion_id),
                AnswerCriterionScore(assignment_id=assignment_id, answer_id=answer2_id, criterion_id=criterion_id)
            )
            updated_criteria_scores.append(score2)
            key2_scored_object = score2.convert_to_scored_object() if score2 != None else ScoredObject(
                key=answer2_id, score=None, variable1=None, variable2=None,
                rounds=0, wins=0, opponents=0, loses=0,
            )

            result_1, result_2 = calculate_score_1vs1(
                package_name=ScoringAlgorithm.elo.value,
                key1_scored_object=key1_scored_object,
                key2_scored_object=key2_scored_object,
                winner=comparison_criterion.comparison_pair_winner(),
                other_comparison_pairs=[c.convert_to_comparison_pair() for c in other_criterion_comparisons if c.criterion_id == criterion_id],
                log=current_app.logger
            )

            for score, result in [(score1, result_1), (score2, result_2)]:
                score.score = result.score
                score.variable1 = result.variable1
                score.variable2 = result.variable2
                score.rounds = result.rounds
                score.wins = result.wins
                score.loses = result.loses
                score.opponents = result.opponents

        updated_scores = []
        score1 = next((score for score in scores if score.answer_id == answer1_id),
            AnswerScore(assignment_id=assignment_id, answer_id=answer1_id)
        )
        updated_scores.append(score1)
        key1_scored_object = score1.convert_to_scored_object() if score1 != None else ScoredObject(
            key=answer1_id, score=None, variable1=None, variable2=None,
            rounds=0, wins=0, opponents=0, loses=0,
        )

        score2 = next((score for score in scores if score.answer_id == answer2_id),
            AnswerScore(assignment_id=assignment_id, answer_id=answer2_id)
        )
        updated_scores.append(score2)
        key2_scored_object = score2.convert_to_scored_object() if score2 != None else ScoredObject(
            key=answer2_id, score=None, variable1=None, variable2=None,
            rounds=0, wins=0, opponents=0, loses=0,
        )

        result_1, result_2 = calculate_score_1vs1(
            package_name=ScoringAlgorithm.elo.value,
            key1_scored_object=key1_scored_object,
            key2_scored_object=key2_scored_object,
            winner=comparison.comparison_pair_winner(),
            other_comparison_pairs=[c.convert_to_comparison_pair() for c in other_comparisons],
            log=current_app.logger
        )

        for score, result in [(score1, result_1), (score2, result_2)]:
            score.score = result.score
            score.variable1 = result.variable1
            score.variable2 = result.variable2
            score.rounds = result.rounds
            score.wins = result.wins
            score.loses = result.loses
            score.opponents = result.opponents

        db.session.add_all(updated_criteria_scores)
        db.session.add_all(updated_scores)
        db.session.commit()

        return updated_scores

    @classmethod
    def calculate_scores(cls, assignment_id):
        from . import AnswerScore, AnswerCriterionScore, \
            AssignmentCriterion, ScoringAlgorithm
        # get all comparisons for this assignment and only load the data we need
        comparisons = Comparison.query \
            .filter(Comparison.assignment_id == assignment_id) \
            .all()

        assignment_criteria = AssignmentCriterion.query \
            .with_entities(AssignmentCriterion.criterion_id) \
            .filter_by(assignment_id=assignment_id, active=True) \
            .all()

        comparison_criteria = []

        comparison_pairs = []
        answer_ids = set()
        for comparison in comparisons:
            answer_ids.add(comparison.answer1_id)
            answer_ids.add(comparison.answer2_id)
            comparison_criteria.extend(comparison.comparison_criteria)
            comparison_pairs.append(comparison.convert_to_comparison_pair())

        # calculate answer score

        comparison_results = calculate_score(
            package_name=ScoringAlgorithm.elo.value,
            comparison_pairs=comparison_pairs,
            log=current_app.logger
        )

        scores = AnswerScore.query \
            .filter(AnswerScore.answer_id.in_(answer_ids)) \
            .all()
        updated_answer_scores = update_answer_scores(scores, assignment_id, comparison_results)
        db.session.add_all(updated_answer_scores)

        # calculate answer criterion scores
        criterion_comparison_results = {}

        for assignment_criterion in assignment_criteria:
            comparison_pairs = []
            for comparison_criterion in comparison_criteria:
                if comparison_criterion.criterion_id != assignment_criterion.criterion_id:
                    continue

                comparison_pairs.append(comparison_criterion.convert_to_comparison_pair())

            criterion_comparison_results[assignment_criterion.criterion_id] = calculate_score(
                package_name=ScoringAlgorithm.elo.value,
                comparison_pairs=comparison_pairs,
                log=current_app.logger
            )

        scores = AnswerCriterionScore.query \
            .filter(AnswerCriterionScore.answer_id.in_(answer_ids)) \
            .all()
        updated_answer_criteria_scores = update_answer_criteria_scores(scores, assignment_id, criterion_comparison_results)
        db.session.add_all(updated_answer_criteria_scores)

        db.session.commit()

def update_answer_scores(scores, assignment_id, comparison_results):
    from . import AnswerScore

    updated_scores = []
    for answer_id, comparison_results in comparison_results.items():
        score = next((score for score in scores
            if score.answer_id == answer_id),
            AnswerScore(assignment_id=assignment_id, answer_id=answer_id)
        )
        updated_scores.append(score)

        score.score = comparison_results.score
        score.variable1 = comparison_results.variable1
        score.variable2 = comparison_results.variable2
        score.rounds = comparison_results.rounds
        score.wins = comparison_results.wins
        score.loses = comparison_results.loses
        score.opponents = comparison_results.opponents

    return updated_scores


def update_answer_criteria_scores(scores, assignment_id, criterion_comparison_results):
    from . import AnswerCriterionScore

    updated_scores = []
    for criterion_id, criterion_comparison_result in criterion_comparison_results.items():
        for answer_id, comparison_results in criterion_comparison_result.items():
            score = next((score for score in scores
                if score.answer_id == answer_id and score.criterion_id == criterion_id),
                AnswerCriterionScore(assignment_id=assignment_id, answer_id=answer_id, criterion_id=criterion_id)
            )
            updated_scores.append(score)

            score.score = comparison_results.score
            score.variable1 = comparison_results.variable1
            score.variable2 = comparison_results.variable2
            score.rounds = comparison_results.rounds
            score.wins = comparison_results.wins
            score.loses = comparison_results.loses
            score.opponents = comparison_results.opponents

    return updated_scores