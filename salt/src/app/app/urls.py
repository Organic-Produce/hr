from django.conf.urls import patterns, include, url
from django.conf import settings

from django.contrib import admin
from clock.views import AppDashboard
admin.autodiscover()

urlpatterns = patterns('',
     url(r'^clock/', include('clock.urls')),
     url(r'^api/', include('dataprep.urls')),
     url(r'^accounts/', include('profiles.urls')),
     url(r'^register/', include('register.urls')),
     url(r'^tax/', include('tax.urls')),
     url(r'^__plumbing__/', include(admin.site.urls)),
     url(r'^$', AppDashboard.as_view(), name='webapp_dashboard'),
)

