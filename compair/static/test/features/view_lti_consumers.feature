Feature: Manage LTI Consumers
  As user, I want to manage LTI consumers

  Scenario: Loading view LTI consumers page by LTI Consumers button as admin
    Given I'm a System Administrator
    And I'm on 'home' page
    When I select the 'Manage LTI' button
    Then I should be on the 'manage lti' page
    And I should see '3' consumers listed
    And I should see consumers with consumer keys:
      | oauth_consumer_key  |
      | consumer_key_1      |
      | consumer_key_2      |
      | consumer_key_3      |
    And I should see '3' contexts listed
    And I should see contexts with titles:
      | context_title         |
      | Canvas Course One     |
      | Canvas Course Two     |
      | Blackboard Course One |

  Scenario: Disable LTI consumer as admin
    Given I'm a System Administrator
    And I'm on 'manage lti' page
    When I set the first consumer's active status to 'Inactive'
    Then I should see a success message

  Scenario: Enable LTI consumer as admin
    Given I'm a System Administrator
    And I'm on 'manage lti' page
    When I set the third consumer's active status to 'Active'
    Then I should see a success message

  Scenario: Unlink LTI context as admin
    Given I'm a System Administrator
    And I'm on 'manage lti' page
    When I unlink the second lti context
    Then I should see '2' contexts listed
    And I should see contexts with titles:
      | context_title         |
      | Canvas Course One     |
      | Blackboard Course One |