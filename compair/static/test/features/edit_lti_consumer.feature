Feature: Edit LTI Consumers
  As user, I want to edit LTI consumers

  Scenario: Loading edit LTI consumer page as admin
    Given I'm a System Administrator
    And I'm on 'manage lti' page
    When I click the first consumer's Edit button
    Then I should be on the 'edit lti consumer' page

  Scenario: Editing a lti consumer as admin
    Given I'm a System Administrator
    And I'm on 'edit lti consumer' page for consumer with id '1abcABC123-abcABC123_Z'
    When I fill form item 'consumer.oauth_consumer_key' in with 'new_consumer_key_1'
    And I fill form item 'consumer.oauth_consumer_secret' in with 'new_consumer_secret_1'
    And I fill form item 'consumer.user_id_override' in with 'new_user_id_override'
    And I toggle the 'Active' checkbox
    And I submit form with the 'Save' button
    Then I should be on the 'manage lti' page
    And I should see '3' consumers listed
    And I should see consumers with consumer keys:
      | oauth_consumer_key  |
      | new_consumer_key_1  |
      | consumer_key_2      |
      | consumer_key_3      |
