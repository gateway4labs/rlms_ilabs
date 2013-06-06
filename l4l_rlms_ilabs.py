# -*-*- encoding: utf-8 -*-*-

import sys
import json
import datetime
import uuid
import hashlib

from flask.ext.wtf import TextField, PasswordField, Required, URL, ValidationError

from labmanager.forms import AddForm, RetrospectiveForm, GenericPermissionForm
from labmanager.data import Laboratory
from labmanager.rlms import register
from labmanager.rlms.base import BaseRLMS, BaseFormCreator

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
        super(UnrAddForm, self).__init__(*args, **kwargs)
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

class IlabsLmsPermissionForm(UnrPermissionForm, GenericPermissionForm):
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
        
        if self.login is None or self.password is None or self.url is None:
            raise Exception("Laboratory misconfigured: fields missing" )

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

    def reserve(self, laboratory_id, username, general_configuration_str, particular_configurations, request_payload, user_agent, origin_ip, referer):

        dtime = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

        random_str = uuid.uuid4()
        data       = "username=%(username)s&fullname=%(fullname)s&timestamp=%(timestamp)s&random=%(random)s" % {
            'username'  : username,
            'fullname'  : username,
            'timestamp' : dtime,
            'random'    : random_str,
        }
        crypted   = _rc4(data, self.password)
        data_hash = hashlib.new("md5", data).hexdigest()
        tpl       = '%(URL)s?id_instalacion=%(INSTALLATION)s&cadena=%(DATA)s&checksum=%(HASH)s'

        return tpl %  {
            'URL'          : self.url,
            'INSTALLATION' : self.login,
            'DATA'         : crypted.encode('hex'), 
            'HASH'         : data_hash,
        }


def _rc4(data, key):
    """
    Encrypts the data with key key using RC4. Based on the pseudocode presented in:

    Using the http://en.wikipedia.org/wiki/ARC4 
    """
    # The key-scheduling algorithm (KSA)
    S = range(256)
    j = 0
    for i in xrange(256):
        j = ( j + S[i] + ord(key[i % len(key)]) ) % 256

        S[i], S[j] = S[j], S[i]

    # The pseudo-random generation algorithm (PRGA)
    i = 0
    j = 0
    output = []

    for c in data:
        i = (i + 1) % 256
        j = (j + S[i]) % 256

        S[i], S[j] = S[j], S[i]

        k = ord(c) ^ S[ (S[i] + S[j]) % 256]
        output.append( chr(k) )

    return ''.join(output)


register("FCEIA-UNR", ['1.0'], __name__)

