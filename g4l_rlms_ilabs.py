# -*-*- encoding: utf-8 -*-*-

import sys
import json
import datetime
import uuid
import hashlib

from flask.ext.wtf import TextField, PasswordField, Required, URL, ValidationError

from labmanager.forms import AddForm, RetrospectiveForm, GenericPermissionForm
from labmanager.data import Laboratory
from labmanager.rlms import register, BaseRLMS, BaseFormCreator, Versions, Capabilities

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
        from launchilab1 import launchilab

        # You may want to use a different separator, such as @ or ::, depending on if that's a valid user.
        unique_user_id = '%s_%s' % (username, institution)

        url = launchilab(unique_user_id)

        return {
            'load_url' : url
        }


register("iLabs", ['1.0'], __name__)

