Feature: Create User
  As user, I want to create users

  Scenario: Loading add user page by Create User button as admin
    Given I'm a System Administrator
    And I'm on "home" page
    When I select "Create User" button
    Then I should be on the "create user" page

  Scenario: Loading add user page by Create User button as instructor
    Given I'm an Instructor
    And I'm on "home" page
    When I select "Create User" button
    Then I should be on the "create user" page

  Scenario: Creating a user as instructor
    Given I'm an Instructor
    And I'm on "create user" page
    And I fill in:
      | element                     | content           |
      | user.system_role            | Student           |
      | user.username               | student2          |
      | user.verifyPassword         | password          |
      | user.password               | password          |
      | user.displayname            | Second Student    |
      | user.firstname              | Second            |
      | user.lastname               | Student           |
    When I submit form with "Save" button
    Then I should be on the "profile" page
    And I should see "Second Student's Profile" in "h1" on the page


