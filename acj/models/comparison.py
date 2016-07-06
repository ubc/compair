# sqlalchemy
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import load_only
from sqlalchemy import func, select, and_, or_
from sqlalchemy.ext.hybrid import hybrid_property
from flask import current_app

from . import *
from importlib import import_module

from acj.core import db
from acj.algorithms import ScoredObject, ComparisonPair, ScoredObject
from acj.algorithms.pair import generate_pair
from acj.algorithms.score import calculate_score, calculate_score_1vs1


class Comparison(DefaultTableMixin, WriteTrackingMixin):
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
    round_compared = db.Column(db.Integer, default=0, nullable=False)
    content = db.Column(db.Text)
    completed = db.Column(db.Boolean(name='completed'), default=False,
        nullable=False, index=True)

    # relationships
    # assignment via Assignment Model
    # user via User Model
    # criterion via Criterion Model

    answer1 = db.relationship("Answer", foreign_keys=[answer1_id])
    answer2 = db.relationship("Answer", foreign_keys=[answer2_id])
    winning_answer = db.relationship("Answer", foreign_keys=[winner_id])

    # hyprid and other functions
    course_id = association_proxy('assignment', 'course_id', creator=lambda course_id:
        import_module('acj.models.assignment').Assignment(course_id=course_id))
    user_avatar = association_proxy('user', 'avatar')
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
    def __declare_last__(cls):
        super(cls, cls).__declare_last__()

    @classmethod
    def create_new_comparison_set(cls, assignment_id, user_id):
        from . import Assignment, UserCourse, CourseRole, Answer, Score

        assignment = Assignment.query.get(assignment_id)

        # ineligible authors - eg. instructors, TAs, dropped student, current user
        non_students = UserCourse.query \
            .filter(and_(
                UserCourse.course_id == assignment.course_id,
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
                Answer.active == True
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

        comparisons = Comparison.query \
            .with_entities(Comparison.answer1_id, Comparison.answer2_id) \
            .distinct() \
            .filter_by(
                user_id=user_id,
                assignment_id=assignment_id
            ) \
            .all()

        comparison_pairs = [ComparisonPair(
            comparison.answer1_id, comparison.answer2_id, winning_key=None
        ) for comparison in comparisons]

        comparison_pair = generate_pair(
            package_name="adaptive",
            scored_objects=scored_objects,
            comparison_pairs=comparison_pairs,
            log=current_app.logger
        )

        answer1 = Answer.query.get(comparison_pair.key1)
        answer2 = Answer.query.get(comparison_pair.key2)

        round_compared = min(answer1.round+1, answer2.round+1)

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
                content=None
            )
            db.session.add(comparison)
            db.session.commit()
            new_comparisons.append(comparison)

        answers = [answer1, answer2]
        for answer in answers:
            # update round counts via sqlalchemy increase counter
            answer.round = Answer.round + 1
            db.session.add(answer)
        db.session.commit()

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
            .filter( Score.answer_id.in_([answer1_id, answer2_id] ) ) \
            .all()

        new_scores = []
        for comparison in comparisons:
            score1 = next((score for score in scores
                if score.answer_id == answer1_id and
                score.criterion_id == comparison.criterion_id),
                None)
            key1_scored_object = score1.convert_to_scored_object() if score1 != None else ScoredObject(
                key=answer1_id, score= None, variable1=None, variable2=None,
                rounds=0, wins=0, opponents=0, loses=0,
            )

            score2 = next((score for score in scores
                if score.answer_id == answer2_id and score.criterion_id == comparison.criterion_id),
                None)
            key2_scored_object = score2.convert_to_scored_object() if score2 != None else ScoredObject(
                key=answer2_id, score= None, variable1=None, variable2=None,
                rounds=0, wins=0, opponents=0, loses=0,
            )

            result_1, result_2 = calculate_score_1vs1(
                package_name=ScoringAlgorithm.true_skill.value,
                key1_scored_object=key1_scored_object,
                key2_scored_object=key2_scored_object,
                winning_key=comparison.winner_id,
                other_comparison_pairs=[comparison.convert_to_comparison_pair() for comparison in other_comparisons],
                log=current_app.logger
            )

            for answer_id, score, result in [(answer1_id, score1, result_1), (answer2_id, score2, result_2)]:
                if score == None:
                    score = Score(
                        assignment_id=assignment_id,
                        answer_id=answer_id,
                        criterion_id=comparison.criterion_id
                    )
                    new_scores.append(score)
                score.score = result.score
                score.variable1 = result.variable1
                score.variable2 = result.variable2
                score.rounds = result.rounds
                score.wins = result.wins
                score.loses = result.loses
                score.opponents = result.opponents

        updated_scores = scores + new_scores
        db.session.add_all(updated_scores)
        db.session.commit()

    @classmethod
    def calculate_scores(cls, assignment_id):
        from . import Score, AssignmentCriterion, ScoringAlgorithm
        # get all comparisons for this assignment and only load the data we need
        comparisons = Comparison.query . \
            options(load_only('winner_id', 'criterion_id', 'answer1_id', 'answer2_id')) . \
            filter(Comparison.assignment_id == assignment_id) \
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
                package_name=ScoringAlgorithm.true_skill.value,
                comparison_pairs=comparison_pairs,
                log=current_app.logger
            )

        # load existing scores
        scores = Score.query.filter(Score.answer_id.in_(answer_ids)). \
            order_by(Score.answer_id, Score.criterion_id).all()

        updated_scores = update_scores(scores, assignment_id, criterion_comparison_results)
        db.session.add_all(updated_scores)
        db.session.commit()


def update_scores(scores, assignment_id, criterion_comparison_results):
    from . import Score

    new_scores = []
    for criterion_id, criterion_comparison_result in criterion_comparison_results.items():
        for answer_id, comparison_results in criterion_comparison_result.items():
            score = None
            for s in scores:
                if s.answer_id == answer_id and s.criterion_id == criterion_id:
                    score = s
            if not score:
                score = Score(
                    assignment_id=assignment_id,
                    answer_id=answer_id,
                    criterion_id=criterion_id
                )
                new_scores.append(score)

            score.score = comparison_results.score
            score.variable1 = comparison_results.variable1
            score.variable2 = comparison_results.variable2
            score.rounds = comparison_results.rounds
            score.wins = comparison_results.wins
            score.loses = comparison_results.loses
            score.opponents = comparison_results.opponents

    return scores + new_scores