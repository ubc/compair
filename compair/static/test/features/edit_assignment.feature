Feature: Edit Assignment
  As user, I want to edit an assignment

  Scenario: Loading edit assignment page as admin
    Given I'm a System Administrator
    And I'm on 'assignment' page for assignment with id '1abcABC123-abcABC123_Z' and course id '1abcABC123-abcABC123_Z'
    When I select the 'Edit Assignment' button
    Then I should be on the 'edit assignment' page

  Scenario: Loading edit assignment page as instructor
    Given I'm an Instructor
    And I'm on 'assignment' page for assignment with id '1abcABC123-abcABC123_Z' and course id '1abcABC123-abcABC123_Z'
    When I select the 'Edit Assignment' button
    Then I should be on the 'edit assignment' page

  Scenario: Editing an assignment as instructor
    Given I'm an Instructor
    And I'm on 'edit assignment' page for assignment with id '3abcABC123-abcABC123_Z' and course id '1abcABC123-abcABC123_Z'
    When I fill form item 'assignment.name' in with 'New Name'
    And I fill in the assignment description with 'This is the new description'
    And I drop the first criterion
    And I add my default criterion
    And I submit form with the 'Save' button
    Then I should be on the 'course' page
    And I should see the assignment with the new name

  Scenario: Editing a assignment's criterion as instructor before comparisons
    Given I'm an Instructor
    And I'm on 'edit assignment' page for assignment with id '3abcABC123-abcABC123_Z' and course id '1abcABC123-abcABC123_Z'
    When I edit the second criterion
    And I fill form item 'criterion.name' in with 'Choose the best one'
    And I fill in the criterion description with 'Choose the best one.'
    And I submit modal form with the 'Save' button
    And I add a new criterion
    And I fill form item 'criterion.name' in with 'Which do you like?'
    And I fill in the criterion description with 'Choose the one you like best.'
    And I toggle the 'Include this criterion in my list of default criteria (to re-use it in other assignments)' checkbox
    And I submit modal form with the 'Save' button
    And I submit form with the 'Save' button
    Then I should be on the 'course' page

  Scenario: Editing assignment's criterion as instructor after the criterion has been compared
    Given I'm an Instructor
    And I'm on 'edit assignment' page for assignment with id '1abcABC123-abcABC123_Z' and course id '1abcABC123-abcABC123_Z'
    When I edit the second criterion
    Then I should see a warning message in the edit criterion modal

  Scenario: Cannot add or remove an assignment's criterion as instructor after its been compared
    Given I'm an Instructor
    And I'm on 'edit assignment' page for assignment with id '1abcABC123-abcABC123_Z' and course id '1abcABC123-abcABC123_Z'
    Then I should not be able to add criteria
    And I should not be able to remove criteria
