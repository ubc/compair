# sqlalchemy
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import synonym, load_only, backref, contains_eager, joinedload, Load
from sqlalchemy import func, select, and_, or_
from sqlalchemy.ext.hybrid import hybrid_property
from flask import current_app

import random

from . import *
from importlib import import_module

from acj.core import db
from acj.algorithms import ScoredObject, ComparisonPair
from acj.algorithms.pair import generate_pair
from acj.algorithms.score import calculate_score


class Comparison(DefaultTableMixin, WriteTrackingMixin):
    # table columns
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignment.id', ondelete="CASCADE"),
        nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete="CASCADE"),
        nullable=False)
    criteria_id = db.Column(db.Integer, db.ForeignKey('criteria.id', ondelete="CASCADE"),
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
    # criteria via Criteria Model

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

    @classmethod
    def create_new_comparison_set(cls, assignment_id, user_id):
        from . import Assignment, UserCourse, CourseRole, Answer, Score

        assignment = Assignment.query.get(assignment_id)

        # choose one of the assignments criteria randomly
        assignment_criteria = random.choice(assignment.assignment_criteria)
        criteria_id = assignment_criteria.criteria_id

        # ineligible authors - eg. instructors, TAs, dropped student, current user

        non_students = UserCourse.query \
            .filter(and_(
                UserCourse.course_id == assignment.course_id,
                UserCourse.course_role != CourseRole.student
            ))
        ineligible_user_ids = [non_student.user_id \
            for non_student in non_students]
        ineligible_user_ids.append(user_id)

        # TODO: try score vs excepted score
        answers_with_score = Answer.query \
            .with_entities(Answer, Score.score) \
            .outerjoin(Score) \
            .filter(and_(
                Answer.user_id.notin_(ineligible_user_ids),
                Answer.assignment_id == assignment_id,
                Answer.active == True,
                or_(
                    Score.criteria_id == criteria_id,
                    Score.criteria_id == None
                )
            )) \
            .all()

        scored_objects = []
        for answer_with_score in answers_with_score:
            scored_objects.append(ScoredObject(
                key=answer_with_score.Answer.id,
                score=answer_with_score.score,
                round=answer_with_score.Answer.round
            ))

        comparisons = Comparison.query \
            .filter_by(
                user_id=user_id,
                assignment_id=assignment_id,
                criteria_id=criteria_id
            )

        comparison_pairs = []
        for comparison in comparisons:
            comparison_pairs.append(ComparisonPair(
                comparison.answer1_id,
                comparison.answer2_id,
                winning_key=comparison.winner_id
            ))

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
        for assignment_criteria in assignment.assignment_criteria:
            criteria_id = assignment_criteria.criteria_id

            comparison = Comparison(
                assignment_id=assignment_id,
                user_id=user_id,
                criteria_id=criteria_id,
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
    def calculate_scores(cls, assignment_id):
        from . import Score, AssignmentCriteria
        # get all comparisons for this assignment and only load the data we need
        comparisons = Comparison.query . \
            options(load_only('winner_id', 'criteria_id', 'answer1_id', 'answer2_id')) . \
            filter(Comparison.assignment_id == assignment_id).all()

        assignment_criteria = AssignmentCriteria.query. \
            with_entities(AssignmentCriteria.criteria_id) . \
            filter_by(assignment_id=assignment_id, active=True).all()

        criteria_comparison_results = {}
        answer_ids = set()
        for assignment_criterion in assignment_criteria:
            comparison_pairs = []
            for comparison in comparisons:
                if comparison.criteria_id != assignment_criterion.criteria_id:
                    continue
                answer1_id = comparison.answer1_id
                answer2_id = comparison.answer2_id
                answer_ids.add(answer1_id)
                answer_ids.add(answer2_id)
                winner = comparison.winner_id
                comparison_pairs.append(ComparisonPair(
                        answer1_id, answer2_id, winning_key=winner
                ))

            criteria_comparison_results[assignment_criterion.criteria_id] = calculate_score(
                package_name="comparative_judgement",
                comparison_pairs=comparison_pairs,
                log=current_app.logger
            )

        # load existing scores
        scores = Score.query.filter(Score.answer_id.in_(answer_ids)). \
            order_by(Score.answer_id, Score.criteria_id).all()

        updated_scores = update_scores(scores, criteria_comparison_results)
        db.session.add_all(updated_scores)
        db.session.commit()


def update_scores(scores, criteria_comparison_results):
    from . import Score

    new_scores = []
    for criteria_id, criteria_comparison_result in criteria_comparison_results.items():
        for answer_id, comparison_results in criteria_comparison_result.items():
            score = None
            for s in scores:
                if s.answer_id == answer_id and s.criteria_id == criteria_id:
                    score = s
            if not score:
                score = Score(answer_id=answer_id, criteria_id=criteria_id)
                new_scores.append(score)

            score.excepted_score = comparison_results.score
            score.rounds = comparison_results.total_rounds
            score.wins = comparison_results.total_wins
            score.opponents = comparison_results.total_opponents

            # a good average score value is excepted score / number of opponents
            score.score = score.excepted_score / score.opponents

    return scores + new_scores
