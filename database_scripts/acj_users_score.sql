/*
For getting a list of users and their scores for each criterion
Note: CHANGE assignmentId and output file name before using the script
*/

SET @assignmentId = 3;

SELECT p.user_id, cq.id, c.name, scores.score
FROM (
	SELECT s.score, s.answer_id, s.criterion_id
	FROM Scores as s
	WHERE s.criterion_id IN
	(SELECT id FROM assignment_criterion
		WHERE assignment_id = @assignmentId and active = 1)
) as scores
JOIN assignment_criterion as ac ON ac.id = scores.criterion_id
JOIN criterion as c ON c.id = cq.criterion_id
JOIN answer AS a ON a.id = scores.answer_id
WHERE NOT a.draft
ORDER BY ac.id ASC, a.user_id ASC
INTO OUTFILE '/tmp/test.csv'
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n';