/*
For getting all of the comparisons in the question and the related answers' final scores
CHANGE questionId and output file name before using the script
*/

SET @questionId = 0;

SELECT summary.users_id, summary.criteriaandquestions_id as criterionId, c.name as criterion, summary.answers_id1 as answer1, s.score as score1, summary.answers_id2 as answer2, s2.score as score2, summary.answers_id_winner as winner
FROM (
	SELECT ap.id, j.users_id, ap.answers_id1, ap.answers_id2, j.criteriaandquestions_id, j.answers_id_winner
	FROM Judgements as j
	JOIN AnswerPairings as ap on ap.id = j.answerpairings_id
	WHERE j.criteriaandquestions_id IN (SELECT id FROM CriteriaAndQuestions WHERE questions_id = @questionId and active = 1)
) as summary
JOIN CriteriaAndQuestions as cq ON cq.id = summary.criteriaandquestions_id
JOIN Criteria as c ON c.id = cq.criteria_id
JOIN Scores as s
ON s.answers_id = summary.answers_id1 and s.criteriaandquestions_id=summary.criteriaandquestions_id
JOIN Scores as s2
ON s2.answers_id = summary.answers_id2 and s2.criteriaandquestions_id=summary.criteriaandquestions_id
ORDER BY summary.criteriaandquestions_id, summary.users_id
INTO OUTFILE '/tmp/test.csv'
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n';