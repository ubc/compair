Feature: Edit Profile
  As user, I want to edit profiles of users

  Scenario: Loading edit own profile as admin
    Given I'm a System Administrator
    And I'm on 'user' page for user with id '1'
    When I select 'Edit' button
    Then I should be on the 'edit profile' page
    And I should see the full Account Details and Account Login sections of the Edit User form for non-students
    And I should see the Password section of the Edit User form

  Scenario: Loading edit instructor's profile as admin
    Given I'm a System Administrator
    And I'm on 'user' page for user with id '2'
    When I select 'Edit' button
    Then I should be on the 'edit profile' page
    And I should see the full Account Details and Account Login sections of the Edit User form for non-students
    And I should see the Password section of the Edit User form without old password

  Scenario: Loading edit own profile as instructor
    Given I'm an Instructor
    And I'm on 'user' page for user with id '2'
    When I select 'Edit' button
    Then I should be on the 'edit profile' page
    And I should see the incomplete Account Details section of the Edit User form for non-students
    And I should see the Password section of the Edit User form

  Scenario: Edit own profile as instructor
    Given I'm an Instructor
    And I'm on 'edit user' page for user with id '2'
    When I fill form item 'user.displayname' in with 'instructor123'
    And I fill form item 'user.firstname' in with 'instructor'
    And I fill form item 'user.lastname' in with '123'
    And I fill form item 'user.email' in with 'instructor.123@example.com'
    And I submit form with 'Save' button
    Then I should be on the 'profile' page
    And I should see 'instructor123's Profile' in 'h1' on the page

  Scenario: Change own password as instructor
    Given I'm an Instructor
    And I'm on 'edit user' page for user with id '2'
    When I fill form item 'password.oldpassword' in with 'password'
    And I fill form item 'password.newpassword' in with 'password2'
    And I fill form item 'password.verifypassword' in with 'password2'
    And I submit form with 'Save' button
    Then I should be on the 'profile' page
    And I should see 'First Instructor's Profile' in 'h1' on the page

  Scenario: Loading edit another user's profile as instructor
    Given I'm an Instructor with students
    And I'm on 'user' page for user with id '3'
    When I select 'Edit' button
    Then I should be on the 'edit profile' page
    And I should see the incomplete Account Details section of the Edit User form for students
    And I should not see the Password section of the Edit User form

  Scenario: Edit another user's profile as instructor
    Given I'm an Instructor with students
    And I'm on 'edit user' page for user with id '3'
    When I fill form item 'user.displayname' in with 'student123'
    And I fill form item 'user.firstname' in with 'student'
    And I fill form item 'user.lastname' in with '123'
    And I fill form item 'user.student_number' in with '1234567890'
    And I fill form item 'user.email' in with 'student.123@example.com'
    And I submit form with 'Save' button
    Then I should be on the 'profile' page
    And I should see 'student123's Profile' in 'h1' on the page

  Scenario: Loading edit own profile as student
    Given I'm a Student
    And I'm on 'user' page for user with id '3'
    When I select 'Edit' button
    Then I should be on the 'edit profile' page
    And I should see the incomplete Account Details section of the Edit User form for non-students
    And I should see the Password section of the Edit User form

  Scenario: Edit own profile as student
    Given I'm a Student
    And I'm on 'edit user' page for user with id '3'
    When I fill form item 'user.displayname' in with 'student123'
    And I fill form item 'user.firstname' in with 'student'
    And I fill form item 'user.lastname' in with '123'
    And I fill form item 'user.student_number' in with '1234567890'
    And I fill form item 'user.email' in with 'student.123@example.com'
    And I submit form with 'Save' button
    Then I should be on the 'profile' page
    And I should see 'student123's Profile' in 'h1' on the page

  Scenario: Change own password as student
    Given I'm a Student
    And I'm on 'edit user' page for user with id '3'
    When I fill form item 'password.oldpassword' in with 'password'
    And I fill form item 'password.newpassword' in with 'password2'
    And I fill form item 'password.verifypassword' in with 'password2'
    And I submit form with 'Save' button
    Then I should be on the 'profile' page
    And I should see 'First Student's Profile' in 'h1' on the page