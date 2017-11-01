Feature: Edit Course
  As user, I want to edit a course

  Scenario: Loading edit course page as admin
    Given I'm a System Administrator
    And I'm on 'course' page for course with id '1abcABC123-abcABC123_Z'
    When I select the 'Edit Course' button
    Then I should be on the 'edit course' page

  Scenario: Loading edit course page as instructor
    Given I'm an Instructor
    And I'm on 'course' page for course with id '1abcABC123-abcABC123_Z'
    When I select the 'Edit Course' button
    Then I should be on the 'edit course' page

  Scenario: Editing a course as instructor
    Given I'm an Instructor
    And I'm on 'edit course' page for course with id '1abcABC123-abcABC123_Z'
    When I fill form item 'course.name' in with 'New Name'
    And I fill form item 'course.year' in with '2020'
    And I fill form item 'course.term' in with 'Winter'
    And I submit form with the 'Save' button
    Then I should be on the 'course' page
    And I should see 'New Name\n(2020 Winter)' in 'h1' on the page
