Feature: Create Account
  As user, I want to create accounts

  Scenario: Loading create user page by Create Account button as admin
    Given I'm a System Administrator
    And I'm on 'home' page
    When I select the 'Create Account' button
    Then I should be on the 'create user' page

  Scenario: Creating a instructor as admin
    Given I'm a System Administrator
    And I'm on 'create user' page
    When I fill form item 'user.system_role' in with 'Instructor'
    And I fill form item 'user.username' in with 'instructor2'
    And I fill form item 'user.verifyPassword' in with 'password'
    And I fill form item 'user.password' in with 'password'
    And I fill form item 'user.displayname' in with 'Second Instructor'
    And I fill form item 'user.firstname' in with 'Second'
    And I fill form item 'user.lastname' in with 'Instructor'
    And I submit form with the 'Save' button
    Then I should be on the 'profile' page
    And I should see 'Second Instructor's Profile' in 'h1' on the page

  Scenario: Creating a student as admin
    Given I'm a System Administrator
    And I'm on 'create user' page
    When I fill form item 'user.system_role' in with 'Student'
    And I fill form item 'user.username' in with 'student2'
    And I fill form item 'user.verifyPassword' in with 'password'
    And I fill form item 'user.password' in with 'password'
    And I fill form item 'user.displayname' in with 'Second Student'
    And I fill form item 'user.firstname' in with 'Second'
    And I fill form item 'user.lastname' in with 'Student'
    And I submit form with the 'Save' button
    Then I should be on the 'profile' page
    And I should see 'Second Student's Profile' in 'h1' on the page


