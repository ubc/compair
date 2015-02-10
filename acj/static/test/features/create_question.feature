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


  Scenario: Creating a question as instructor
    Given I'm "instructor1"
    And I'm on "create question" page for course with id "1"
    And I fill in:
      | element        | content       |
      | question.title | Test Question |
    And I select the first criteria
    When I click on "Save" button
    Then I should be on "course" page
    And I should see "Test Question »" in "h3" on the page