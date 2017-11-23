Feature: Create Assignment
  As user, I want to create assignments

  Scenario: Loading add assignment page by Add Assignment button as admin
    Given I'm a System Administrator
    And I'm on 'course' page for course with id '2abcABC123-abcABC123_Z'
    When I select the 'Add Assignment' button
    Then I should be on the 'create assignment' page

  Scenario: Loading add assignment page by Add Assignment button as instructor
    Given I'm an Instructor
    And I'm on 'course' page for course with id '2abcABC123-abcABC123_Z'
    When I select the 'Add Assignment' button
    Then I should be on the 'create assignment' page

  Scenario: Creating a assignment as instructor
    Given I'm an Instructor
    And I'm on 'create assignment' page for course with id '2abcABC123-abcABC123_Z'
    When I fill form item 'assignment.name' in with 'Test Assignment'
    And I submit form with the 'Save' button
    Then I should be on the 'course' page
    And I should see 'Test Assignment »' in 'h3' on the page
