Feature: Manage Users
  As user, I want to manage accounts

  Scenario: Loading view users page by Manage Users button as admin
    Given I'm a System Administrator
    And I'm on 'home' page
    When I select the 'Manage Users' button
    Then I should be on the 'users' page
    And I should see '4' users listed
    And I should users with displaynames:
      | displayname           |
      | First Instructor      |
      | First Student         |
      | root                  |
      | Second Student        |

  Scenario: Filter users page as admin
    Given I'm a System Administrator
    And I'm on 'users' page
    When I filter users page by 'Second'
    Then I should see '1' users listed
    And I should users with displaynames:
      | displayname           |
      | Second Student        |