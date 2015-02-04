Feature: Create Question
  As user, I want to create questions

  Scenario: Loading add question page by Add Question button as admin
    Given I'm "admin"
    And I'm on "course" page for course with id "1"
    When I select 'Add Question' button
    Then "Add Question" page should load

  Scenario: Loading add question page by Add Question button as admin
    Given I'm "instructor1"
    And I'm on "course" page for course with id "1"
    When I select 'Add Question' button
    Then "Add Question" page should load