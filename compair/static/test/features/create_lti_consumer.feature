Feature: Create LTI Consumers
  As user, I want to create LTI consumers

  Scenario: Loading create LTI consumers page as admin
    Given I'm a System Administrator
    And I'm on 'manage lti' page
    When I select the 'Add LTI Consumer' button
    Then I should be on the 'create lti consumer' page

  Scenario: Creating a lti consumer as admin
    Given I'm a System Administrator
    And I'm on 'create lti consumer' page
    When I fill form item 'consumer.oauth_consumer_key' in with 'consumer_key_4'
    And I fill form item 'consumer.oauth_consumer_secret' in with 'consumer_secret_4'
    And I submit form with the 'Save' button
    Then I should be on the 'manage lti' page
    And I should see '4' consumers listed
    And I should see consumers with consumer keys:
      | oauth_consumer_key  |
      | consumer_key_1      |
      | consumer_key_2      |
      | consumer_key_3      |
      | consumer_key_4      |
