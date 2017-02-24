import floppyforms as forms
from clock.models import Site, Schedule
from profiles.models import Profile
from django.forms.models import inlineformset_factory
from datetime import timedelta, datetime
from gmapi.forms.widgets import Widget
from django.utils.translation import ugettext_lazy as _

ScheduleFormSet = inlineformset_factory(Site, Schedule)

class GMapWidget(forms.gis.BaseOsmWidget, forms.gis.PolygonWidget):
    pass

class SiteForm(forms.ModelForm):
    class Meta:
        model = Site
        widgets = {
            'location': GMapWidget
        }

class WriteupForm(forms.Form):
    text = forms.CharField(label=_("Text"), widget=forms.Textarea(attrs={
            'placeholder': _("Full text"), 'rows': 3 }))
    user_id = forms.IntegerField(widget=forms.HiddenInput())

class SignForm(forms.Form):
    password = forms.CharField(label=_("Password"), widget=forms.PasswordInput(render_value=False))

class TimesEntryForm(forms.Form):
    start = forms.TimeField(label=_("Start"), widget=forms.TimeInput(attrs={'placeholder': "hh:mm"}))
    end = forms.TimeField(label=_("End"), widget=forms.TimeInput(attrs={'placeholder': "hh:mm"}))
    start_full = forms.DateTimeField(widget=forms.HiddenInput())
    end_full = forms.DateTimeField(widget=forms.HiddenInput())
    ID = forms.CharField(widget=forms.HiddenInput())
    week = forms.CharField(widget=forms.HiddenInput())

    def clean(self):
        cleaned_data = super(TimesEntryForm, self).clean()
        start_time = cleaned_data.get("start")
        end_time = cleaned_data.get("end")
        delta = 3600 * (start_time.hour - end_time.hour) + 60 * (start_time.minute - end_time.minute) + (start_time.second - end_time.second)
        if delta >= 0 :
            self._errors["start"] = self.error_class(["Wrong times: start is after end for %d seconds" % delta])

        return cleaned_data

class TimesEntryNew(forms.Form):
    start = forms.TimeField(label=_("Start"), widget=forms.TimeInput(attrs={'placeholder': "hh:mm"}))
    end = forms.TimeField(label=_("End"), widget=forms.TimeInput(attrs={'placeholder': "hh:mm"}))
    user_id = forms.CharField(widget=forms.HiddenInput())
    ID = forms.CharField(required=False,widget=forms.HiddenInput())
    OID = forms.CharField(required=False,widget=forms.HiddenInput())
    start_date = forms.DateField(widget=forms.DateInput(attrs={'placeholder': "YYYY-MM-DD"}))
    end_date = forms.DateField(required=False,widget=forms.DateInput(attrs={'placeholder': "YYYY-MM-DD"}))
    note = forms.CharField(label=_("Note"), required=False,widget=forms.Textarea(attrs={
            'placeholder': "Full text", 'rows': 2 }))

    def clean(self):
        cleaned_data = super(TimesEntryNew, self).clean()
        start_time = cleaned_data.get("start")
        end_time = cleaned_data.get("end")
        start_date = cleaned_data.get("start_date")
        if cleaned_data.get("end_date") :
            end_date = cleaned_data.get("end_date")
        else :
            end_date = cleaned_data.get("start_date")
        start = datetime.combine(start_date,start_time)
        end = datetime.combine(end_date,end_time)
        if start - end > timedelta(minutes=0) :
            self._errors["start"] = self.error_class(["Wrong times: start is after end for %d seconds" % (start - end).total_seconds()])

        return cleaned_data

