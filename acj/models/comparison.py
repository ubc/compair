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
        """ TODO: fix when merged with refactor score algorithm
        
        # get all judgements for this question and only load the data we need
        judgements = Judgements.query . \
            options(load_only('answers_id_winner', 'criteriaandquestions_id')) . \
            options(contains_eager(Judgements.answerpairing).load_only('answers_id1', 'answers_id2')) . \
            join(AnswerPairings). \
            filter(AnswerPairings.questions_id == question_id).all()
        answer_ids = set()  # stores answers that've been judged
        question_criteria = CriteriaAndPostsForQuestions.query. \
            with_entities(CriteriaAndPostsForQuestions.id) . \
            filter_by(questions_id=question_id, active=True).all()
        # 2D array, keep tracks of wins, e.g.: wins[A][B] is the number of times A won vs B
        wins = WinsTable([criterion.id for criterion in question_criteria])
        # keeps track of number of times judged for each answer
        rounds = {}
        for judgement in judgements:
            answers_id1 = judgement.answerpairing.answers_id1
            answers_id2 = judgement.answerpairing.answers_id2
            winner = judgement.answers_id_winner
            loser = answers_id2 if winner == answers_id1 else answers_id1
            wins.add(winner, loser, judgement.criteriaandquestions_id)
            # update number of times judged
            rounds[answers_id1] = rounds.get(answers_id1, 0) + 1
            rounds[answers_id2] = rounds.get(answers_id2, 0) + 1
            answer_ids.add(answers_id1)
            answer_ids.add(answers_id2)
        current_app.logger.debug("Wins table: " + str(wins))
        answer_ids = sorted(answer_ids)

        # load existing scores
        scores = Scores.query.filter(Scores.answers_id.in_(answer_ids)). \
            order_by(Scores.answers_id, Scores.criteriaandquestions_id).all()

        question_criteria_ids = [criterion.id for criterion in question_criteria]
        updated_scores = update_scores(scores, answer_ids, question_criteria_ids, wins, rounds)
        db.session.add_all(updated_scores)
        db.session.commit()
        """


""" TODO: fix when merged with refactor score algorithm
def update_scores(scores, answer_ids, question_criteria_ids, wins, rounds):
    # score_index = 0
    new_scores = []
    for answer_id in answer_ids:
        for question_criterion_id in question_criteria_ids:
            score = None
            for s in scores:
                if s.answers_id == answer_id and s.criteriaandquestions_id == question_criterion_id:
                    score = s
            if not score:
                score = Scores(answers_id=answer_id, criteriaandquestions_id=question_criterion_id)
                new_scores.append(score)

            # if (len(scores) == score_index or
            #     scores[score_index].answers_id > answer_id or
            #     scores[score_index].answers_id <= answer_id and
            #         scores[score_index].criteriaandquestions_id > question_criterion_id):
            #     # create a new one
            #     score = Scores(answers_id=answer_id, criteriaandquestions_id=question_criterion_id)
            #     new_scores.append(score)
            # elif (scores[score_index].answers_id == answer_id and
            #         scores[score_index].criteriaandquestions_id == question_criterion_id):
            #     # existing score
            #     score = scores[score_index]
            #     score_index += 1
            # else:
            #     current_app.logger.error(
            #         'Wrong answer_id {} and criterion_id {}'.format(answer_id, question_criterion_id))
            score.rounds = rounds.get(answer_id, 0)
            score.score = wins.get_score(answer_id, question_criterion_id)
            score.wins = wins.get_total_wins(answer_id, question_criterion_id)

    # if score_index != len(scores):
    #     current_app.logger.error(
    #         'Inconsistent scores. Got {} scores in database but updated {}!'.format(len(scores), score_index))

    return scores + new_scores
"""