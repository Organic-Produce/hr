from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import ListView
from django.views.generic.edit import UpdateView, CreateView, DeleteView
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.contrib.sites.models import RequestSite
from django.http import HttpResponse

from haystack.views import SearchView
from haystack.forms import SearchForm
from haystack.query import SearchQuerySet
from registration.views import RegistrationView
from registration.models import RegistrationProfile

from gmapi import maps
from gmapi.forms.widgets import GoogleMap

from profiles.models import Applicant
from register.models import Telephone_number, Previous_Job, Education, Extra_document
from register.forms import Authentication, ApplicantForm, ManageFrom

from datetime import datetime, timedelta, time
import pytz

local = pytz.timezone("America/Chicago")

@login_required
def dashboard(request):
        if request.user.groups.filter(name='Reclutant'):
            context = {'applicants': Applicant.objects.all() }
            return render(request, 'registration/applicant_list.html', context )
        else:
            return reverse('register_detail_applicant', kwargs={'pk': request.user.pk})

class CreateApplicantView(RegistrationView):
    template_name = 'profiles/login.html'
    form_class = Authentication

    def post(self, request):
        from django.contrib.auth.views import login

        cleaned_data = request.POST 
        form = self.form_class(request.POST)

        if cleaned_data["login"] == "Login" :
            return login(self.request)

        elif form.is_valid() :
            username = cleaned_data["username"]
            password = cleaned_data["password"]
            applicant = Applicant.objects.create_user(username=username, password=password, email=username)
            applicant.is_active = False
            applicant.save()
            profile = RegistrationProfile.objects.create_profile(applicant)
            profile.send_activation_email(RequestSite(request))
            return render(request, 'registration/registration_complete.html')

        return self.get(request)

class DeleteApplicantView(DeleteView):
    model = Applicant
    def get_success_url(self) :
        return reverse('register_form_success')

class DetailApplicantView(UpdateView):
    model = Applicant
    form_class = ApplicantForm
    template_name = 'registration/applicant_form.html'
    #fields = ['first_name', 'last_name', 'birth_date', 'address', 'city', 'state', 'zip',
    #            'emergency_contact', 'marital_status', 'social_security', 'licence_number', 'licence_expiration', 'licence_state',
    #            'employment_type', 'salary', 'weekdays', 'weekends', 'first', 'second', 'third', 'criminal_record', 'criminal_note', 'resume']

    def get_success_url(self):
        return  reverse('register_detail_applicant', kwargs={'pk': self.get_object().id})

    def get_context_data(self, **kwargs):
        context = super(DetailApplicantView, self).get_context_data(**kwargs)
        applicant = self.get_object()

        if not self.request.user.groups.filter(name='Reclutant'):
            if self.request.user.id != self.get_object().id : context = {'message': 'Error'}
            if self.get_object().status != 1 :
                context = {'message': 'Your application has been submitted, you will be contacted by e-mail'} 
        context['action'] = reverse('register_detail_applicant',
                            kwargs={'pk': applicant.id})

        return context

    def form_valid(self, form):
        form.instance.applicant = Applicant.objects.get(pk=self.get_object().id)
        if self.request.POST.get("status") :
            form.instance.applicant.status = 2
            form.instance.applicant.save()
            return super(DetailApplicantView, self).get(self.request)
        return super(DetailApplicantView, self).form_valid(form)

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):

        return super(DetailApplicantView, self).dispatch(*args, **kwargs)

class DetailApplicantListView(UpdateView):
    model = Applicant
    template_name = 'registration/list_form.html'

    def get_context_data(self, **kwargs):
        context = super(DetailApplicantListView, self).get_context_data(**kwargs)
        applicant = self.get_object()
        list = {'telephones': applicant.telephones.all(), 'job': applicant.worked.all(), 'education': applicant.education.all(), 'document': applicant.documentation.all() }
        name = self.kwargs['ls']
	if name == 'all' :
		context['applicant'] = list
	else :
		context['list'] = list[name]
		context['name'] = name
        return  context

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):

        return super(DetailApplicantListView, self).dispatch(*args, **kwargs)

