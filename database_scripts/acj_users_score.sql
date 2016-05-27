/*
For getting a list of users and their scores for each criterion
Note: CHANGE assignmentId and output file name before using the script
*/

SET @assignmentId = 3;

SELECT p.user_id, cq.id, c.name, scores.score
FROM (
	SELECT s.score, s.answer_id, s.criteria_id
	FROM Scores as s
	WHERE s.criteria_id IN
	(SELECT id FROM AssignmentCriteria
		WHERE assignment_id = @assignmentId and active = 1)
) as scores
JOIN AssignmentCriteria as ac ON ac.id = scores.criteria_id
JOIN Criteria as c ON c.id = cq.criteria_id
JOIN Answer AS a ON a.id = scores.answer_id
ORDER BY ac.id ASC, a.user_id ASC
INTO OUTFILE '/tmp/test.csv'
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n';