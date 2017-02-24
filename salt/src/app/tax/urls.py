from django.conf.urls import patterns, url

from tax.views import ( ListAffiliateSearchView, ListExpectedSearchView, 
    CreateClientView, QueueInView, CreateApplicantView, QueueStartView, QueueEndView, CreateExpectedView,
    )

urlpatterns = patterns('tax.views',
    url(r'^$', CreateClientView.as_view(), name='tax_identify_client'),
    url(r'^entrie/add/$', QueueInView.as_view(), name='tax_queuein'),
    url(r'^entrie/start/(?P<client_id>[\w-]+)/$', QueueStartView.as_view(), name='tax_start'),
    url(r'^entrie/end/(?P<client_id>[\w-]+)/$', QueueEndView.as_view(), name='tax_end'),
    url(r'^list/$', 'dashboard', name='tax_home'),
    url(r'^applicant/add/(?P<subclass>\w+)/$', CreateApplicantView.as_view(), name='tax_create_applicant'),
    url(r'^client/$', ListExpectedSearchView(), name='tax_list_expected'),
    url(r'^client/add/(?P<affiliate>\d+)/$', CreateExpectedView.as_view(), name='tax_create_expected'),
    url(r'^affiliate/$', ListAffiliateSearchView(), name='tax_list_affiliates'),
    url(r'^report(?P<opt>.+)/$', 'report', name='tax_get_report'),
)