class DetailTelephoneView(UpdateView):
    model = Telephone_number
    fields = ['number','type']

    def get_success_url(self) :
        return reverse('register_form_success')

    def get_context_data(self, **kwargs):
        context = super(DetailTelephoneView, self).get_context_data(**kwargs)
        context['action'] = reverse('register_detail_telephones', kwargs={'pk': self.get_object().id})
        return context

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(DetailTelephoneView, self).dispatch(*args, **kwargs)

class AddTelephoneView(CreateView):
    model = Telephone_number
    fields = ['number','type']

    def get_success_url(self) :
        return reverse('register_form_success')

    def form_valid(self, form):
        form.instance.applicant = Applicant.objects.get(pk=self.request.user.id)
        return super(AddTelephoneView, self).form_valid(form)

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(AddTelephoneView, self).dispatch(*args, **kwargs)

class DeleteTelephoneView(DeleteView):
    model = Telephone_number
    def get_success_url(self) :
        return reverse('register_form_success')

class DetailJobView(UpdateView):
    model = Previous_Job
    fields = ['place','state','date_ended']

    def get_success_url(self) :
        return reverse('register_form_success')

    def get_context_data(self, **kwargs):
        context = super(DetailJobView, self).get_context_data(**kwargs)
        context['action'] = reverse('register_detail_job', kwargs={'pk': self.get_object().id})
        return context

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):

        return super(DetailJobView, self).dispatch(*args, **kwargs)

class AddJobView(CreateView):
    model = Previous_Job
    fields = ['place','state','date_ended']

    def get_success_url(self) :
        return reverse('register_form_success')

    def form_valid(self, form):
        form.instance.applicant = Applicant.objects.get(pk=self.request.user.id)
        return super(AddJobView, self).form_valid(form)

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):

        return super(AddJobView, self).dispatch(*args, **kwargs)

class DeleteJobView(DeleteView):
    model = Previous_Job
    def get_success_url(self) :
        return reverse('register_form_success')

class DetailEducationView(UpdateView):
    model = Education
    fields = ['place','year','state']

    def get_success_url(self):
        return reverse('register_form_success')

    def get_context_data(self, **kwargs):
        context = super(DetailEducationView, self).get_context_data(**kwargs)
        context['action'] = reverse('register_detail_education',
                            kwargs={'pk': self.get_object().id})

        return context

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):

        return super(DetailEducationView, self).dispatch(*args, **kwargs)

class AddEducationView(CreateView):
    model = Education
    fields = ['place','year','state']

    def get_success_url(self):
        return reverse('register_form_success')

    def form_valid(self, form):
        form.instance.applicant = Applicant.objects.get(pk=self.request.user.id)
        return super(AddEducationView, self).form_valid(form)

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):

        return super(AddEducationView, self).dispatch(*args, **kwargs)

class DeleteEducationView(DeleteView):
    model = Education

    def get_success_url(self):
        return reverse('register_form_success')

class DetailDocumentView(UpdateView):
    model = Extra_document
    fields = ['document','description']

    def get_success_url(self):
        return reverse('register_form_success')

    def get_context_data(self, **kwargs):
        context = super(DetailDocumentView, self).get_context_data(**kwargs)
        context['action'] = reverse('register_detail_document',
                            kwargs={'pk': self.get_object().id})

        return context

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):

        return super(DetailDocumentView, self).dispatch(*args, **kwargs)

class AddDocumentView(CreateView):
    model = Extra_document
    fields = ['document','description']

    def get_success_url(self):
        return reverse('register_form_success')

    def form_valid(self, form):
        form.instance.applicant = Applicant.objects.get(pk=self.request.user.id)
        return super(AddDocumentView, self).form_valid(form)

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):

        return super(AddDocumentView, self).dispatch(*args, **kwargs)

class DeleteDocumentView(DeleteView):
    model = Extra_document

    def get_success_url(self):
        return reverse('register_form_success')

class ManageApplicantView(UpdateView):
    model = Applicant
    form_class = ManageFrom
    template_name = 'registration/manage_form.html'

    def get_context_data(self, **kwargs):
        context = super(ManageApplicantView, self).get_context_data(**kwargs)
        applicant = self.get_object()
        list = {'telephones': applicant.telephones.all(), 'job': applicant.worked.all(), 'education': applicant.education.all(), 'document': applicant.documentation.all() }
        return  context

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):

        return super(ManageApplicantView, self).dispatch(*args, **kwargs)

