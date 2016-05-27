/*
For getting all of the comparisons in the assignment and the related answers' final scores
CHANGE assignmentId and output file name before using the script
*/

SET @assignmentId = 0;

SELECT summary.user_id, summary.criteria_id as criterionId, c.name as criterion, summary.answer1_id as answer1, s.score as score1, summary.answer2_id as answer2, s2.score as score2, summary.winner_id as winner
FROM (
	SELECT c.id, c.user_id, c.answer1_id, c.answer2_id, c.criteria_id, c.winner_id
	FROM Comparison as c
	WHERE c.criteria_id IN (SELECT id FROM AssignmentCriteria WHERE assignment_id = @assignmentId and active = 1)
) as summary
JOIN Criteria as c ON c.id = summary.criteria_id
JOIN Scores as s
ON s.answer_id = summary.answer1_id and s.criteria_id=summary.criteria_id
JOIN Scores as s2
ON s2.answer_id = summary.answer2_id and s2.criteria_id=summary.criteria_id
ORDER BY summary.criteria_id, summary.user_id
INTO OUTFILE '/tmp/test.csv'
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n';