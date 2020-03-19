import ldap
from . import UserLookupMixin
from flask import current_app

class LdapLookupEngine(UserLookupMixin):
    """ User info lookup using LDAP
    """

    def __init__(self, config):
        """ Inits with flask app config or a dict
        """
        self._config = config
        self._ldap_client = None

        self._ldap_url = config.get('USER_LOOKUP_LDAP_URL', None)
        self._ldap_proxy_agent = config.get('USER_LOOKUP_LDAP_PROXY_AGENT', None)
        self._ldap_proxy_password = config.get('USER_LOOKUP_LDAP_PROXY_PASSWORD', None)

        self._base_dn = config.get('USER_LOOKUP_LDAP_BASE_DN', None)
        self._student_number_attribute = config.get('USER_LOOKUP_LDAP_SEARCH_STUDENT_NUM_ATTRS', None)
        self._username_attribute = config.get('USER_LOOKUP_LDAP_SEARCH_USERNAME_ATTRS', None)
        self._unique_identifier = config.get('USER_LOOKUP_LDAP_SEARCH_UNIQUE_IDENTIFIER_ATTRS', None)

    def __enter__(self):
        self._ldap_client = None
        try:
            self._ldap_client = ldap.initialize(self._ldap_url, bytes_mode=False)
            # Don't chase referrals, just in case if we are connecting to Microsoft AD
            self._ldap_client.set_option(ldap.OPT_REFERRALS, 0)
            self._ldap_client.simple_bind_s(self._ldap_proxy_agent, self._ldap_proxy_password)
            return self

        except ldap.INVALID_CREDENTIALS:
            self._ldap_client = None
            current_app.logger.error("Invalid LDAP credentials")
        except Exception as ex:
            self._ldap_client = None
            current_app.logger.error("Exception caught when trying to bind LDAP")
            current_app.logger.error(ex)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self._ldap_client:
            self._ldap_client.unbind()

    def is_available(self):
        return not (self._ldap_client is None)

    @classmethod
    def _get_first_str(cls, attr, ldap_result):
        """ Parses the LDAP result and from the first entry gets the first value of the given attribute.
        Decodes values as utf-8 strings.  Returns None if attribute not found or empty result.
        """
        if len(ldap_result) < 1:
            return None

        attributes = ldap_result[0][1]
        values = attributes.get(attr, None)
        if type(values) is list and len(values) > 0:
            return values[0].decode('utf-8')
        else:
            return None

    @classmethod
    def _split_display_name(cls, ldap_result):
        """ Splits the LDAP attribute displayName into (first_name, last_name)
        """
        display_name = LdapLookupEngine._get_first_str('displayName', ldap_result)
        if not display_name:
            return (None, None)
        values = display_name.split()

        if len(values) < 2:
            return (display_name, None)

        return (' '.join(values[0:-1]), values[-1])

    @classmethod
    def _deduct_names(cls, ldap_result):
        """ Deducts user first name and last name from LDAP result. Priority given to displayName.
        Otherse, try the sn and givenName attributes from inetOrgPerson class.
        Returns result in tuple of (first_name, last_name)
        """
        first_name, last_name = LdapLookupEngine._split_display_name(ldap_result)

        if first_name is None:
            first_name = LdapLookupEngine._get_first_str('givenName', ldap_result)
        if last_name is None:
            last_name = LdapLookupEngine._get_first_str('sn', ldap_result)

        return (first_name, last_name)

    def _parse_ldap_result(self, ldap_result):
        first_name, last_name = LdapLookupEngine._deduct_names(ldap_result)
        user = {
            'username': LdapLookupEngine._get_first_str(self._username_attribute, ldap_result),
            'student_number': LdapLookupEngine._get_first_str(self._student_number_attribute, ldap_result),
            'unique_identifier': LdapLookupEngine._get_first_str(self._unique_identifier, ldap_result),
            'firstname': first_name,
            'lastname': last_name,
        }
        return user

    def get_by_username(self, username):
        """ Retrieves user info using username.  Returns None if not found
        """
        try:
            result = self._ldap_client.search_s(self._base_dn, ldap.SCOPE_SUBTREE, \
                '{}={}'.format(self._username_attribute, username))

            if len(result) == 0:
                return None
            return self._parse_ldap_result(result)
        except Exception as ex:
            current_app.logger.error("Exception caught when trying to search user by unique id")
            current_app.logger.error(ex)
            raise

    def get_by_student_number(self, student_number):
        """ Retrieves user info using student number.  Returns None if not found
        """
        try:
            result = self._ldap_client.search_s(self._base_dn, ldap.SCOPE_SUBTREE, \
                '{}={}'.format(self._student_number_attribute, student_number))

            if len(result) == 0:
                return None
            return self._parse_ldap_result(result)
        except Exception as ex:
            current_app.logger.error("Exception caught when trying to search user by unique id")
            current_app.logger.error(ex)
            raise