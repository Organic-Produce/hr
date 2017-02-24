import floppyforms as forms
from profiles.models import Applicant, STATE_CHOICES, MARITAL_CHOICES
from django.contrib.auth.forms import AuthenticationForm
from django.core.validators import validate_email

class Authentication(forms.Form):
    username = AuthenticationForm().fields["username"]
    password = AuthenticationForm().fields["password"]
    login = forms.CharField(widget=forms.HiddenInput())
    def clean(self):
        cleaned_data = super(Authentication, self).clean()
        user = cleaned_data.get("username")
        login = cleaned_data["login"]
        if Applicant.objects.filter(username=user) and login == "Register" :
            self._errors["login"] = self.error_class(["Your e-mail is already registred"])

        validate_email(user)

        return cleaned_data
    
class ApplicantForm(forms.ModelForm):
    class Meta:
        model = Applicant
        exclude = ('username', 'password', 'last_login', 'date_joined', 'pay_type', 'pay_period', 'geo_radius', 'geo_frecuency', 'email', 'status', 'note', 'employees',
                   'overtime', 'desired_accuracy', 'stationary_radius', 'distance_filter', 'location_timeout', 'IOS_config', 'is_active' )
    first_name = forms.CharField(max_length=30, required=False, label=u'First name')
    last_name = forms.CharField(max_length=30, required=False, label=u'Last name')
    email = forms.EmailField(max_length=75, required=False, label=u'Email address')
    salary = forms.DecimalField(initial=7.25, max_digits=16, decimal_places=2, label=u'Salary')
    birth_date = forms.DateField(initial=u'yyyy-mm-dd', label=u'Birth date')
    address = forms.CharField(max_length=512, label=u'Address')
    city = forms.CharField(max_length=256, label=u'City')
    state = forms.TypedChoiceField(initial=u'tx', choices=STATE_CHOICES, label=u'State')
    zip = forms.CharField(max_length=9, label=u'Zip')
    emergency_contact = forms.CharField(max_length=512, label=u'Emergency contact')
    marital_status = forms.TypedChoiceField(initial=u'si', choices=MARITAL_CHOICES, label=u'Marital status')
    social_security = forms.CharField(max_length=9, label=u'Social security')
    licence_number = forms.CharField(max_length=9, required=False, label=u'Licence number')
    licence_expiration = forms.DateField(required=False, label=u'Licence expiration')
    licence_state = forms.TypedChoiceField(initial=u'tx', choices=STATE_CHOICES, label=u'Licence state', required=False)
    weekdays = forms.BooleanField(required=False)
    weekends = forms.BooleanField(required=False)
    first = forms.BooleanField(required=False)
    second = forms.BooleanField(required=False)
    third = forms.BooleanField(required=False)
    criminal_record = forms.BooleanField(initial=False, required=False, label=u'Criminal record')
    criminal_note = forms.CharField(max_length=512, required=False, label=u'Criminal note')
    resume = forms.FileField(required=False)

class ManageFrom(forms.ModelForm):
    class Meta:
        model = Applicant
        exclude = ('username', 'password', 'last_login', 'date_joined', 'pay_type', 'pay_period', 'geo_radius', 'geo_frecuency', 'email', 'status', 'note', 'employees',
                   'overtime', 'desired_accuracy', 'stationary_radius', 'distance_filter', 'location_timeout', 'IOS_config', 'is_active' )
    appointment_date = forms.DateField(initial=u'yyyy-mm-dd', required=False)
    message_text = forms.CharField(max_length=512)
    application_verification = forms.FileField(required=False)
    policies_and_procedures = forms.FileField(required=False)
    sexual_arassment = forms.FileField(required=False)
    hostile_environment = forms.FileField(required=False)
    employee_agreement = forms.FileField(required=False)
    non_disclosure_agreements = forms.FileField(required=False)
    non_competes = forms.FileField(required=False)
    background_authorization_form = forms.FileField(required=False)
    handbook_acknowledgement_form = forms.FileField(required=False)
    direct_deposit_form = forms.FileField(required=False)
    EEOC_form = forms.FileField(required=False)
    HIPPA_form = forms.FileField(required=False)
