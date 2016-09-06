Feature: View Navbar
  As user, I want to see my navigation bar

  Scenario: Loading navbar as admin
    Given I'm a System Administrator
    And I'm on 'home' page
    Then I should see the brand home link
    And I should see the admin navigation items
    And I should see the profile and logout links

  Scenario: Loading navbar as instructor
    Given I'm an Instructor
    And I'm on 'home' page
    Then I should see the brand home link
    And I should see the instructor navigation items
    And I should see the profile and logout links

  Scenario: Loading navbar as student
    Given I'm a Student
    And I'm on 'home' page
    Then I should see the brand home link
    And I should see the student navigation items
    And I should see the profile and logout links