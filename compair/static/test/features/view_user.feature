Feature: View Profile
  As user, I want to view profiles of users

  Scenario: Loading own profile as admin
    Given I'm a System Administrator
    And I'm on 'home' page
    When I select the 'Profile' button
    Then I should be on the 'profile' page
    And I should see root's profile
    And I should see the edit notification settings option
    And I should see the edit profile button

  Scenario: Toggling user notification settings option
    Given I'm a System Administrator
    And I'm on 'user' page for user with id '1abcABC123-abcABC123_Z'
    When I toggle the user notification settings option
    Then I should see the notification settings set to off

  Scenario: Loading other user's profile as admin
    Given I'm a System Administrator
    And I'm on 'user' page for user with id '2abcABC123-abcABC123_Z'
    Then I should see First Instructor's profile
    And I should see the edit notification settings option
    And I should see the edit profile button

  Scenario: Loading own profile as instructor
    Given I'm an Instructor
    And I'm on 'home' page
    When I select the 'Profile' button
    Then I should be on the 'profile' page
    And I should see First Instructor's profile
    And I should see the edit notification settings option
    And I should see the edit profile button

  Scenario: Loading other user's profile as instructor with edit permissions
    Given I'm an Instructor
    And I'm on 'user' page for user with id '3abcABC123-abcABC123_Z'
    Then I should see instructor view of First Student's profile
    And I should not see the edit notification settings option
    And I should see the edit profile button

  Scenario: Loading own profile as CAS instructor
    Given I'm a CAS Instructor
    And I'm on 'home' page
    When I select the 'Profile' button
    Then I should be on the 'profile' page
    And I should see First Instructor's CAS profile
    And I should see the edit notification settings option
    And I should see the edit profile button

  Scenario: Loading other user's profile as CAS instructor with edit permissions
    Given I'm a CAS Instructor
    And I'm on 'user' page for user with id '3abcABC123-abcABC123_Z'
    Then I should see instructor view of First Student's CAS profile
    And I should not see the edit notification settings option
    And I should see the edit profile button

  Scenario: Loading own profile as student
    Given I'm a Student
    And I'm on 'home' page
    When I select the 'Profile' button
    Then I should be on the 'profile' page
    And I should see First Student's profile
    And I should see the edit notification settings option
    And I should see the edit profile button

  Scenario: Loading other user's profile as student
    Given I'm a Student
    And I'm on 'user' page for user with id '2abcABC123-abcABC123_Z'
    Then I should see the student view of First Instructor's profile
    And I should not see the edit notification settings option
    And I should not see the edit profile button

  Scenario: Loading own profile as CAS student
    Given I'm a CAS Student
    And I'm on 'home' page
    When I select the 'Profile' button
    Then I should be on the 'profile' page
    And I should see First Student's CAS profile
    And I should see the edit notification settings option
    And I should see the edit profile button