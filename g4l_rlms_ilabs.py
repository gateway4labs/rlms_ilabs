# -*-*- encoding: utf-8 -*-*-

import sys
import httplib
import json
import datetime
import uuid
import hashlib

import xml.etree.ElementTree as ET

from flask.ext.wtf import TextField, PasswordField, Required, URL, ValidationError

from labmanager.forms import AddForm, RetrospectiveForm, GenericPermissionForm
from labmanager.rlms import register, BaseRLMS, BaseFormCreator, Versions, Capabilities, Laboratory

def launchilab(username):

    #from scorm or other format provided by the ServiceBroker 

    # ServuiceBroker Info
    host= "ludi.mit.edu"
    url = "/iLabServiceBroker/iLabServiceBroker.asmx"
    sbGuid = "ISB-247A4591CA1443485D85657CF357"

    # Client specific Info
    groupName = "Experiment_Group"

    # WebLab Micro-electronics -- Batch Applet lab
    webLabClientGuid = "6BD4E985-4967-4742-854B-D44B8B844A21"
    webLabCouponID = "36" 
    webLabPassCode = "EDFCA4AE-A611-48D6-85E3-E86A2728B90A"

    # Time of day without scheduling -- Interactive redirect
    todNotScheduledGuid="2D1888C0-7F43-46DC-AD51-3A77A8DE8152"
    todCouponID = "64"
    todPassCode = "1A20F154-D467-4058-8CF3-CB0E1580F04C"

    #Specific to LMS or other SerrviceBroker registered authority
    authorityGuid = "fakeGUIDforRMLStest-12345"


    #########

    duration = "-1"

    couponID = todCouponID
    passkey = todPassCode
    clientGuid = todNotScheduledGuid

    soapXml = '''<?xml version="1.0" encoding="utf-8"?>
            <soap12:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
            xmlns:xsd="http://www.w3.org/2001/XMLSchema"
            xmlns:soap12="http://www.w3.org/2003/05/soap-envelope">
                <soap12:Header>
                    <OperationAuthHeader xmlns="http://ilab.mit.edu/iLabs/type">
                        <coupon  xmlns="http://ilab.mit.edu/iLabs/type">
                            <couponId>''' + couponID + '''</couponId>
                            <issuerGuid>''' + sbGuid + '''</issuerGuid>
                            <passkey>''' + passkey +'''</passkey>
                        </coupon>
                    </OperationAuthHeader>
                </soap12:Header>
                <soap12:Body>
                    <LaunchLabClient xmlns="http://ilab.mit.edu/iLabs/Services">
                        <clientGuid>''' + clientGuid +'''</clientGuid>
                        <groupName>''' + groupName + '''</groupName>
                        <userName>''' + username +'''</userName>
                        <authorityKey>''' + authorityGuid + '''</authorityKey>
                        <duration>''' + duration + '''</duration>
                        <autoStart>1</autoStart>
                    </LaunchLabClient>
                </soap12:Body>
            </soap12:Envelope>'''

    #make connection
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
    #print res, "\n"
    root = ET.fromstring(res)
    tag = root[0][0][0][1].text
    return tag

def get_module(version):
    """get_module(version) -> proper module for that version

    Right now, a single version is supported, so this module itself will be returned.
    When compatibility is required, we may change this and import different modules.
    """
    # TODO: check version
    return sys.modules[__name__]

class IlabsAddForm(AddForm):

    remote_login = TextField("Login",        validators = [Required()])
    password     = PasswordField("Password")
    url          = TextField("URL",    validators = [Required(), URL() ])

    def __init__(self, add_or_edit, *args, **kwargs):
        super(IlabsAddForm, self).__init__(*args, **kwargs)
        self.add_or_edit = add_or_edit

    @staticmethod
    def process_configuration(old_configuration, new_configuration):
        old_configuration_dict = json.loads(old_configuration)
        new_configuration_dict = json.loads(new_configuration)
        if new_configuration_dict.get('password', '') == '':
            new_configuration_dict['password'] = old_configuration_dict.get('password','')
        return json.dumps(new_configuration_dict)

    def validate_password(form, field):
        if form.add_or_edit and field.data == '':
            raise ValidationError("This field is required.")

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

        self.login    = self.configuration.get('remote_login')
        self.password = self.configuration.get('password')
        self.url = self.configuration.get('url')
        
        # if self.login is None or self.password is None or self.url is None:
        #    raise Exception("Laboratory misconfigured: fields missing" )

    def get_version(self):
        return Versions.VERSION_1

    def get_capabilities(self):
        return []

    def test(self):
        json.loads(self.configuration)
        # TODO
        return None

    def get_laboratories(self):
        return [ Laboratory('Time of Day Client', 'AB3904BAF6345D5979C6D85EDB5460E'),
                 Laboratory('Amplitude Modulation', 'AM-Lab-5C053055-18F4-4B5F-915C-8C6F6555EBDE'),
                 Laboratory('BEE Lab Analysis', 'beeA-056D99F3-7F2A-42B8-BD28-ECEC2CC72D74'),
                 Laboratory('Building Energy Efficiency Client','beeTC-B053E3E7-3139-452E-BF07-9FBCC8CE1F6E'),
                 Laboratory('TimeOfDay for testing RMLS', 'TOD-12345')]

    def reserve(self, laboratory_id, username, institution, general_configuration_str, particular_configurations, request_payload, user_properties, *args, **kwargs):
        # You may want to use a different separator, such as @ or ::, depending on if that's a valid user.
        unique_user_id = '%s_%s' % (username, institution)

        url = launchilab(unique_user_id)

        return {
            'load_url' : url
        }


register("iLabs", ['1.0'], __name__)

