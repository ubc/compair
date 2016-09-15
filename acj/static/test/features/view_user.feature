Feature: View Profile
  As user, I want to view profiles of users

  Scenario: Loading own profile as admin
    Given I'm a System Administrator
    And I'm on 'home' page
    When I select 'Profile' button
    Then I should be on the 'profile' page
    And I should see root's profile
    And I should see the edit profile button

  Scenario: Loading other user's profile as admin
    Given I'm a System Administrator
    And I'm on 'user' page for user with id '2abcABC123-abcABC123_Z'
    Then I should see First Instructor's profile
    And I should see the edit profile button

  Scenario: Loading own profile as instructor
    Given I'm an Instructor
    And I'm on 'home' page
    When I select 'Profile' button
    Then I should be on the 'profile' page
    And I should see First Instructor's profile
    And I should see the edit profile button

  Scenario: Loading other user's profile as instructor with edit permissions
    Given I'm an Instructor with students
    And I'm on 'user' page for user with id '3abcABC123-abcABC123_Z'
    Then I should see First Student's profile
    And I should see the edit profile button

  Scenario: Loading other user's profile as instructor without edit permissions
    Given I'm an Instructor with students
    And I'm on 'user' page for user with id '4abcABC123-abcABC123_Z'
    And I should not see the edit profile button

  Scenario: Loading own profile as CWL instructor
    Given I'm a CWL Instructor with students
    And I'm on 'home' page
    When I select 'Profile' button
    Then I should be on the 'profile' page
    And I should see First Instructor's CWL profile
    And I should see the edit profile button

  Scenario: Loading other user's profile as CWL instructor with edit permissions
    Given I'm a CWL Instructor with students
    And I'm on 'user' page for user with id '3abcABC123-abcABC123_Z'
    Then I should see First Student's CWL profile
    And I should see the edit profile button

  Scenario: Loading own profile as student
    Given I'm a Student
    And I'm on 'home' page
    When I select 'Profile' button
    Then I should be on the 'profile' page
    And I should see First Student's profile
    And I should see the edit profile button

  Scenario: Loading other user's profile as student
    Given I'm a Student
    And I'm on 'user' page for user with id '2abcABC123-abcABC123_Z'
    Then I should see the student view of First Instructor's profile
    And I should not see the edit profile button

  Scenario: Loading own profile as CWL student
    Given I'm a CWL Student
    And I'm on 'home' page
    When I select 'Profile' button
    Then I should be on the 'profile' page
    And I should see First Student's CWL profile
    And I should see the edit profile button