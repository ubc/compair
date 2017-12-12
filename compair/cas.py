# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from flask import current_app, url_for
from caslib import SAMLClient, CASClient, CASResponse
from xml.dom.minidom import parseString
import requests

def _use_saml():
    return current_app.config.get('CAS_USE_SAML', False)

def _get_client():
    server_url = current_app.config.get('CAS_SERVER')
    service_url = url_for('login_api.cas_auth', _external=True)
    auth_prefix = current_app.config.get('CAS_AUTH_PREFIX', '/cas')

    if _use_saml():
        return CustomSAMLClient(
            server_url=server_url,
            service_url=service_url,
            auth_prefix=auth_prefix
        )
    else:
        return CustomCASClient(
            server_url=server_url,
            service_url=service_url,
            auth_prefix=auth_prefix
        )

def get_cas_login_url():
    return _get_client()._login_url()

def validate_cas_ticket(ticket):
    client = _get_client()
    return client.saml_serviceValidate(ticket) if _use_saml() else client.cas_serviceValidate(ticket)

def get_cas_logout_url():
    logout_service_url = url_for('route_app', _external=True)
    return _get_client()._logout_url(logout_service_url)


class CustomCASClient(CASClient):
    def get_cas_response(self, url):
        try:
            # overwritten to allow development environment to use self signed certificates
            verify = current_app.config.get('ENFORCE_SSL', True)
            response = requests.get(url, verify=verify)
            response_text = response.text.encode('utf-8') if response.text else None
            return CASResponse(response_text)
        except Exception:
            current_app.logger.exception("CASLIB: Error retrieving a response")
            return None


class CustomSAMLClient(SAMLClient):
    def get_saml_response(self, url, envelope):
        try:
            # overwritten to allow development environment to use self signed certificates
            verify = current_app.config.get('ENFORCE_SSL', True)
            response = requests.post(url, data=envelope, verify=verify)
            response_text = response.text.encode('utf-8') if response.text else None
            return CustomSAMLResponse(response_text)
        except Exception:
            current_app.logger.error("SAML: Error retrieving a response")
            raise



class CustomSAMLResponse():
    """
    based on caslib.py SAMLResponse but rewritten to be less strict and more flexible
    """
    def __init__(self, response):
        self.response = response
        (self.xml, self.map) = self.parse_response(response)
        self.success = "success" in self.map.get('Status', {})\
                                            .get('Value', '').lower()
        if not self.success:
            self.user = None
            self.attributes = None
            return
        # NOTE: Not all of these attributes will exist for a given type.
        # The values you need are supecific to the type of request being made.
        # For more information, RTD
        self.user = self._get_user()
        self.attributes = self._get_attributes()

    def __str__(self):
        return "CustomSAMLResponse - Success: %s, User: %s" % (self.success, self.user)

    def __unicode__(self):
        return "CustomSAMLResponse - Success: %s, User: %s" % (self.success, self.user)

    def _get_attributes(self):
        attributes = {}
        for attribute_name, attribute in self.map.get('Assertion', {}).get('AttributeStatement', {}).items():
            if attribute_name != 'Subject':
                attributes[attribute_name] = attribute
        return attributes

    def _get_user(self):
        return self.map.get('Assertion', {}).get('AttributeStatement', {}).get('Subject', {}).get('NameIdentifier')

    def parse_response(self, response):
        samlMap = {}
        if response is None or len(response) == 0:
            return (None, samlMap)
        try:
            doc = parseString(response)
            node_element = self._get_response_node(doc.documentElement)
            if node_element == None:
                raise Exception(
                    "Parsing saml Response failed. "
                    "Expected saml1p:Response in XML response.")

            tag_name = self.clean_tag_name(node_element)
            if tag_name != 'Response':
                raise Exception(
                    "Parsing saml Response failed. "
                    "Expected saml1p:Response in XML response.")
            # First level, SAML should contain an Assertion and a Status
            for child in node_element.childNodes:
                if child.nodeType != child.ELEMENT_NODE:
                    raise Exception(
                        "Parsing saml Response failed. "
                        "Expected ELEMENT_NODE to follow saml1p:Response.")
                # Grab relevant info from remaining XML
                samlMap.update(self.xml2dict(child))
        except Exception as e:
            current_app.logger.error(str(e))
            raise Exception("Malformed SAML response: %s" % response)

        return (doc, samlMap)

    def _get_response_node(self, node_element):
        tag_name = self.clean_tag_name(node_element)
        if tag_name == 'Response':
            return node_element

        if node_element.childNodes:
            for childNode in node_element.childNodes:
                node_element = self._get_response_node(childNode)
                if node_element != None:
                    return node_element

        return None

    def clean_tag_name(self, tag):
        real_name = tag.nodeName
        return real_name\
            .replace("saml1:", "")\
            .replace("saml1p:", "")\
            .replace("SOAP-ENV", "")

    def parse_attr(self, tag):
        attr_key = tag.getAttribute('AttributeName')
        attr_values = tag.getElementsByTagName("saml1:AttributeValue") + tag.getElementsByTagName("AttributeValue")
        py_values = [node.childNodes[0].data for node in attr_values]
        if len(py_values) == 0:
            return None
        elif len(py_values) == 1:
            return {attr_key: py_values[0]}
        else:
            return {attr_key: py_values}

    def xml2dict(self, tag):
        """
        Recursively create python dict's to replace the nested XML structure
        """
        # Attributes must be parsed separately, since the namespaces conflict.
        tag_name = self.clean_tag_name(tag)
        if tag_name == 'Attribute':
            return self.parse_attr(tag)

        # These attributes are the key-value pairs associated on the same XML
        # line.
        if tag.hasAttributes():
            nodeMap = dict(
                    (key, value) for (key, value) in
                    tag.attributes.items())
        else:
            nodeMap = {}
        # Any XML nested inside will be caught with this loop(Will recurse)
        children_map = {}
        for child in tag.childNodes:
            if child.nodeType == child.TEXT_NODE:
                text = child.nodeValue
                nodeMap[tag_name] = text.strip()
                return nodeMap
            elif child.nodeType != child.ELEMENT_NODE:
                raise Exception("Parsing saml Response failed. "
                                "Expected TEXT_NODE|ELEMENT_NODE to follow %s"
                                % tag.nodeName)
            children_map.update(self.xml2dict(child))
        nodeMap[tag_name] = children_map

        return nodeMap
