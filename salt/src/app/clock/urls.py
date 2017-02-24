from django.conf.urls import patterns, url

from clock.views import (ListEmployeesSearchView, ListSitesSearchView, DetailSiteView,
    UpdateEmployeeView, CreateEmployeeView, AlertListView, EntryListView, EntryUpdate, EntryNew,
    WriteupView, EntryDelete, ManageEmployeeView, ChangePasswordView)

urlpatterns = patterns('clock.views',
    url(r'^dashboard/$', 'dashboard', name='clock_dashboard'),
    url(r'^list/$', ListSitesSearchView(), name='clock_list_sites'),
    url(r'^list/(?P<pk>\d+)/$', DetailSiteView.as_view(), name='clock_detail_site'),
    url(r'^entries(?P<opt>\w*)/$', EntryListView.as_view(), name='clock_list_entries'),
    url(r'^entrie/(?P<opt>\w+)/(?P<pk>.*)/(?P<index>.*)/$', EntryDelete.as_view(), name='clock_delete_entrie'),
    url(r'^entrie/add(?P<opt>\w*)/(?P<pk>\d*)$', EntryNew.as_view(), name='clock_add_entrie'),
    url(r'^entrie/(?P<opt>\w\w)/(?P<pk>.*)/$', EntryUpdate.as_view(), name='clock_edit_entrie_list'),
    url(r'^entrie/(?P<pk>.*)/$', EntryUpdate.as_view(), name='clock_edit_entrie'),
    url(r'^writeup(?P<opt>\w*)/(?P<pk>.*)/$', WriteupView.as_view(), name='clock_edit_writeup'),
    url(r'^alerts/$', AlertListView.as_view(), name='clock_list_alerts'),
    url(r'^employees/$', ListEmployeesSearchView(), name='clock_list_employees'),
    url(r'^employees/add/$', CreateEmployeeView.as_view(), name='clock_create_employee'),
    url(r'^employees/pwd/(?P<user_id>\d+)/$', ChangePasswordView.as_view(), name='clock_change_password'),
    url(r'^employees/(?P<pk>\d+)/$', UpdateEmployeeView.as_view(), name='clock_form_employee'),
    url(r'^employees/(?P<opt>\w+)/$', ManageEmployeeView.as_view(), name='clock_manage_employee'),
    url(r'^report(?P<opt>.+)/$', 'report', name='clock_get_report'),
)
