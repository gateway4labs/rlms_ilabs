# -*-*- encoding: utf-8 -*-*-

import sys
import json
import uuid
import hashlib
import urllib2
import datetime
import urlparse
import traceback

import xml.etree.ElementTree as ET

from flask.ext.wtf import TextField, PasswordField, Required, URL, ValidationError

from labmanager import app
from labmanager.forms import AddForm, RetrospectiveForm, GenericPermissionForm
from labmanager.rlms import register, BaseRLMS, BaseFormCreator, Versions, Capabilities, Laboratory

DEBUG = True

def launchilab(username, sb_guid, sb_url, authority_guid, group_name, lab_data):

    # Take lab data; pass it to string (just in case the duration for instance is an int)
    duration   = str(lab_data['duration'])
    couponID   = str(lab_data['coupon_id'])
    passkey    = str(lab_data['pass_key'])
    clientGuid = str(lab_data['client_guid'])

    soap_xml = '''<?xml version="1.0" encoding="utf-8"?>
            <soap12:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
            xmlns:xsd="http://www.w3.org/2001/XMLSchema"
            xmlns:soap12="http://www.w3.org/2003/05/soap-envelope">
                <soap12:Header>
                    <OperationAuthHeader xmlns="http://ilab.mit.edu/iLabs/type">
                        <coupon  xmlns="http://ilab.mit.edu/iLabs/type">
                            <couponId>''' + couponID + '''</couponId>
                            <issuerGuid>''' + sb_guid + '''</issuerGuid>
                            <passkey>''' + passkey +'''</passkey>
                        </coupon>
                    </OperationAuthHeader>
                </soap12:Header>
                <soap12:Body>
                    <LaunchLabClient xmlns="http://ilab.mit.edu/iLabs/Services">
                        <clientGuid>''' + clientGuid +'''</clientGuid>
                        <groupName>''' + group_name + '''</groupName>
                        <userName>''' + username +'''</userName>
                        <authorityKey>''' + authority_guid + '''</authorityKey>
                        <duration>''' + duration + '''</duration>
                        <autoStart>1</autoStart>
                    </LaunchLabClient>
                </soap12:Body>
            </soap12:Envelope>'''
    if DEBUG:
        print "Request:", soap_xml
   
    request = urllib2.Request(sb_url, data = soap_xml, headers = {
        'Content-Type'   : 'application/soap+xml; charset=utf-8',
    })

    res = urllib2.urlopen(request).read()
    if DEBUG:
        print res

    root = ET.fromstring(res)

    # Use XPath to query for the <tag> element; get its text
    namespaces = {"ilab_type" : "http://ilab.mit.edu/iLabs/type"}
    tag = root.findtext(".//ilab_type:tag", namespaces = namespaces)
    if DEBUG:
        print tag
    return tag

def get_foreign_credentials(base_url, auth_key):
    system_data = {}
    lab_data = {}
    try:
        if base_url.endswith('/'):
            base_url = base_url[:-1]

        contents = urllib2.urlopen("%s/clientList.aspx?authKey=%s" % (base_url, auth_key)).read()
        root = ET.fromstring(contents)

        system_data['sb_name']         = root.find("Sb_Name").text
        system_data['location']        = root.find("Location").text
        system_data['sb_guid']         = root.find("Sb_Guid").text
        system_data['sb_service_url']  = root.find("SbServiceUrl").text
        system_data['sb_url']          = root.find("SbUrl").text
        system_data['authority_group'] = root.find("AuthorityGroup").text

        for lab in root.iter("lab"):
            name           = lab.find("name").text
            lab_data[name] = {
                'name'           : name,
                'duration'       : lab.find("duration").text,
                'auth_coupon_id' : lab.find("authCouponId").text,
                'pass_key'       : lab.find("pass_key").text,
                'client_guid'    : lab.find('client_guid').text,
                'description'    : lab.find('lab_description').text,
            }
    except:
        print >> sys.stderr, "clientList.aspx doesn't exist. Please upgrade your iLab installation to properly support gateway4labs, or establish the ILAB_LABS variable in the LabManager"
        traceback.print_exc()

    return system_data, lab_data

