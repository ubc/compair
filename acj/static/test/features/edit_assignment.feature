Feature: Edit Assignment
  As user, I want to edit an assignment

  Scenario: Loading edit assignment page as admin
    Given I'm a System Administrator with assignments
    And I'm on "assignment" page for assignment with id "1" and course id "1"
    When I select "Edit Assignment" button
    Then I should be on the "edit assignment" page

  Scenario: Loading edit assignment page as instructor
    Given I'm an Instructor with assignments
    And I'm on "assignment" page for assignment with id "1" and course id "1"
    When I select "Edit Assignment" button
    Then I should be on the "edit assignment" page

  Scenario: Editing an assignment as instructor
    Given I'm an Instructor with assignments
    And I'm on "edit assignment" page for assignment with id "3" and course id "1"
    When I fill in:
      | element         | content   |
      | assignment.name | New Name  |
    And I fill in the assignment description with "This is the new description"
    And I drop the first criterion
    And I add my default criterion
    And I submit form with "Save" button
    Then I should be on the "course" page
    And I should see the assignment with the new name and description

  Scenario: Editing a assignment's criterion as instructor before comparisons
    Given I'm an Instructor with assignments
    And I'm on "edit assignment" page for assignment with id "3" and course id "1"
    When I edit the second criterion
    And I fill in:
      | element         | content               |
      | criterion.name  | Choose the best one   |
    And I fill in the criterion description with "Choose the best one."
    And I submit modal form with "Update" button
    And I add a new criterion
    And I fill in:
      | element         | content               |
      | criterion.name  | Which do you like?    |
    And I fill in the criterion description with "Choose the one you like best."
    And I toggle the "Include this criterion in my list of default criteria (to use it in other assignments)" checkbox
    And I submit modal form with "Add New" button
    And I submit form with "Save" button
    Then I should be on the "course" page

  Scenario: Cannot Edit a assignment's criterion as instructor after its been compared
    Given I'm an Instructor with assignments
    And I'm on "edit assignment" page for assignment with id "1" and course id "1"
    Then I should not be able to modify criteria
    And I should not be able to add criteria
