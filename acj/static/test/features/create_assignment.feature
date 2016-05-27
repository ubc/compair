Feature: Create Assignment
  As user, I want to create assignments

  Scenario: Loading add assignment page by Add Assignment button as admin
    Given I'm a System Administrator with courses
    And I'm on "course" page for course with id "1"
    When I select "Add Assignment" button
    Then "Add Assignment" page should load

  Scenario: Loading add assignment page by Add Assignment button as instructor
    Given I'm an Instructor with courses
    And I'm on "course" page for course with id "1"
    When I select "Add Assignment" button
    Then "Add Assignment" page should load

  Scenario: Creating a assignment as instructor
    Given I'm an Instructor with courses
    And I'm on "create assignment" page for course with id "1"
    When I fill in:
      | element          | content         |
      | assignment.name  | Test Assignment |
    And I submit form with "Save" button
    Then I should be on the "course" page
    And I should see "Test Assignment »" in "h3" on the page
