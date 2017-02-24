from django.conf.urls import patterns, url, include

urlpatterns = patterns('django.contrib.auth.views',
    url(r'^login/$', 'login', {'template_name': 'profiles/login.html'}, name='profile_login'), 
    url(r'^logout/$', 'logout', {'next_page': '/'}, name='profile_logout'),
)
