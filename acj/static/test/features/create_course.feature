Feature: Create Course
  As user, I want to create courses

  Scenario: Loading add course page by Add Course button as admin
    Given I'm a System Administrator
    And I'm on "home" page
    When I select "Add Course" button
    Then "Add Course" page should load

  Scenario: Loading add course page by add a course button as instructor
    Given I'm an Instructor
    And I'm on "home" page
    When I select "Add Course" button
    Then "Add Course" page should load

  Scenario: Creating a course as instructor
    Given I'm an Instructor
    And I'm on "create course" page
    When I toggle the "Add a course description (optional)" checkbox
    And I fill in:
      | element     | content       |
      | course.name | Test Course 2 |
      | course.year | 2015          |
      | course.term | Winter        |
    And I fill in the course description with "This is the description for Test Course 2"
    And I submit form with "Save" button
    Then I should be on the "course" page
    And I should see "Test Course 2 (2015 Winter)" in "h1" on the page
    And I should see "This is the description for Test Course 2" in "div.intro-text" on the page