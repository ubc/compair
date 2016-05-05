Feature: Edit Course
  As user, I want to edit a course

  Scenario: Loading edit course page as admin
    Given I'm a System Administrator with courses
    And I'm on "course" page for course with id "1"
    When I select "Edit Course" button
    Then I should be on the "edit course" page

  Scenario: Loading edit course page as admin
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
    And I fill in the course description with "This is the new description"
    And I drop the first criteria
    And I add my default criteria
    And I submit form with "Save" button
    Then I should be on the "course" page
    And I should see "New Name" in "h1" on the page
    And I should see "This is the new description" in "div.intro-text" on the page
    
  Scenario: Editing a course's criteria as instructor
    Given I'm an Instructor with courses
    And I'm on "edit course" page for course with id "1"
    When I edit the second criteria
    And I fill in:
      | element         | content               |
      | criterion.name  | Choose the best one   |
    And I fill in the criteria description with "Choose the best one."
    And I submit modal form with "Update" button
    And I add a new criteria
    And I fill in:
      | element         | content               |
      | criterion.name  | Which do you like?    |
    And I fill in the criteria description with "Choose the one you liek best."
    And I toggle the "Include this criterion in my list of default criteria (to use it in any course)" checkbox
    And I submit modal form with "Add New" button
    And I submit form with "Save" button
    Then I should be on the "course" page
  