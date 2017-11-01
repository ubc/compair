Feature: Create Course
  As user, I want to create courses

  Scenario: Loading add course page by Add Course button as admin
    Given I'm a System Administrator
    And I'm on 'home' page
    When I select the 'Add Course' button
    Then I should be on the 'create course' page

  Scenario: Loading add course page by add a course button as instructor
    Given I'm an Instructor
    And I'm on 'home' page
    When I select the 'Add Course' button
    Then I should be on the 'create course' page

  Scenario: Creating a course as instructor
    Given I'm an Instructor
    And I'm on 'create course' page
    When I fill form item 'course.name' in with 'Test Course 2'
    And I fill form item 'course.year' in with '2015'
    And I fill form item 'course.term' in with 'Winter'
    And I submit form with the 'Save' button
    Then I should be on the 'course' page
    And I should see 'Test Course 2\n(2015 Winter)' in 'h1' on the page