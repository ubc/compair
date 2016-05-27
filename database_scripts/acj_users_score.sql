/*
For getting a list of users and their scores for each criterion
Note: CHANGE questionId and output file name before using the script
*/

SET @questionId = 3;

SELECT p.users_id, cq.id, c.name, scores.score
FROM (
	SELECT s.score, s.answer_id, s.criteriaandquestions_id
	FROM Scores as s
	WHERE s.criteriaandquestions_id IN 
	(SELECT id FROM CriteriaAndQuestions
		WHERE questions_id = @questionId and active = 1)
) as scores
JOIN CriteriaAndQuestions as cq ON cq.id = scores.criteriaandquestions_id
JOIN Criteria as c ON c.id = cq.criteria_id
JOIN Answers AS a ON a.id = scores.answer_id
JOIN Posts AS p ON p.id = a.posts_id
ORDER BY cq.id ASC, p.users_id ASC
INTO OUTFILE '/tmp/test.csv'
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n';