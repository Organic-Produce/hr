from django import forms
#import floppyforms as forms

class AffiliateForm(forms.Form):
    affiliate = forms.IntegerField(widget=forms.RadioSelect)
    client_id = forms.CharField(widget=forms.HiddenInput())
    social_security = forms.IntegerField(required=False)

class ExpectedForm(forms.Form):
    expected = forms.IntegerField()
    client_id = forms.CharField(widget=forms.HiddenInput())

class FinishForm(forms.Form):
    finished = forms.IntegerField()
    fees = forms.DecimalField(initial=0.00, max_digits=16, decimal_places=2, label=u'Fees')
    tax_federal = forms.DecimalField(initial=0.00, max_digits=16, decimal_places=2, label=u'Estimated tax federal return')
    tax_state = forms.DecimalField(initial=0.00, max_digits=16, decimal_places=2, label=u'Estimated tax state return')
    phone = forms.CharField(required=False) #PhoneNumberInput
    note = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 3 }))
    client_id = forms.CharField(widget=forms.HiddenInput())
    ID = forms.CharField(widget=forms.HiddenInput())

class ClientForm(forms.Form):
    first_name = forms.CharField()
    last_name = forms.CharField()
    social_security_number = forms.IntegerField(required=False)
