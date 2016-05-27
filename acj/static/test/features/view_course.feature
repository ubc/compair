Feature: View Course
  As user, I want to view a course

  Scenario: Loading course page as admin
    Given I'm a System Administrator with questions
    And I'm on "home" page
    When I select the course named "CHEM 111"
    Then I should be on the "course" page
    And I should see "4" questions
    And I should see my questions with names:
      | name                    |
      | Question Finished       |
      | Question Being Judged   |
      | Question Being Answered |
      | Question Upcoming       |

  Scenario: Loading course page as instructor
    Given I'm an Instructor with questions
    And I'm on "home" page
    When I select the course named "CHEM 111"
    Then I should be on the "course" page
    And I should see "4" questions
    And I should see my questions with names:
      | name                    |
      | Question Finished       |
      | Question Being Judged   |
      | Question Being Answered |
      | Question Upcoming       |

  Scenario: Filtering questions on course page as instructor
    Given I'm an Instructor with questions
    And I'm on "course" page for course with id "1"
    When I filter course page questions by "Assignments being answered"
    Then I should see "1" questions
    And I should see my questions with names:
      | name                    |
      | Question Being Answered |

  Scenario: Filtering questions on course page as instructor
    Given I'm an Instructor with questions
    And I'm on "course" page for course with id "1"
    When I filter course page questions by "Assignments being compared"
    Then I should see "1" questions
    And I should see my questions with names:
      | name                    |
      | Question Being Judged   |

  Scenario: Filtering questions on course page as instructor
    Given I'm an Instructor with questions
    And I'm on "course" page for course with id "1"
    When I filter course page questions by "Upcoming assignments"
    Then I should see "1" questions
    And I should see my questions with names:
      | name                    |
      | Question Upcoming       |


  Scenario: Loading course page as student
    Given I'm a Student with questions
    And I'm on "home" page
    When I select the course named "CHEM 111"
    Then I should be on the "course" page
    And I should see "3" questions
    And I should see my questions with names:
      | name                    |
      | Question Finished       |
      | Question Being Judged   |
      | Question Being Answered |

  Scenario: Filtering questions on course page as student
    Given I'm a Student with questions
    And I'm on "course" page for course with id "1"
    When I filter course page questions by "My pending assignments"
    Then I should see "1" questions
    And I should see my questions with names:
      | name                    |
      | Question Being Answered |

