/*
For getting all of the comparisons in the question and the related answers' final scores
CHANGE questionId and output file name before using the script
*/

SET @questionId = 0;

SELECT summary.users_id, summary.criteriaandquestions_id as criterionId, c.name as criterion, summary.answer1_id as answer1, s.score as score1, summary.answer2_id as answer2, s2.score as score2, summary.winner_id as winner
FROM (
	SELECT ap.id, j.users_id, ap.answer1_id, ap.answer2_id, j.criteriaandquestions_id, j.winner_id
	FROM Judgements as j
	JOIN AnswerPairings as ap on ap.id = j.answerpairings_id
	WHERE j.criteriaandquestions_id IN (SELECT id FROM CriteriaAndQuestions WHERE questions_id = @questionId and active = 1)
) as summary
JOIN CriteriaAndQuestions as cq ON cq.id = summary.criteriaandquestions_id
JOIN Criteria as c ON c.id = cq.criteria_id
JOIN Scores as s
ON s.answer_id = summary.answer1_id and s.criteriaandquestions_id=summary.criteriaandquestions_id
JOIN Scores as s2
ON s2.answer_id = summary.answer2_id and s2.criteriaandquestions_id=summary.criteriaandquestions_id
ORDER BY summary.criteriaandquestions_id, summary.users_id
INTO OUTFILE '/tmp/test.csv'
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n';