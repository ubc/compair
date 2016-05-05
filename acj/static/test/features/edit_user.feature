Feature: Edit Profile
  As user, I want to edit profiles of users

  # admin
  Scenario: Loading edit own profile as admin
    Given I'm a System Administrator
    And I'm on "user" page for user with id "1"
    When I select "Edit" button
    Then I should be on the "edit profile" page
    And I should see the User Login section of the Edit User form
    And I should see the User Details section of the Edit User form
    And I should see the Password section of the Edit User form
    
  Scenario: Edit own profile as admin
    Given I'm a System Administrator
    And I'm on "edit user" page for user with id "1"
    And I fill in:
      | element                     | content              |
      | user.usertypesforsystem_id  | System Administrator |
      | user.username               | root                 |
      | user.student_no             | abcd                 |
      | user.displayname            | root2                |
      | user.firstname              | Root                 |
      | user.lastname               | Two                  |
      | user.email                  | root.two@example.com |
    When I submit form with "Save" button
    Then I should be on the "profile" page
    And I should see "root2's Profile" in "h1" on the page
    
  Scenario: Change own password as admin
    Given I'm a System Administrator
    And I'm on "edit user" page for user with id "1"
    And I fill in:
      | element                     | content              |
      | password.oldpassword        | password             |
      | password.newpassword        | password2            |
      | password.verifypassword     | password2            |
    When I submit form with "Save" button
    Then I should be on the "profile" page
    And I should see "root's Profile" in "h1" on the page
  
  Scenario: Loading edit other user's profile as admin
    Given I'm a System Administrator
    And I'm on "user" page for user with id "2"
    When I select "Edit" button
    Then I should be on the "edit profile" page
    And I should see the User Login section of the Edit User form
    And I should see the User Details section of the Edit User form
    And I should see the Password section of the Edit User form without old password
    
  Scenario: Edit another user's profile as admin
    Given I'm a System Administrator
    And I'm on "edit user" page for user with id "2"
    And I fill in:
      | element                     | content                 |
      | user.usertypesforsystem_id  | Student                 |
      | user.username               | nowStudent              |
      | user.student_no             | abcd123                 |
      | user.displayname            | Now a Student           |
      | user.firstname              | Now                     |
      | user.lastname               | Student                 |
      | user.email                  | now.student@example.com |
    When I submit form with "Save" button
    Then I should be on the "profile" page
    And I should see "Now a Student's Profile" in "h1" on the page
    
  Scenario: Change another user's password as admin
    Given I'm a System Administrator
    And I'm on "edit user" page for user with id "2"
    And I fill in:
      | element                     | content              |
      | password.newpassword        | password2            |
      | password.verifypassword     | password2            |
    When I submit form with "Save" button
    Then I should be on the "profile" page
    And I should see "First Instructor's Profile" in "h1" on the page
    
  # instructor
  Scenario: Loading edit own profile as instructor
    Given I'm an Instructor
    And I'm on "user" page for user with id "2"
    When I select "Edit" button
    Then I should be on the "edit profile" page
    And I should not see the User Login section of the Edit User form
    And I should see the User Details section of the Edit User form
    And I should see the Password section of the Edit User form
    
  Scenario: Edit own profile as instructor
    Given I'm an Instructor
    And I'm on "edit user" page for user with id "2"
    And I fill in:
      | element                     | content                    |
      | user.displayname            | instructor123              |
      | user.firstname              | instructor                 |
      | user.lastname               | 123                        |
      | user.email                  | instructor.123@example.com |
    When I submit form with "Save" button
    Then I should be on the "profile" page
    And I should see "instructor123's Profile" in "h1" on the page
    
  Scenario: Change own password as instructor
    Given I'm an Instructor
    And I'm on "edit user" page for user with id "2"
    And I fill in:
      | element                     | content              |
      | password.oldpassword        | password             |
      | password.newpassword        | password2            |
      | password.verifypassword     | password2            |
    When I submit form with "Save" button
    Then I should be on the "profile" page
    And I should see "First Instructor's Profile" in "h1" on the page
    
  Scenario: Loading edit another user's profile as instructor
    Given I'm an Instructor with students
    And I'm on "user" page for user with id "3"
    When I select "Edit" button
    Then I should be on the "edit profile" page
    And I should not see the User Login section of the Edit User form
    And I should see the User Details section of the Edit User form
    And I should not see the Password section of the Edit User form
    
  Scenario: Edit another user's profile as instructor
    Given I'm an Instructor with students
    And I'm on "edit user" page for user with id "3"
    And I fill in:
      | element                     | content                    |
      | user.displayname            | student123                 |
      | user.firstname              | student                    |
      | user.lastname               | 123                        |
      | user.email                  | student.123@example.com    |
    When I submit form with "Save" button
    Then I should be on the "profile" page
    And I should see "student123's Profile" in "h1" on the page
    
  # student
  Scenario: Loading edit own profile as student
    Given I'm a Student
    And I'm on "user" page for user with id "3"
    When I select "Edit" button
    Then I should be on the "edit profile" page
    And I should not see the User Login section of the Edit User form
    And I should see the User Details section of the Edit User form
    And I should see the Password section of the Edit User form
    
  Scenario: Edit own profile as student
    Given I'm a Student
    And I'm on "edit user" page for user with id "3"
    And I fill in:
      | element                     | content                    |
      | user.displayname            | student123                 |
      | user.firstname              | student                    |
      | user.lastname               | 123                        |
      | user.email                  | student.123@example.com    |
    When I submit form with "Save" button
    Then I should be on the "profile" page
    And I should see "student123's Profile" in "h1" on the page
    
  Scenario: Change own password as student
    Given I'm a Student
    And I'm on "edit user" page for user with id "3"
    And I fill in:
      | element                     | content              |
      | password.oldpassword        | password             |
      | password.newpassword        | password2            |
      | password.verifypassword     | password2            |
    When I submit form with "Save" button
    Then I should be on the "profile" page
    And I should see "First Student's Profile" in "h1" on the page