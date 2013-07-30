# -*-*- encoding: utf-8 -*-*-

import sys
import json
import uuid
import hashlib
import httplib
import datetime
import urlparse

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

    soapXml = '''<?xml version="1.0" encoding="utf-8"?>
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
        print "Request:", soapXml
    
    #make connection
    parse_results = urlparse.urlparse(sb_url)
    host = parse_results.netloc
    url  = parse_results.path
    ws = httplib.HTTP(host)
    ws.putrequest("POST", url)

    #add headers
    ws.putheader("Content-Type", "application/soap+xml; charset=utf-8")
    ws.putheader("Content-Length", "%d"%(len(soapXml),))
    ws.endheaders()

    #send request
    ws.send(soapXml)

    #get response
    statuscode, statusmessage, header = ws.getreply()
    #print "Response: ", statuscode, statusmessage
    #print "headers: ", header
    res = ws.getfile().read()
    if DEBUG:
        print res

    root = ET.fromstring(res)
    # Use XPath to query for the <tag> element; get its text
    namespaces = {"ilab_type" : "http://ilab.mit.edu/iLabs/type"}
    tag = root.findtext(".//ilab_type:tag", namespaces = namespaces)
    if DEBUG:
        print tag
    return tag

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

        # XXX: This should not be implemented like this. The RLMS 
        # plug-in should be able to contact the Service Broker with the
        # data above, and with this data, retrieve this information
        # automatically.

        sample_data = {
           'AB3904BAF6345D5979C6D85EDB5460E' : {
               'name'        : 'Time of Day Client',
               'duration'    : '-1',
               'coupon_id'   : '64',
               'pass_key'    : '1A20F154-D467-4058-8CF3-CB0E1580F04C',
               'client_guid' : '2D1888C0-7F43-46DC-AD51-3A77A8DE8152',
           },
           'ABCDEFGHIJKLMNOPQRSTUVWXYZ' : {
               'name'        : 'WebLab Microelectronics',
               'duration'    : '-1',
               'coupon_id'   : '36',
               'pass_key'    : 'EDFCA4AE-A611-48D6-85E3-E86A2728B90A',
               'client_guid' : '6BD4E985-4967-4742-854B-D44B8B844A21',
           },
           # ...
        }

        # 
        # ILAB_LABS is a configuration variable that can be set in the
        # config.py file. 
        # 
        self.ilab_labs = app.config.get('ILAB_LABS', sample_data)
        
        laboratories = []
        for laboratory_id in self.ilab_labs:
            lab_data = self.ilab_labs[laboratory_id]
            laboratories.append(Laboratory(lab_data['name'], laboratory_id))
        self.laboratories = laboratories

    def get_version(self):
        return Versions.VERSION_1

    def get_capabilities(self):
        return []

    def test(self):
        json.loads(self.configuration)
        # TODO
        return None

    def get_laboratories(self):
        return self.laboratories

    def reserve(self, laboratory_id, username, institution, general_configuration_str, particular_configurations, request_payload, user_properties, *args, **kwargs):

        # You may want to use a different separator, such as @ or ::, depending on if that's a valid user.
        unique_user_id = '%s_%s' % (username, institution)

        lab_data = self.ilab_labs[laboratory_id]

        url = launchilab(unique_user_id, self.sb_guid, self.sb_url, self.authority_guid, self.group_name, lab_data)
        if DEBUG:
            print repr(url)
        return {
            'load_url' : url
        }


register("iLabs", ['1.0'], __name__)

