from django.conf.urls import patterns, url
from rest_framework.urlpatterns import format_suffix_patterns
from rest_framework.authtoken.views import obtain_auth_token

urlpatterns = patterns('',
    url(r'^user/status/(?P<location_geo>\-?\d{0,3}\.?\d{0,15},?\-?\d{0,3}\.?\d{0,15})$', 'dataprep.views.user'),
    url(r'^entry/clockin/$', 'dataprep.views.checkin'),
    url(r'^entry/clockout/$', 'dataprep.views.checkout'),
    url(r'^entry/validate/$', 'dataprep.views.validate_entry'),
    url(r'^user/writeup/$', 'dataprep.views.writeup'),
    url(r'^user/history/$', 'dataprep.views.history'),
    url(r'^user/fence/$', 'dataprep.views.fence'),
    url(r'^user/token/', 'rest_framework.authtoken.views.obtain_auth_token' ),
    url(r'^user/setup/(?P<location_geo>\-?\d{0,3}\.?\d{0,15},?\-?\d{0,3}\.?\d{0,15})$', 'dataprep.views.setup'),
    url(r'^user/changepassword/$', 'dataprep.views.changepassword'),
)

urlpatterns = format_suffix_patterns(urlpatterns)
