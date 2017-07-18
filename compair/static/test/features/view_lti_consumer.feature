Feature: Manage LTI Consumers
  As user, I want to manage LTI consumers

  Scenario: Loading view LTI consumer as admin
    Given I'm a System Administrator
    And I'm on 'manage lti' page
    When I click the first consumer's key
    Then I should be on the 'lti consumer' page

  Scenario: View LTI consumer as admin
    Given I'm a System Administrator
    And I'm on 'lti consumer' page for consumer with id '1abcABC123-abcABC123_Z'
    Then I should see consumer_key_1's information

  Scenario: View LTI inactive consumer as admin
    Given I'm a System Administrator
    And I'm on 'lti consumer' page for consumer with id '3abcABC123-abcABC123_Z'
    Then I should see consumer_key_3's information

  Scenario: Disable LTI consumer as admin
    Given I'm a System Administrator
    And I'm on 'lti consumer' page for consumer with id '1abcABC123-abcABC123_Z'
    When I toggle the 'consumer.active' form checkbox
    Then I should see a success message

  Scenario: Enable LTI consumer as admin
    Given I'm a System Administrator
    And I'm on 'lti consumer' page for consumer with id '3abcABC123-abcABC123_Z'
    When I toggle the 'consumer.active' form checkbox
    Then I should see a success message