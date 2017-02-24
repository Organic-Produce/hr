from django.conf.urls import patterns, url
from django.views.generic import TemplateView
from registration.backends.default.views import ActivationView

from register.views import (DetailApplicantView, CreateApplicantView, DeleteApplicantView, ManageApplicantView,
        DetailTelephoneView, AddTelephoneView, DeleteTelephoneView,
        DetailJobView, AddJobView, DeleteJobView, DetailApplicantListView,
        DetailEducationView, AddEducationView, DeleteEducationView,
        DetailDocumentView, AddDocumentView, DeleteDocumentView, dashboard
        )

urlpatterns = patterns('register.views',
    url(r'^dashboard/$', 'dashboard', name='register_dashboard'),
    url(r'^applicant/add/$', CreateApplicantView.as_view(), name='register_create_applicant'),
    url(r'^applicant/activate/(?P<activation_key>.*)/$', ActivationView.as_view(), name='registration_activate'),
    url(r'^applicant/active/$', TemplateView.as_view(template_name = 'registration/activation_complete.html' ), name='registration_activation_complete'),
    url(r'^applicant/del/(?P<pk>\d+)/$', DeleteApplicantView.as_view(), name='register_delete_applicant'),
    url(r'^applicant/(?P<pk>\d+)/$', DetailApplicantView.as_view(), name='register_detail_applicant'),
    url(r'^applicant/(?P<pk>\d+)/(?P<ls>\w+)/$', DetailApplicantListView.as_view(), name='register_list_applicant'),
    url(r'^applicant/manage/(?P<pk>\d+)/$', ManageApplicantView.as_view(), name='register_manage_applicant'),
    url(r'^telephone/add/(?P<ap>\d+)/$', AddTelephoneView.as_view(), name='register_add_telephones'),
    url(r'^telephone/delete/(?P<pk>\d+)/$', DeleteTelephoneView.as_view(), name='register_delete_telephones'),
    url(r'^telephone/(?P<pk>\d+)/$', DetailTelephoneView.as_view(), name='register_detail_telephones'),
    url(r'^job/add/(?P<ap>\d+)/$', AddJobView.as_view(), name='register_add_job'),
    url(r'^job/delete/(?P<pk>\d+)/$', DeleteJobView.as_view(), name='register_delete_job'),
    url(r'^job/(?P<pk>\d+)/$', DetailJobView.as_view(), name='register_detail_job'),
    url(r'^education/add/(?P<ap>\d+)/$', AddEducationView.as_view(), name='register_add_education'),
    url(r'^education/delete/(?P<pk>\d+)/$', DeleteEducationView.as_view(), name='register_delete_education'),
    url(r'^education/(?P<pk>\d+)/$', DetailEducationView.as_view(), name='register_detail_education'),
    url(r'^document/add/(?P<ap>\d+)/$', AddDocumentView.as_view(), name='register_add_document'),
    url(r'^document/delete/(?P<pk>\d+)/$', DeleteDocumentView.as_view(), name='register_delete_document'),
    url(r'^document/(?P<pk>\d+)/$', DetailDocumentView.as_view(), name='register_detail_document'),
    url(r'^form/success/$', TemplateView.as_view(template_name = 'registration/form_success.html' ), name='register_form_success'),
)
