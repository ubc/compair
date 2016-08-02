Feature: Edit Course
  As user, I want to edit a course

  Scenario: Loading edit course page as admin
    Given I'm a System Administrator with courses
    And I'm on "course" page for course with id "1"
    When I select "Edit Course" button
    Then I should be on the "edit course" page

  Scenario: Loading edit course page as instructor
    Given I'm an Instructor with courses
    And I'm on "course" page for course with id "1"
    When I select "Edit Course" button
    Then I should be on the "edit course" page

  Scenario: Editing a course as instructor
    Given I'm an Instructor with courses
    And I'm on "edit course" page for course with id "1"
    When I fill in:
      | element     | content   |
      | course.name | New Name  |
      | course.year | 2020      |
      | course.term | Winter    |
    And I fill in the course description with "This is the new description"
    And I submit form with "Save" button
    Then I should be on the "course" page
    And I should see "New Name (2020 Winter)" in "h1" on the page
    And I should see "This is the new description" in "div.intro-text" on the page
