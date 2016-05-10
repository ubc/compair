# sqlalchemy
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import synonym, load_only, column_property, backref, contains_eager, joinedload, Load
from sqlalchemy import func, select, and_, or_
from sqlalchemy.ext.hybrid import hybrid_property

from . import *

from acj.core import db

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
        nullable=False)
    round_compared = db.Column(db.Integer, default=0, nullable=False)
    content = db.Column(db.Text)
    
    # relationships
    # assignment via Assignment Model
    # user via User Model
    # criteria via Criteria Model
    
    answer1 = db.relationship("Answer", foreign_keys=[answer1_id])
    answer2 = db.relationship("Answer", foreign_keys=[answer2_id])
    winning_answer = db.relationship("Answer", foreign_keys=[winner_id])
    
    # hyprid and other functions
    course_id = association_proxy('assignment', 'course_id')
    user_avatar = association_proxy('user', 'avatar')
    user_displayname = association_proxy('user', 'displayname')
    user_fullname = association_proxy('user', 'fullname')
    user_system_role = association_proxy('user', 'system_role')
    
    @classmethod
    def create_new_comparison_set(cls, assignment_id, user_id, answer1_id, answer2_id, round_compared):
        assignment = db.session.query(Assignment).get(assignment_id)
        
        comparisons = []
        for criteria in assignment.criteria:
            comparison = Comparison(
                assignment_id=assignment_id,
                user_id=user_id,
                criteria_id=criteria.id,
                answer1_id=answer1_id,
                answer2_id=answer2_id,
                winner_id=None,
                round_compared=round_compared,
                content=None
            )
            db.session.add(comparison)
            db.session.commit()
            comparisons.append(comparison)
        answer_ids = [answer1_id, answer2_id]
        answers = Answer.query.filter(Answer.id.in_(answer_ids)).all()
        for answer in answers:
            # update round counts via sqlalchemy increase counter
            answer.round = Answer.round + 1
            db.session.add(answer)
        db.session.commit()
         
        return comparisons

    @classmethod
    def calculate_scores(cls, assignment_id):
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
                comparison_pairs.append(
                    ComparisonPair(answer1_id, answer2_id, winning_key=winner)
                )
            
            criteria_comparison_results[assignment_criteria.criteria_id] = acj.algorithms. \
                calculate_scores(comparison_pairs, "acj", current_app.logger)
            
        # load existing scores
        scores = Score.query.filter(Score.answer_id.in_(answer_ids)). \
            order_by(Score.answer_id, Score.criteria_id).all()

        updated_scores = update_scores(scores, criteria_comparison_results)
        db.session.add_all(updated_scores)
        db.session.commit()


def update_scores(scores, criteria_comparison_results):
    new_scores = []
    for criterion_id, criteria_comparison_result in criteria_comparison_results.items():
        for answer_id, comparison_results in criteria_comparison_result.items():
            score = None
            for s in scores:
                if s.answer_id == answer_id and s.criterion_id == criterion_id:
                    score = s
            if not score:
                score = Scores(answer_id=answer_id, criterion_id=criterion_id)
                new_scores.append(score)
            
            score.excepted_score = comparison_results.score
            score.rounds = comparison_results.total_rounds
            score.wins = comparison_results.total_wins
            score.opponents = comparison_results.total_opponents
            
            # a good average score value is excepted score / number of opponents
            score.score = score.excepted_score / score.opponents
    
    return scores + new_scores
