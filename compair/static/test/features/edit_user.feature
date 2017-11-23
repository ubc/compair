Feature: Edit Profile
  As user, I want to edit profiles of users

  Scenario: Loading edit own profile as admin
    Given I'm a System Administrator
    And I'm on 'user' page for user with id '1abcABC123-abcABC123_Z'
    When I select the 'Edit' button
    Then I should be on the 'edit profile' page
    And I should not see the student number in the Account Details section
    And I should see the system role in the Account Details section
    And I should see email fields in the Account Details section
    And I should see the rest of the Account Details section fields
    And I should see the Account Login section
    And I should see the 'Edit Password' button

  Scenario: Loading edit instructor's profile as admin
    Given I'm a System Administrator
    And I'm on 'user' page for user with id '2abcABC123-abcABC123_Z'
    When I select the 'Edit' button
    Then I should be on the 'edit profile' page
    And I should not see the student number in the Account Details section
    And I should see the system role in the Account Details section
    And I should see email fields in the Account Details section
    And I should see the rest of the Account Details section fields
    And I should see the Account Login section
    And I should see the 'Edit Password' button

  Scenario: Loading edit own profile as instructor
    Given I'm an Instructor
    And I'm on 'user' page for user with id '2abcABC123-abcABC123_Z'
    When I select the 'Edit' button
    Then I should be on the 'edit profile' page
    And I should not see the student number in the Account Details section
    And I should not see the system role in the Account Details section
    And I should see email fields in the Account Details section
    And I should see the rest of the Account Details section fields
    And I should see the Account Login section
    And I should see the 'Edit Password' button

  Scenario: Edit own profile as instructor
    Given I'm an Instructor
    And I'm on 'edit user' page for user with id '2abcABC123-abcABC123_Z'
    When I fill form item 'user.displayname' in with 'instructor123'
    And I fill form item 'user.firstname' in with 'instructor'
    And I fill form item 'user.lastname' in with '123'
    And I fill form item 'user.email' in with 'instructor.123@example.com'
    And I fill form item 'user.username' in with 'instructor123'
    And I submit form with the first 'Save' button
    Then I should be on the 'profile' page
    And I should see 'instructor123's Profile' in 'h1' on the page

  Scenario: Change own password as instructor
    Given I'm an Instructor
    And I'm on 'edit user' page for user with id '2abcABC123-abcABC123_Z'
    When I select the 'Edit Password' button
    And I fill form item 'password.oldpassword' in with 'password'
    And I fill form item 'password.newpassword' in with 'password2'
    And I fill form item 'password.verifypassword' in with 'password2'
    And I submit modal form with the 'Save' button
    Then I should see a success message

  Scenario: Loading edit another user's profile as instructor
    Given I'm an Instructor
    And I'm on 'user' page for user with id '3abcABC123-abcABC123_Z'
    When I select the 'Edit' button
    Then I should be on the 'edit profile' page
    And I should see the student number in the Account Details section
    And I should not see the system role in the Account Details section
    And I should not see email fields in the Account Details section
    And I should see the rest of the Account Details section fields
    And I should see the Account Login section
    And I should not see the 'Edit Password' button

  Scenario: Edit another user's profile as instructor
    Given I'm an Instructor
    And I'm on 'edit user' page for user with id '3abcABC123-abcABC123_Z'
    When I fill form item 'user.displayname' in with 'student123'
    And I fill form item 'user.firstname' in with 'student'
    And I fill form item 'user.lastname' in with '123'
    And I fill form item 'user.student_number' in with '1234567890'
    And I fill form item 'user.username' in with 'student123'
    And I submit form with the first 'Save' button
    Then I should be on the 'profile' page
    And I should see 'student123's Profile' in 'h1' on the page

  Scenario: Loading edit own profile as student
    Given I'm a Student
    And I'm on 'user' page for user with id '3abcABC123-abcABC123_Z'
    When I select the 'Edit' button
    Then I should be on the 'edit profile' page
    And I should see the student number in the Account Details section
    And I should not see the system role in the Account Details section
    And I should see email fields in the Account Details section
    And I should see the rest of the Account Details section fields
    And I should see the Account Login section
    And I should see the 'Edit Password' button

  Scenario: Edit own profile as student
    Given I'm a Student
    And I'm on 'edit user' page for user with id '3abcABC123-abcABC123_Z'
    When I fill form item 'user.displayname' in with 'student123'
    And I fill form item 'user.firstname' in with 'student'
    And I fill form item 'user.lastname' in with '123'
    And I fill form item 'user.student_number' in with '1234567890'
    And I fill form item 'user.email' in with 'student.123@example.com'
    And I fill form item 'user.username' in with 'student123'
    And I submit form with the first 'Save' button
    Then I should be on the 'profile' page
    And I should see 'student123's Profile' in 'h1' on the page

  Scenario: Change own password as student
    Given I'm a Student
    And I'm on 'edit user' page for user with id '3abcABC123-abcABC123_Z'
    When I select the 'Edit Password' button
    And I fill form item 'password.oldpassword' in with 'password'
    And I fill form item 'password.newpassword' in with 'password2'
    And I fill form item 'password.verifypassword' in with 'password2'
    And I submit modal form with the 'Save' button
    Then I should see a success message

  Scenario: Loading edit own profile as CAS instructor
    Given I'm a CAS Instructor
    And I'm on 'user' page for user with id '2abcABC123-abcABC123_Z'
    When I select the 'Edit' button
    Then I should be on the 'edit profile' page
    And I should not see the student number in the Account Details section
    And I should not see the system role in the Account Details section
    And I should see email fields in the Account Details section
    And I should see the rest of the Account Details section fields
    And I should not see the Account Login section
    And I should not see the 'Edit Password' button

  Scenario: Edit own profile as CAS instructor
    Given I'm a CAS Instructor
    And I'm on 'edit user' page for user with id '2abcABC123-abcABC123_Z'
    When I fill form item 'user.displayname' in with 'instructor123'
    And I fill form item 'user.firstname' in with 'instructor'
    And I fill form item 'user.lastname' in with '123'
    And I fill form item 'user.email' in with 'instructor.123@example.com'
    And I submit form with the first 'Save' button
    Then I should be on the 'profile' page
    And I should see 'instructor123's Profile' in 'h1' on the page

  Scenario: Loading edit another user's profile as CAS instructor
    Given I'm a CAS Instructor
    And I'm on 'user' page for user with id '3abcABC123-abcABC123_Z'
    When I select the 'Edit' button
    Then I should be on the 'edit profile' page
    And I should see the student number in the Account Details section
    And I should not see the system role in the Account Details section
    And I should not see email fields in the Account Details section
    And I should see the rest of the Account Details section fields
    And I should not see the Account Login section
    And I should not see the 'Edit Password' button

  Scenario: Edit another user's profile as CAS instructor
    Given I'm a CAS Instructor
    And I'm on 'edit user' page for user with id '3abcABC123-abcABC123_Z'
    When I fill form item 'user.displayname' in with 'student123'
    And I fill form item 'user.firstname' in with 'student'
    And I fill form item 'user.lastname' in with '123'
    And I fill form item 'user.student_number' in with '1234567890'
    And I submit form with the first 'Save' button
    Then I should be on the 'profile' page
    And I should see 'student123's Profile' in 'h1' on the page

  Scenario: Loading edit another user's profile as CAS admin
    Given I'm a CAS System Administrator
    And I'm on 'user' page for user with id '3abcABC123-abcABC123_Z'
    When I select the 'Edit' button
    Then I should be on the 'edit profile' page
    And I should see the student number in the Account Details section
    And I should see the system role in the Account Details section
    And I should see email fields in the Account Details section
    And I should see the rest of the Account Details section fields
    And I should see the Account Login section
    And I should not see the 'Edit Password' button

  Scenario: Edit another user's profile as CAS admin
    Given I'm a CAS System Administrator
    And I'm on 'edit user' page for user with id '3abcABC123-abcABC123_Z'
    When I fill form item 'user.displayname' in with 'student123'
    And I fill form item 'user.firstname' in with 'student'
    And I fill form item 'user.lastname' in with '123'
    And I fill form item 'user.student_number' in with '1234567890'
    And I fill form item 'user.email' in with 'student.123@example.com'
    And I fill form item 'user.username' in with 'student123'
    And I submit form with the first 'Save' button
    Then I should be on the 'profile' page
    And I should see 'student123's Profile' in 'h1' on the page