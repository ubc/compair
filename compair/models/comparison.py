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
from compair.algorithms import ScoredObject, ComparisonPair, ScoredObject
from compair.algorithms.pair import generate_pair
from compair.algorithms.score import calculate_score, calculate_score_1vs1


class Comparison(DefaultTableMixin, UUIDMixin, WriteTrackingMixin):
    __tablename__ = 'comparison'

    # table columns
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignment.id', ondelete="CASCADE"),
        nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete="CASCADE"),
        nullable=False)
    criterion_id = db.Column(db.Integer, db.ForeignKey('criterion.id', ondelete="CASCADE"),
        nullable=False)
    answer1_id = db.Column(db.Integer, db.ForeignKey('answer.id', ondelete="CASCADE"),
        nullable=False)
    answer2_id = db.Column(db.Integer, db.ForeignKey('answer.id', ondelete="CASCADE"),
        nullable=False)
    winner_id = db.Column(db.Integer, db.ForeignKey('answer.id', ondelete="CASCADE"),
        nullable=True)
    comparison_example_id = db.Column(db.Integer, db.ForeignKey('comparison_example.id', ondelete="SET NULL"),
        nullable=True)
    round_compared = db.Column(db.Integer, default=0, nullable=False)
    content = db.Column(db.Text)
    completed = db.Column(db.Boolean(name='completed'), default=False,
        nullable=False, index=True)
    pairing_algorithm = db.Column(EnumType(PairingAlgorithm, name="pairing_algorithm"),
        nullable=True, default=PairingAlgorithm.random)

    # relationships
    # assignment via Assignment Model
    # user via User Model
    # criterion via Criterion Model
    # comparison_example via ComparisonExample Model

    answer1 = db.relationship("Answer", foreign_keys=[answer1_id])
    answer2 = db.relationship("Answer", foreign_keys=[answer2_id])
    winning_answer = db.relationship("Answer", foreign_keys=[winner_id])

    # hyprid and other functions
    course_id = association_proxy('assignment', 'course_id', creator=lambda course_id:
        import_module('compair.models.assignment').Assignment(course_id=course_id))
    course_uuid = association_proxy('assignment', 'course_uuid')

    assignment_uuid = association_proxy('assignment', 'uuid')

    criterion_uuid = association_proxy('criterion', 'uuid')

    answer1_uuid = association_proxy('answer1', 'uuid')
    answer2_uuid = association_proxy('answer2', 'uuid')
    winner_uuid = association_proxy('winning_answer', 'uuid')

    user_avatar = association_proxy('user', 'avatar')
    user_uuid = association_proxy('user', 'uuid')
    user_displayname = association_proxy('user', 'displayname')
    user_fullname = association_proxy('user', 'fullname')
    user_system_role = association_proxy('user', 'system_role')

    def convert_to_comparison_pair(self):
        return ComparisonPair(
            key1=self.answer1_id,
            key2=self.answer2_id,
            winning_key=self.winner_id
        )

    @classmethod
    def comparison_available_for_user(cls, course_id, assignment_id, user_id):
        from . import UserCourse, CourseRole, Answer
        # ineligible authors - eg. instructors, TAs, dropped student, user
        ineligible_users = UserCourse.query. \
            filter(and_(
                UserCourse.course_id == course_id,
                UserCourse.course_role != CourseRole.student
            )). \
            values(UserCourse.user_id)
        ineligible_user_ids_base = [u[0] for u in ineligible_users]
        ineligible_user_ids_base.append(user_id)

        # ineligible authors (potentially) - eg. authors for answers that the user has seen
        compared = Comparison.query \
            .filter_by(
                user_id=user_id,
                assignment_id=assignment_id
            ) \
            .all()
        compared_authors1 = [c.answer1.user_id for c in compared]
        compared_authors2 = [c.answer2.user_id for c in compared]
        ineligible_user_ids = ineligible_user_ids_base + compared_authors1 + compared_authors2

        eligible_answers = Answer.query \
            .filter(and_(
                Answer.assignment_id == assignment_id,
                Answer.user_id.notin_(ineligible_user_ids),
                Answer.draft == False,
                Answer.active == True
            )) \
            .count()
        return eligible_answers / 2 >= 1  # min 1 pair required

    @classmethod
    def __declare_last__(cls):
        super(cls, cls).__declare_last__()

    @classmethod
    def _get_new_comparison_pair(cls, course_id, assignment_id, user_id, pairing_algorithm, comparisons):
        from . import Assignment, UserCourse, CourseRole, Answer, Score, PairingAlgorithm

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
            .with_entities(Answer, func.avg(Score.score).label('average_score') ) \
            .outerjoin(Score) \
            .filter(and_(
                Answer.user_id.notin_(ineligible_user_ids),
                Answer.assignment_id == assignment_id,
                Answer.active == True,
                Answer.practice == False,
                Answer.draft == False
            )) \
            .group_by(Answer.id)

        scored_objects = []
        for answer_with_score in answers_with_score:
            scored_objects.append(ScoredObject(
                key=answer_with_score.Answer.id,
                score=answer_with_score.average_score,
                rounds=answer_with_score.Answer.round,
                variable1=None, variable2=None,
                wins=None, loses=None, opponents=None
            ))

        comparison_pairs = [ComparisonPair(
            comparison.answer1_id, comparison.answer2_id, winning_key=None
        ) for comparison in comparisons]

        comparison_pair = generate_pair(
            package_name=pairing_algorithm.value,
            scored_objects=scored_objects,
            comparison_pairs=comparison_pairs,
            log=current_app.logger
        )

        return comparison_pair

    @classmethod
    def create_new_comparison_set(cls, assignment_id, user_id, skip_comparison_examples):
        from . import Assignment, UserCourse, CourseRole, Answer, Score, ComparisonExample

        # get all comparisons for the user
        comparisons = Comparison.query \
            .with_entities(Comparison.answer1_id, Comparison.answer2_id, Comparison.comparison_example_id) \
            .distinct() \
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
            db.session.commit()

        new_comparisons = []
        for criterion in assignment.criteria:
            comparison = Comparison(
                assignment_id=assignment_id,
                user_id=user_id,
                criterion_id=criterion.id,
                answer1_id=answer1.id,
                answer2_id=answer2.id,
                winner_id=None,
                round_compared=round_compared,
                comparison_example_id=comparison_example_id,
                content=None,
                pairing_algorithm=pairing_algorithm
            )
            db.session.add(comparison)
            db.session.commit()
            new_comparisons.append(comparison)

        return new_comparisons

    @classmethod
    def update_scores_1vs1(cls, comparisons):
        from . import Score, ScoringAlgorithm

        assignment_id = comparisons[0].assignment_id
        answer1_id = comparisons[0].answer1_id
        answer2_id = comparisons[0].answer2_id

        # get all other comparisons for the answers not including the ones being calculated
        other_comparisons = Comparison.query . \
            options(load_only('winner_id', 'criterion_id', 'answer1_id', 'answer2_id')) . \
            filter(and_(
                Comparison.assignment_id == assignment_id,
                ~Comparison.id.in_([comparison.id for comparison in comparisons]),
                or_(
                    Comparison.answer1_id.in_([answer1_id, answer2_id]),
                    Comparison.answer2_id.in_([answer1_id, answer2_id])
                )
            )) \
            .all()

        scores = Score.query \
            .filter( Score.answer_id.in_([answer1_id, answer2_id]) ) \
            .all()

        updated_scores = []
        for comparison in comparisons:
            score1 = next((score for score in scores
                if score.answer_id == answer1_id and score.criterion_id == comparison.criterion_id),
                Score(assignment_id=assignment_id, answer_id=answer1_id, criterion_id=comparison.criterion_id)
            )
            updated_scores.append(score1)
            key1_scored_object = score1.convert_to_scored_object() if score1 != None else ScoredObject(
                key=answer1_id, score=None, variable1=None, variable2=None,
                rounds=0, wins=0, opponents=0, loses=0,
            )

            score2 = next((score for score in scores
                if score.answer_id == answer2_id and score.criterion_id == comparison.criterion_id),
                Score(assignment_id=assignment_id, answer_id=answer2_id, criterion_id=comparison.criterion_id)
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
                winning_key=comparison.winner_id,
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

        db.session.add_all(updated_scores)
        db.session.commit()

        return updated_scores

    @classmethod
    def calculate_scores(cls, assignment_id):
        from . import Score, AssignmentCriterion, ScoringAlgorithm
        # get all comparisons for this assignment and only load the data we need
        comparisons = Comparison.query \
            .options(load_only('winner_id', 'criterion_id', 'answer1_id', 'answer2_id')) \
            .filter(Comparison.assignment_id == assignment_id) \
            .all()

        assignment_criteria = AssignmentCriterion.query \
            .with_entities(AssignmentCriterion.criterion_id) \
            .filter_by(assignment_id=assignment_id, active=True) \
            .all()

        criterion_comparison_results = {}
        answer_ids = set()
        for assignment_criterion in assignment_criteria:
            comparison_pairs = []
            for comparison in comparisons:
                if comparison.criterion_id != assignment_criterion.criterion_id:
                    continue
                answer_ids.add(comparison.answer1_id)
                answer_ids.add(comparison.answer2_id)

                comparison_pairs.append(comparison.convert_to_comparison_pair())

            criterion_comparison_results[assignment_criterion.criterion_id] = calculate_score(
                package_name=ScoringAlgorithm.elo.value,
                comparison_pairs=comparison_pairs,
                log=current_app.logger
            )

        # load existing scores
        scores = Score.query.filter(Score.answer_id.in_(answer_ids)). \
            order_by(Score.answer_id, Score.criterion_id).all()

        updated_scores = update_scores(scores, assignment_id, criterion_comparison_results)
        db.session.add_all(updated_scores)
        db.session.commit()

        return updated_scores


def update_scores(scores, assignment_id, criterion_comparison_results):
    from . import Score

    updated_scores = []
    for criterion_id, criterion_comparison_result in criterion_comparison_results.items():
        for answer_id, comparison_results in criterion_comparison_result.items():
            score = next((score for score in scores
                if score.answer_id == answer_id and score.criterion_id == criterion_id),
                Score(assignment_id=assignment_id, answer_id=answer_id, criterion_id=criterion_id)
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