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
from labmanager.forms import AddForm
from labmanager.rlms import register, BaseRLMS, BaseFormCreator, Versions, Capabilities, Laboratory

DEBUG = app.config.get('debug', False)

def launchilab(username, sb_guid, sb_service_url, authority_guid, group_name, lab_data):

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
   
    request = urllib2.Request(sb_service_url, data = soap_xml, headers = {
        'Content-Type'   : 'application/soap+xml; charset=utf-8',
    })

    res = urllib2.urlopen(request, timeout=10).read()
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
        
        headers = {'X-ISA-Auth-Key' : auth_key}

        client_list_url = "%s/clientList.aspx" % base_url
        r = ILAB.cached_session.timeout_get(client_list_url, headers = headers)
        r.raise_for_status()
        contents = r.text
        root = ET.fromstring(contents)

        system_data['sb_name']         = root.find("Agent_Name").text
        system_data['location']        = root.find("Location").text
        system_data['sb_guid']         = root.find("Agent_GUID").text
        system_data['sb_service_url']  = root.find("WebService_URL").text
        system_data['sb_url']          = base_url
        system_data['authority_group'] = root.find("groupName").text

        for lab in root.iter("iLabClient"):
            name           = lab.find("clientName").text
            lab_data[name] = {
                'name'           : name,
                'duration'       : lab.find("duration").text,
                'coupon_id'      : lab.find("authCouponId").text,
                'pass_key'       : lab.find("authPasskey").text,
                'client_guid'    : lab.find('clientGuid').text,
                'description'    : lab.find('description').text,
            }
            if lab.find('height') is not None:
                lab_data[name]['height'] = lab.find('height').text

            if lab.find('translations') is not None:
                translations_url = lab.find('translations').text
                if translations_url:
                    lab_data[name]['translations'] = lab.find('translations').text
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

    sb_guid        = TextField("SB GUID",        validators = [Required()], description = "Service Broker unique identifier")
    sb_url         = TextField("SB URL",    validators = [Required(), URL() ], description = "Service Broker URL")
    authority_guid = TextField("Authority Guid",        validators = [Required()], description = "Authority GUID")
    group_name     = TextField("Group name", validators = [Required()], description = "Client specific info")
    default_height = TextField("Default height", description = "Default height")

    def __init__(self, add_or_edit, *args, **kwargs):
        super(IlabsAddForm, self).__init__(*args, **kwargs)
        self.add_or_edit = add_or_edit

    @staticmethod
    def process_configuration(old_configuration, new_configuration):
        return new_configuration

class IlabsFormCreator(BaseFormCreator):

    def get_add_form(self):
        return IlabsAddForm

FORM_CREATOR = IlabsFormCreator()

