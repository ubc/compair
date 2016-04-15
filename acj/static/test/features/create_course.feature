Feature: Create Course
  As user, I want to create courses

  Scenario: Loading add course page by Add Course button as admin
    Given I'm "admin"
    And I'm on "home" page
    When I select "Add Course" button
    Then "Add Course" page should load

  Scenario: Loading add course page by add a course button as instructor
    Given I'm "instructor1"
    And I'm on "home" page
    When I select "Add Course" button
    Then "Add Course" page should load

  Scenario: Creating a course as instructor
    Given I'm "instructor1"
    And I'm on "create course" page
    And I fill in:
      | element     | content     |
      | course.name | Test Course |
    When I submit form with "Save" button
    Then I should be on the "course" page
    And I should see "Test Course" in "h1" on the page