def get_module(version):
    """get_module(version) -> proper module for that version

    Right now, a single version is supported, so this module itself will be returned.
    When compatibility is required, we may change this and import different modules.
    """
    # TODO: check version
    return sys.modules[__name__]

# TODO: to be removed
DEFAULT_DATA = {
    'sb_guid'        : 'ISB-247A4591CA1443485D85657CF357',
    'sb_url'         : 'http://ludi.mit.edu/iLabServiceBroker/iLabServiceBroker.asmx',
    'group_name'     : 'Experiment_Group',
    'authority_guid' : 'fakeGUIDforRMLStest-12345',
}

class IlabsAddForm(AddForm):

    sb_guid        = TextField("SB GUID",        validators = [Required()], description = "Service Broker unique identifier", default = DEFAULT_DATA['sb_guid'])
    sb_url         = TextField("SB URL",    validators = [Required(), URL() ], description = "Service Broker URL", default = DEFAULT_DATA['sb_url'])
    authority_guid = TextField("Authority Guid",        validators = [Required()], description = "Authority GUID", default = DEFAULT_DATA['authority_guid'])
    group_name     = TextField("Group name", validators = [Required()], description = "Client specific info", default = DEFAULT_DATA['group_name'])

    def __init__(self, add_or_edit, *args, **kwargs):
        super(IlabsAddForm, self).__init__(*args, **kwargs)
        self.add_or_edit = add_or_edit

    @staticmethod
    def process_configuration(old_configuration, new_configuration):
        return new_configuration

class IlabsPermissionForm(RetrospectiveForm):
    pass

class IlabsLmsPermissionForm(IlabsPermissionForm, GenericPermissionForm):
    pass

class IlabsFormCreator(BaseFormCreator):

    def get_add_form(self):
        return IlabsAddForm

    def get_permission_form(self):
        return IlabsPermissionForm

    def get_lms_permission_form(self):
        return IlabsLmsPermissionForm

FORM_CREATOR = IlabsFormCreator()

class RLMS(BaseRLMS):

    def __init__(self, configuration):
        self.configuration = json.loads(configuration or '{}')

        self.sb_guid        = self.configuration.get('sb_guid')
        self.sb_url         = self.configuration.get('sb_url')
        self.authority_guid = self.configuration.get('authority_guid')
        self.group_name     = self.configuration.get('group_name')


    def get_version(self):
        return Versions.VERSION_1

    def get_capabilities(self):
        return [ Capabilities.WIDGET ] 

    def test(self):
        json.loads(self.configuration)
        # TODO
        return None

    def load_widget(self, reservation_id, widget_name, **kwargs):
        return {
            'url' : reservation_id 
        }

    def list_widgets(self, laboratory_id, **kwargs):
        labs = app.config.get('ILAB_WIDGETS', {})
        default_widget = dict( name = 'default', description = 'Default widget')
        return labs.get(laboratory_id, [ default_widget ])

    def _get_labs_data(self):
        ilab_labs = app.config.get('ILAB_LABS', {})
        if ilab_labs:
            return ilab_labs


    def get_laboratories(self, **kwargs):
        laboratories = []

        system_data, labs_data = self._get_labs_data()
        for name in labs_data:
            laboratories.append(Laboratory(name = name, laboratory_id = name, description = labs_data[name]['description']))

        return laboratories

    def reserve(self, laboratory_id, username, institution, general_configuration_str, particular_configurations, request_payload, user_properties, *args, **kwargs):

        # You may want to use a different separator, such as @ or ::, depending on if that's a valid user.
        unique_user_id = '%s_%s' % (username, institution)

        system_data, ilab_labs = self._get_labs_data()
        lab_data = ilab_labs[laboratory_id]

        url = launchilab(unique_user_id, self.sb_guid, self.sb_url, self.authority_guid, self.group_name, lab_data)
        if DEBUG:
            print repr(url)
        return {
            'load_url' : url,
            'reservation_id' : url
        }


register("iLabs", ['1.0'], __name__)