class RLMS(BaseRLMS):

    def __init__(self, configuration):
        self.configuration = json.loads(configuration or '{}')

        self.sb_guid        = self.configuration.get('sb_guid')
        self.sb_url         = self.configuration.get('sb_url')
        self.sb_service_url = self.configuration.get('sb_service_url', self.sb_url)
        self.authority_guid = self.configuration.get('authority_guid')
        self.group_name     = self.configuration.get('group_name')
        self.default_height = self.configuration.get('default_height')


    def get_version(self):
        return Versions.VERSION_1

    def get_capabilities(self):
        return [ Capabilities.WIDGET, Capabilities.TRANSLATIONS, Capabilities.CHECK_URLS ]

    def test(self):
        # TODO
        return None

    def load_widget(self, reservation_id, widget_name, **kwargs):
        return {
            'url' : reservation_id 
        }

    def list_widgets(self, laboratory_id, **kwargs):
        labs = app.config.get('ILAB_WIDGETS', {})
        default_widget = dict( name = 'default', description = 'Default widget')
        labs_data = self._get_labs_data(use_cache = True)
        if labs_data and laboratory_id in labs_data and 'height' in labs_data[laboratory_id]:
            default_widget['height'] = labs_data[laboratory_id]['height']
        elif self.default_height:
            default_widget['height'] = self.default_height

        return labs.get(laboratory_id, [ default_widget ])

    def _get_labs_data(self, use_cache):
        ilab_labs = app.config.get('ILAB_LABS', {})
        if ilab_labs:
            return ilab_labs

        foreign_credentials = None
        if use_cache:
            foreign_credentials = ILAB.rlms_cache.get('foreign_credentials')

        if foreign_credentials is not None:
            system_data, ilab_labs = foreign_credentials
        else:
            system_data, ilab_labs = get_foreign_credentials(self.sb_url, self.authority_guid)
            foreign_credentials = system_data, ilab_labs
            ILAB.rlms_cache['foreign_credentials'] = foreign_credentials

        self.sb_guid        = system_data.get('sb_guid',         self.sb_guid)
        self.sb_service_url = system_data.get('sb_service_url',  self.sb_service_url)
        self.group_name     = system_data.get('authority_group', self.group_name)

        return ilab_labs

    def get_check_urls(self, laboratory_id):
        labs_data = self._get_labs_data(True)
        return [ self.sb_url ]

    def get_laboratories(self, **kwargs):
        laboratories = []

        labs_data = self._get_labs_data(use_cache = True)
        for name in labs_data:
            lab = Laboratory(name = name, laboratory_id = name)
            if 'description' in labs_data[name]:
                lab.description = labs_data[name]['description']
            laboratories.append(lab)

        return laboratories

    def get_translations(self, laboratory_id, **kwargs):
        KEY = u'__translations_%s' % laboratory_id
        translations = ILAB.rlms_cache.get(KEY)
        if translations:
            return translations

        labs_data = self._get_labs_data(use_cache = True)
        lab_data = labs_data.get(laboratory_id, {})
        translations_url = lab_data.get('translations')
        result = {}
        if translations_url:
            try:
                r = ILAB.cached_session.timeout_get(translations_url)
                r.raise_for_status()
                translations = r.json()
                
                metadata = translations.pop('@metadata', {})
                mails = metadata.get('author_mails', [])
                namespaces = metadata.get('namespaces', {})

                processed_translations = {
                    # language : {
                    #     key : {
                    #        'value' : value,
                    #        'namespace' : namespace,
                    #     },
                    # }
                }

                for lang, lang_data in translations.iteritems():
                    processed_translations[lang] = {}

                    for key, value in lang_data.iteritems():
                        processed_translations[lang][key] = {
                            'value' : value,
                        }
                        if key in namespaces:
                            processed_translations[lang][key]['namespace'] = namespaces[key]

                result = {
                    'translations' : processed_translations,
                    'mails' : mails,
                }
            except Exception as e:
                traceback.print_exc()

        ILAB.rlms_cache[KEY] = result
        return result

    def reserve(self, laboratory_id, username, institution, general_configuration_str, particular_configurations, request_payload, user_properties, *args, **kwargs):

        # You may want to use a different separator, such as @ or ::, depending on if that's a valid user.
        unique_user_id = '%s_%s' % (username, institution)

        ilab_labs = self._get_labs_data(use_cache = False)
        lab_data = ilab_labs[laboratory_id]

        url = launchilab(unique_user_id, self.sb_guid, self.sb_service_url, self.authority_guid, self.group_name, lab_data)
        if DEBUG:
            print repr(url)
        return {
            'load_url' : url,
            'reservation_id' : url
        }

def populate_cache(rlms):
    for lab in rlms.get_laboratories():
        rlms.get_translations(lab.laboratory_id)

ILAB = register("iLabs", ['1.0'], __name__)
ILAB.add_local_periodic_task('Populating cache', populate_cache, minutes = 55)

if __name__ == '__main__':
    DEBUG = True
    import getpass, sys, pprint
    if len(sys.argv) == 2:
        auth_key = sys.argv[1]
    else:
        auth_key = getpass.getpass("Provide auth key: ")
    pprint.pprint(get_foreign_credentials('http://ilabs.cti.ac.at/iLabServiceBroker/', auth_key))
    configuration = json.dumps({
        'sb_url' : 'http://ilabs.cti.ac.at/iLabServiceBroker/',
        'authority_guid' : auth_key,
    })
    rlms = RLMS(configuration)
    print
    labs = rlms.get_laboratories()
    pprint.pprint(labs)
    print
    reservation_status = rlms.reserve(labs[0].laboratory_id, 'porduna', 'deusto', '', '', '', {})
    pprint.pprint(reservation_status)

    print 
    print "Translations:"
    print rlms.get_translations("Blackbody Radiation Lab")
    
    populate_cache(rlms)
