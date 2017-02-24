# -*- coding: utf-8 -*-
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.utils.decorators import method_decorator
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.generic import ListView
from django.views.generic.edit import UpdateView, CreateView, FormView
from django.core.urlresolvers import reverse
from django.conf import settings
from django.http import HttpResponse
from django import forms

from haystack.views import SearchView
from haystack.forms import SearchForm
from haystack.query import SearchQuerySet
from rest_framework.authtoken.models import Token

from gmapi import maps
from gmapi.forms.widgets import GoogleMap

from profiles.models import Profile, Applicant
from clock.models import Site, Schedule, Instance
from clock.forms import SiteForm, TimesEntryForm, WriteupForm, SignForm, TimesEntryNew
from clock.templatetags.dicgetatt import stripdecimal
from dataprep.views import setup, user, checkin, checkout, validate_entry, writeup, message
from django.utils.translation import ugettext_lazy as _

from datetime import datetime, timedelta, time
import pytz
import elasticsearch

es_host = settings.ELASTICSEARCH_HOST
local = pytz.timezone("America/Chicago")
ES_INDICES = '2016-4*,2016-5*,2017-*'

class MapForm(forms.Form):
    map = forms.Field(widget=GoogleMap(attrs={'width':500, 'height':300}))

def is_manager(user):
    if user.groups.filter(name__contains='Manager'):
        return True
    return False

def week_ending(instance='Fernic',date=datetime.today()):
    fin = date
    fin -= timedelta(days=fin.weekday())
    if instance == 'monthly' : fin -= timedelta(days=4)
    if instance == 'biweekly' : fin -= timedelta(days=2)
    hours = local.localize(datetime.combine(fin, time(0,0,0, tzinfo=None)), is_dst=None).astimezone(pytz.utc)
    return hours

def worked_total(week=[]):
    worked = timedelta(minutes=0)
    for entry in week:
        worked += entry['delta']
    worked = (worked.total_seconds())/3600
    extra = 0
    if worked > 40 :
        extra = worked-40
        worked = 40
    return [worked,extra]

def entry_format(entry):
    entry['_source']['user'] = Profile.objects.get(pk=entry['_source']['user_id'])
    if entry['_source']['location_id'] and not entry['_source'].get('site_name'):
        entry['_source']['site_name'] = Site.objects.get(pk=entry['_source']['location_id'])
    entry['delta'] = datetime.now() - stripdecimal(entry['_source']['start'])
    if entry['_source'].get('end'): entry['delta'] = stripdecimal(entry['_source']['end'])-stripdecimal(entry['_source']['start'])
    if entry['_source'].get('note') :
        entry['note'] = True
        start = pytz.utc.localize(stripdecimal(entry['_source'].get('end')), is_dst=None).astimezone (local)
        entry['start'] = start.date()
    return entry

def entries_by_week(user_id=[193],instance='Fernic',stat=5,hist=6):
    es = elasticsearch.Elasticsearch(es_host)
    status = '{"not": {"term": {"status": %d}}}' % stat
    employees = '{"terms": {"user_id": %s }}' % user_id.__repr__()
    sort = '"sort": {"start": {"order":"desc"}}'
    weeks = []
    week_end = week_ending(instance, datetime.today())
    range = '{ "range" : { "start" : { "gte" : "%s"} } }' % week_end.isoformat()
    query='{"size" : 100,"query": {"filtered":{"filter": {"and" : [%s,%s,%s] }}},%s}' % (range,status,employees,sort)
    week = es.search(index=ES_INDICES, body=query).get('hits')
    for entry in week.get('hits'):
        entry = entry_format(entry)
    weeks.append([(week_end+timedelta(days=7)-timedelta(days=1)).date(),week_end.date(),worked_total(week.get('hits')),week.get('hits')])
    history = 0
    while history < hist :
        range1 = '{ "range" : { "start" : { "lte" : "%s"} } }' % (week_end-timedelta(days=7*history)).isoformat()
        history += 1
        range2 = '{ "range" : { "start" : { "gte" : "%s"} } }' % (week_end-timedelta(days=7*history)).isoformat()
        query='{"size" : 100,"query": {"filtered":{"filter": {"and" : [%s,%s,%s,%s] }}},%s}' % (range1,range2,status,employees,sort)
        week = es.search(index=ES_INDICES, body=query).get('hits')
        for entry in week.get('hits'):
            entry = entry_format(entry)
        weeks.append([(week_end-timedelta(days=7*(history-1))-timedelta(days=1)).date(),(week_end-timedelta(days=7*history)).date(),worked_total(week.get('hits')),week.get('hits')])
        if week.get('total') == 0 :
            weeks.pop()
    return weeks

@login_required
def dashboard(request):
    if request.get_host() in [inst.url.split('/')[2] for inst in Instance.objects.all()] :
        if not request.user.instances[0].name.lower() in request.get_host(): 
            request.error = 'Wrong server!'
            return redirect(reverse('profile_logout'))

    if request.user.groups.filter(name='Tax Manager'):
            return redirect(reverse('tax_home'))

    if not is_manager(request.user):
        if request.user.groups.filter(name='Reclutant'):
            context = {'applicants': Applicant.objects.all() }
            return render(request, 'registration/applicant_list.html', context )
        else:
            return redirect(reverse('webapp_dashboard'))

    es = elasticsearch.Elasticsearch(es_host)
    decl_term = '{"term": {"status": %d }}' % 3
    force_term = '{"terms": {"status": [%d,%d] }}' % (6,7)
    employees = '{"terms": {"user_id": %s }}' % request.user.employee_pk_list.__repr__()
    sort = '"sort": {"start": {"order":"desc"}}'
    decl_query='{"size" : 100,"query": {"filtered":{"filter": {"and" : [%s,%s] }}},%s}' % (decl_term,employees,sort)
    force_query='{"size" : 100,"query": {"filtered":{"filter": {"and" : [%s,%s] }}},%s}' % (force_term,employees,sort)
    declined = es.search(index=ES_INDICES, body=decl_query)
    declined = declined['hits']
    forced = es.search(index=ES_INDICES, body=force_query)
    forced = forced['hits']
    if request.user.instances[0].manager_messages :
        mesg_term = '{"term": {"type": %d }}' % 9
        msort = '"sort": {"time": {"order":"desc"}}'
        mesg_query='{"size" : 100,"query": {"filtered":{"filter": {"and" : [%s,%s] }}},%s}' % (mesg_term,employees,msort)
        messages = es.search(index='alerts', body=mesg_query)
        messages = messages['hits']
    else:
        messages = { 'total': 0 }
    OPCIONES = { 'mapTypeId': maps.MapTypeId.ROADMAP, 'mapTypeControlOptions': { 'style': maps.MapTypeControlStyle.DROPDOWN_MENU } }
    if request.user.instances[0].site.state in ['df', 'mo'] :
        center = maps.LatLng(19.43, -99.13)
        zoom = 10
    else :
        center = maps.LatLng(32.82, -96.73)
        zoom = 8
    OPCIONES.update({ 'center': center , 'zoom': zoom })
    gmap = maps.Map(opts = OPCIONES)

    for employee in SearchQuerySet().models(Profile).order_by('last_name').filter(id__in=request.user.employee_pk_list):
     if employee.last_location:
        last_location = employee.last_location
        marker = maps.Marker(opts = {
            'map': gmap,
            'position': maps.LatLng(last_location.y,last_location.x),
            'color': 'blue',
            'size': 'small',
            'icon': '/static/blue-dot.png'
        })
        maps.event.addListener(marker, 'mouseover', 'myobj.markerOver')
        maps.event.addListener(marker, 'mouseout', 'myobj.markerOut')
        info = maps.InfoWindow({
            'content': employee.last_name+', '+employee.first_name+'<br>'+pytz.utc.localize(employee.last_time, is_dst=None).astimezone (local).__str__() ,
            'disableAutoPan': True
        })
        info.open(gmap, marker)

    site_count = 1

    if request.user.instances[0].multi_site :
            site_count = request.user.instances[0].branch_list.split(',').__len__()

    context = {'form': MapForm(initial={'map': gmap}), 'declined' : declined, 'forced': forced, 'sites_count': site_count, 'messages': messages }
    
    if 'report' in request.path :
        context['errors'] = request.error

    return render(request, 'clock/dashboard.html', context )

class DetailSiteView(UpdateView):
    model = Site
    template_name = 'clock/site_form.html'
    form_class = SiteForm

    def get_context_data(self, *args, **kwargs):

        context = super(DetailSiteView, self).get_context_data(*args, **kwargs)

        if len(self.request.GET):
            data = self.request.GET
            if data.get('l') :
                list = data['l'].split(",")
                item = list.index(self.get_object().id.__str__())
                if item != 0 :
                    context['previous'] = list[item-1]
                    context['prev_site'] = Site.objects.get(id=list[item-1]).name
                if item != list.__len__()-1 :
                    context['next'] = list[item+1] 
                    context['next_site'] = Site.objects.get(id=list[item+1]).name
                context['list'] = data['l']

            if data.get('square'):
                loc = data.get('square')
                from utils.poligoning import encuadra
                encuadra(self.get_object(),loc)

        return context

    def get_success_url(self):
        return self.request.get_full_path()

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        if not is_manager(self.request.user):
            return redirect(reverse('webapp_dashboard'))

        return super(DetailSiteView, self).dispatch(*args, **kwargs)

class WriteupView(FormView):
    def get_template(self):
        if self.request.user.instances[0].iframes :
            return 'clock/skel_writeup.html'
        else:
            return 'clock/writeup.html'
    form_class = WriteupForm

    def get(self, request, **kwargs):
        user_id = self.kwargs['pk']
        options = self.kwargs['opt']
        employee = Profile.objects.get(pk=user_id)

        memo = False
        if options == 'm' :
            memo = True
            data = { 'user_id': 0 }
        else : data = { 'user_id': user_id }
        form = self.form_class(initial=data)

        return render(request, self.get_template(), {'employee': employee.get_full_name(), 'form': form, 'memo': memo})

    def post(self, request, **kwargs):
        es = elasticsearch.Elasticsearch(es_host)
        options = self.kwargs['opt']
        doc = {}
        doc['text'] = request.POST.get('text')
        doc['time'] = datetime.now()
        if options == 'm' : 
            doc['type'] = 10
            for employee in self.request.user.employees.all() :
                doc['user_id'] = employee.id
                es.index(index='alerts', doc_type='alert_entry', body=doc)
            return redirect(reverse('clock_list_employees'))

        else : 
            doc['user_id'] = request.POST.get('user_id')
            doc['type'] = 0

        if not self.request.user.employees.filter(id=doc['user_id']):
            return redirect(reverse('webapp_dashboard'))

        es.index(index='alerts', doc_type='alert_entry', body=doc)

        return redirect(reverse('clock_form_employee',args=(doc['user_id'],)))

    @method_decorator(login_required)                                                                                                                                          
    def dispatch(self, *args, **kwargs):                                                                                                                                       
        if not is_manager(self.request.user):
            return redirect(reverse('webapp_dashboard'))

        return super(WriteupView, self).dispatch(*args, **kwargs)

class EntryDelete(FormView):
    es = elasticsearch.Elasticsearch(es_host)

    def get(self, request, **kwargs):
        if not is_manager(self.request.user):
            return redirect(reverse('webapp_dashboard'))

        ID = self.kwargs['pk']
        index = self.kwargs['index']

        doc = self.es.get(index=index,id=ID)['_source']
        entry_type = 'clock_entry'

        if self.kwargs['opt'] == 'force' :
            doc['status'] = 6
            doc['ID'] = ID
            doc['end'] = datetime.now()
        elif self.kwargs['opt'] == 'approve' :
            doc['type'] = 8
            entry_type = 'alert_entry'
        elif self.kwargs['opt'] == 'decline' :
            doc['type'] = 7
            entry_type = 'alert_entry'
        else :
            doc['status'] = 5

        self.es.index(index, entry_type, doc, id=ID)
        return redirect(reverse('clock_form_employee',args=(doc['user_id'],)))

    @method_decorator(login_required)                                                                                                                                          
    def dispatch(self, *args, **kwargs):                                                                                                                                       
        return super(EntryDelete, self).dispatch(*args, **kwargs)

class EntryUpdate(FormView):
    def get_template_names(self):
        if self.request.user.instances[0].iframes :
            return 'clock/skel_entry.html'
        else:
            return 'clock/entry.html'
    es = elasticsearch.Elasticsearch(es_host)
    form_class = TimesEntryForm

    def get_context_data(self, **kwargs):

        context = super(EntryUpdate, self).get_context_data(**kwargs)

        if 'form' in context:
            context['date'] = context['form'].cleaned_data['start_full'].date()
            return context

        ID = context['pk']
        
        term = '{"term": {"_id": "%s" }}' %ID
        query='{"size" : 10,"query": {"filtered":{"filter": %s }}}' % (term)
        entry = self.es.search(index=ES_INDICES, body=query)
        entry_source = entry['hits']['hits'][0]
        entry = entry_source['_source']
        start_utc = stripdecimal(entry['start'])
        start = pytz.utc.localize(start_utc, is_dst=None).astimezone (local)
        end_utc = stripdecimal(entry['end'])
        end = pytz.utc.localize(end_utc, is_dst=None).astimezone (local)
        employee = Profile.objects.get(pk=entry['user_id'])

        data = { 'start': start.time(), 'end': end.time(),
                'start_full': datetime.combine(start.date(),start.time()),
                'end_full':  datetime.combine(end.date(),end.time()),
                'ID': entry_source['_id'], 'week': entry_source['_index'], 'user_id': employee.pk }
        form = TimesEntryForm(initial=data)
        context['employee'] = employee.get_full_name()
        context['form'] = form
        context['date'] = start.date()

        return context

    def get(self, request, *args, **kwargs):
        return self.render_to_response(self.get_context_data(*args, **kwargs))

    def form_valid(self, form):
        start_posted = form.cleaned_data["start"]
        end_posted = form.cleaned_data["end"]

        ID = form.cleaned_data["ID"]
        start_ori = local.localize(form.cleaned_data["start_full"], is_dst=None)
        start_posted = datetime.combine(start_ori.date(),start_posted)
        local_start = local.localize(start_posted, is_dst=None)
        utc_start = local_start.astimezone(pytz.utc)
        end_ori = local.localize(form.cleaned_data["end_full"], is_dst=None)
        end_posted = datetime.combine(end_ori.date(),end_posted)
        local_end = local.localize(end_posted, is_dst=None)
        utc_end = local_end.astimezone(pytz.utc)

        index = form.cleaned_data["week"]
        doc = self.es.get(index=index, id=ID)
        doc = doc['_source']
        changed = False

        redir = redirect(reverse('clock_form_employee',args=(doc['user_id'],)))
        if self.kwargs.get('opt'):
            if doc['status'] == 6 or doc['status'] == 7 :
                redir = redirect(reverse('clock_list_entries',args=('f',)))
            else :
                redir = redirect(reverse('clock_list_entries',args=('',)))

        if not utc_start.time() == start_ori.time() :
            doc['start'] = utc_start
            doc['status'] = 2
            changed = True

        if not utc_end.time() == end_ori.time() :
            doc['end'] = utc_end
            doc['status'] = 2
            changed = True

        if changed : self.es.index(index, 'clock_entry', doc, id=ID)

        return redir

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        if not is_manager(self.request.user):
            return redirect(reverse('webapp_dashboard'))

        return super(EntryUpdate, self).dispatch(*args, **kwargs)

class EntryNew(FormView):
    def get_template_names(self):
        if self.request.user.instances[0].iframes :
            return 'clock/skel_entry.html'
        else:
            return 'clock/entry.html'
    es = elasticsearch.Elasticsearch(es_host)
    form_class = TimesEntryNew

    def get_context_data(self, **kwargs):

        context = super(EntryNew, self).get_context_data(**kwargs)
        user_id = self.kwargs['pk']
        options = self.kwargs['opt']
        employee = Profile.objects.get(pk=user_id)
        context['employee'] = employee

        if 'form' in context:
            return context

        user_id = int(context['pk'])
        employee = Profile.objects.get(pk=user_id)
        form = TimesEntryNew(initial={'user_id': user_id})
        context['form'] = form
        context['employee'] = employee
        if options == 'note' :
            context['note'] = True
        return context

    def get(self, request, *args, **kwargs):
        if not self.request.user.employees.filter(id=self.kwargs['pk']):
            return redirect(reverse('webapp_dashboard'))

        return self.render_to_response(self.get_context_data(*args, **kwargs))

    def form_valid(self, form):
        if not self.request.user.employees.filter(id=self.kwargs['pk']):
            return redirect(reverse('webapp_dashboard'))

        start_posted = form.cleaned_data["start"]
        end_posted = form.cleaned_data["end"]

        user_id = form.cleaned_data["user_id"]
        employee = Profile.objects.get(pk=user_id)
        start_date_posted = form.cleaned_data["start_date"]
        start_full_posted = datetime.combine(start_date_posted,start_posted)
        start_full_local = local.localize(start_full_posted, is_dst=None)
        utc_start = start_full_local.astimezone(pytz.utc)
        if form.cleaned_data["end_date"] : 
            end_date_posted = form.cleaned_data["end_date"]
        else :
            end_date_posted = form.cleaned_data["start_date"]
        end_full_posted = datetime.combine(end_date_posted,end_posted)
        end_full_local = local.localize(end_full_posted, is_dst=None)
        utc_end = end_full_local.astimezone(pytz.utc)
        week = datetime.now().strftime('%Y-%U')
        doc = {'start':utc_start , 'end': utc_end,
                    'user_id': user_id, 'status': 2, 'location_id': employee.sites.first().id }
        if form.cleaned_data["note"] : doc.update({'note': form.cleaned_data["note"]})
        new_entry = self.es.index(index=week, doc_type='clock_entry', body=doc)
        doc['ID'] = new_entry['_id']
        self.es.index(week, 'clock_entry', doc, id=doc['ID'])

        if form.cleaned_data["OID"] == "Save and add more" :
            return redirect(reverse('clock_add_entrie', kwargs={'pk': user_id, 'opt':''}))
        return redirect(reverse('clock_form_employee', args=(user_id,)))

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        if not is_manager(self.request.user):
            return redirect(reverse('webapp_dashboard'))

        return super(EntryNew, self).dispatch(*args, **kwargs)

class EntryListView(ListView):

    template_name = 'clock/list_entries.html'

    def get_queryset(self):
        
        profile = SearchQuerySet().models(Profile).filter(id='profiles.profile.%s' % self.request.user.pk)

        es = elasticsearch.Elasticsearch(es_host)

        sort = '"sort": {"start": {"order":"desc"}}'
        messages = { 'total': 0 }

        if is_manager(self.request.user):
            if self.kwargs['opt'] == 'm' and self.request.user.instances[0].manager_messages :
                employees = '{"terms": {"user_id": %s }}' % self.request.user.employee_pk_list.__repr__()
                mesg_term = '{"term": {"type": %d }}' % 9
                msort = '"sort": {"time": {"order":"desc"}}'
                mesg_query='{"size" : 100,"query": {"filtered":{"filter": {"and" : [%s,%s] }}},%s}' % (mesg_term,employees,msort)
                messages = es.search(index='alerts', body=mesg_query)
                messages = messages['hits']
            if self.kwargs['opt'] == 'f' :
                status = '{"terms": {"status": [%d,%d] }}' % (6,7)
            else :
                status = '{"term": {"status": %d}}' % 3
            term = '{"terms": {"user_id": %s}}' % self.request.user.employee_pk_list.__repr__()
            query='{"size" : 200,"query": {"filtered":{"filter": {"and" : [%s,%s] }}},%s}' % (term,status,sort)
            entries = es.search(index=ES_INDICES, body=query).get('hits').get('hits')
            for entry in entries:
                employee = Profile.objects.get(pk=entry['_source']['user_id'])
                entry['_source']['user'] = employee.get_full_name()
                if not entry['_source'].get('site_name') and entry['_source']['location_id'] :
                    entry['_source']['site_name'] = Site.objects.get(pk=entry['_source']['location_id'])
                entry['delta'] = datetime.now() - stripdecimal(entry['_source']['start'])
                if entry['_source'].get('end'): entry['delta'] = stripdecimal(entry['_source']['end'])-stripdecimal(entry['_source']['start'])
        else:
            #if self.request.user.groups.filter(name__in=['PPI Employee']):
            #    if self.request.user.pay_period == 3 :
            #        entries = entries_by_week([self.request.user.pk],'monthly') 
            #    else :
            #        entries = entries_by_week([self.request.user.pk],'biweekly') 
            #else :
                entries = entries_by_week([self.request.user.pk])

        setattr(profile[0], 'entries', entries)
        setattr(profile[0], 'messages', messages)
        setattr(profile[0], 'is_manager', is_manager(self.request.user))

        return profile

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):

        return super(EntryListView, self).dispatch(*args, **kwargs)

class AlertListView(ListView):
    template_name = 'clock/list_alerts.html'

    def get_queryset(self):
        profiles = SearchQuerySet().models(Profile)
        profile = profiles.filter(id='profiles.profile.%s' % self.request.user.pk)
        es = elasticsearch.Elasticsearch(es_host)
        term = '{"terms": {"user_id": %s}}' % self.request.user.employee_pk_list.__repr__()
        sort = '"sort": {"date": {"order":"desc", "ignore_unmapped" : true }}'
        query='{"size" : 100,"query": {"filtered": {"filter": %s }},%s}' % (term,sort)
        alerts = es.search(index='alerts', body=query)

        setattr(profile[0], 'alerts', alerts)

        return profile

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        if not is_manager(self.request.user):
            return redirect(reverse('webapp_dashboard'))

        return super(AlertListView, self).dispatch(*args, **kwargs)

class GenericSearchView(SearchView):
    @method_decorator(login_required)
    def __call__(self, *args, **kwargs):
        return super(GenericSearchView, self).__call__(*args, **kwargs)

    def extra_context(self):
        return {
            'request': self.request
        }

class ListSitesSearchForm(SearchForm):
    def no_query_found(self):
        return self.searchqueryset.models(Site).all()

class ListSitesSearchView(GenericSearchView):
    def __init__(self, *args, **kwargs):
        if kwargs.get('template') is None:
            kwargs['template'] = 'clock/list_sites.html'

        if kwargs.get('form_class') is None:
            kwargs['form_class'] = ListSitesSearchForm

        super(ListSitesSearchView, self).__init__(*args, **kwargs)

    def build_form(self, form_kwargs=None):
        data = None
        kwargs = {'load_all': self.load_all}

        if form_kwargs: kwargs.update(form_kwargs)

        query_set = SearchQuerySet().models(Site).order_by('name')
        if self.request.user.instances[0].multi_site :
            query_set = query_set.filter(id__in=self.request.user.instances[0].branch_list.split(','))
        else :
            query_set = query_set.filter(id=self.request.user.instances[0].site.id)
        if len(self.request.GET):
            data = self.request.GET
            if data.get('q') :
                query_set = query_set.filter(text__icontains=data.get('q'))

        kwargs['searchqueryset'] = query_set

        return self.form_class(data, **kwargs)

    def __name__(self):
        return 'ListSitesSearchView'

class ListEmployeesSearchForm(SearchForm):
    def no_query_found(self):
        return self.searchqueryset.models(Profile).all()

class ListEmployeesSearchView(GenericSearchView):
    def get_template(self): 
            return 'clock/list_employees.html'

    def __init__(self, *args, **kwargs):
        if kwargs.get('template') is None:
            kwargs['template'] = self.get_template()

        if kwargs.get('form_class') is None:
            kwargs['form_class'] = ListEmployeesSearchForm

        super(ListEmployeesSearchView, self).__init__(*args, **kwargs)

    def build_form(self, form_kwargs=None):
        data = None
        kwargs = {'load_all': self.load_all}

        if form_kwargs: kwargs.update(form_kwargs)
        qs = SearchQuerySet().models(Profile).order_by('last_name')
        if len(self.request.GET):
            data = self.request.GET
            if data.get('r') :
                group = Group.objects.get(name=self.request.user.instances[0].name+' Employee')
                for employee in qs.all():
                    if employee.object.is_active : qs = qs.exclude(id=employee.pk)
                    if group not in employee.object.groups.all() : qs = qs.exclude(id=employee.pk)
            else :
                qs = qs.filter(id__in=self.request.user.employee_pk_list)
            if data.get('q') :
                kwargs['searchqueryset'] = qs.filter(text__icontains=data.get('q'))
        else :
            qs = qs.filter(id__in=self.request.user.employee_pk_list)

        kwargs['searchqueryset'] = qs

        return self.form_class(data, **kwargs)

    def __name__(self):
        return 'ListEmployeesSearchView'

class ChangePasswordView(CreateView):
    model = Profile
    def get_template_names(self):
        if self.request.user.instances[0].iframes :
            return 'clock/skel_employee_manage.html'
        else:
            return 'clock/employee_manage.html'
    fields = ['password',]

    def get_context_data(self, **kwargs):
        user_id = self.kwargs['user_id']
        context = super(ChangePasswordView, self).get_context_data(**kwargs)
        context['action'] = reverse('clock_change_password', kwargs={'user_id': user_id})
        context['employee'] = Profile.objects.get(pk=user_id).get_full_name()
        
        return context

    def form_valid(self, form):
        user_id = int(self.kwargs['user_id'])
        employee = Profile.objects.get(pk=user_id)
        employee.set_password(form.cleaned_data['password'])

        employee.save()

        return redirect(reverse('clock_form_employee', kwargs={'pk': user_id}))

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        if not is_manager(self.request.user) or not self.request.user.employees.filter(id=self.kwargs['user_id']):
            return redirect(reverse('webapp_dashboard'))

        return super(ChangePasswordView, self).dispatch(*args, **kwargs)

class ManageEmployeeView(CreateView):
    model = Profile
    def get_template_names(self):
        if self.request.user.instances[0].iframes :
            return 'clock/skel_employee_manage.html'
        else:
            return 'clock/employee_manage.html'
    fields = ['employees',]

    def get_context_data(self, **kwargs):

        context = super(ManageEmployeeView, self).get_context_data(**kwargs)
        context['action'] = reverse('clock_manage_employee', kwargs={'opt': 'manage'})
        if self.request.user.instances[0].multi_manager :
            employees = Profile.objects.filter(groups__name=self.request.user.instances[0].name+' Employee')
            for employee in employees.all():
                if employee.employer_count > 1 : employees = employees.exclude(id=employee.id)
        else:
            employees = []
        nform = context['form']
        nform.fields["employees"].queryset = employees
        context['form'] = nform

        return context

    def form_valid(self, form):

        for employee in form.cleaned_data['employees']:

            if self.kwargs['opt'] == 'deactivate' :
                employee.employers.clear()
                employee.is_active = False
                employee.save()

            elif self.kwargs['opt'] == 'reactivate' :
                employee.employers.add(self.request.user.id)
                employee.is_active = True
                manager = self.request.user.instances[0].admin
                employee.employers.add(manager)
                employee.save()

            else :
                if self.kwargs['opt'] == 'unmanage' :
                    self.request.user.employees.remove(employee)
                else :
                    self.request.user.employees.add(employee)

        if self.kwargs['opt'] != 'deactivate' :
            self.request.user.save()

        if self.request.user.instances[0].iframes and (self.kwargs['opt'] == 'unmanage' or self.kwargs['opt'] == 'deactivate'):
            return redirect('/static/select.html')
        elif self.kwargs['opt'] == 'reactivate':
            return redirect(reverse('clock_form_employee',args=(employee.pk,)))

        return redirect(reverse('clock_list_employees'))

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        if not is_manager(self.request.user):
            return redirect(reverse('webapp_dashboard'))

        return super(ManageEmployeeView, self).dispatch(*args, **kwargs)

class CreateEmployeeView(CreateView):
    model = Profile
    template_name = 'clock/employee_add.html'
    fields = ['username', 'first_name', 'last_name', 'password', 'employees', 'email', 'employment_type', 'geo_radius'] 
    configurable_fields = ['pay_type', 'overtime', 'salary', 'pay_period', 'geo_frecuency'] 
    fields += configurable_fields
    # 'desired_accuracy', 'stationary_radius', 'distance_filter', 'location_timeout', 'IOS_config' ]

    def get_success_url(self):
        return reverse('clock_list_employees')

    def get_context_data(self, **kwargs):

        context = super(CreateEmployeeView, self).get_context_data(**kwargs)
        context['action'] = reverse('clock_create_employee')
        nform = context['form']
        hidden_fields = [field for field in self.configurable_fields if field not in self.request.user.instances[0].user_configs]
        for field in hidden_fields : 
            nform.fields[field].widget.attrs['hidden'] = True
            nform.fields[field].label = ''
            nform.fields[field].help_text = ''

        nform.fields["employees"].initial = [self.request.user]
        nform.fields["employees"].queryset = self.request.user.groups.all().first().user_set.all()
        if self.request.user.instances[0].multi_manager :
                nform.fields["employees"].label = _('Managers')
                nform.fields["employees"].initial.append(self.request.user.instances[0].admin)
        else :
            nform.fields["employees"].label = ''
            nform.fields["employees"].widget.attrs['hidden'] = True
            nform.fields["employees"].help_text = ''
        context['form'] = nform

        return context

    def form_valid(self, form):

        username = form.cleaned_data["username"]
        first_name = form.cleaned_data["first_name"]
        last_name = form.cleaned_data["last_name"]
        password = form.cleaned_data["password"]
        email = form.cleaned_data["email"]

        pf = Profile.objects.create_user(username=username, first_name=first_name, last_name=last_name, password=password, email=email)

        extra_fields = ['employment_type', 'geo_radius', ] 
        extra_fields += self.request.user.instances[0].user_configs

        for field in extra_fields : 
            pf.__setattr__(field,form.cleaned_data[field])

        generic = self.request.user.instances[0].site

        pf.groups.add(Group.objects.get(name=self.request.user.instances[0].name+' Employee'))
        instance_manager = self.request.user.instances[0].admin

        pf.save()

        sch = Schedule.objects.create(site=generic, worker=pf)
        generic.save()

        instance_manager.employees.add(pf)
        instance_manager.save()
        for manager in form.cleaned_data['employees']:
            if manager != instance_manager :
                manager.employees.add(pf)
                manager.save()

        return redirect(self.get_success_url())

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        if not is_manager(self.request.user):
            return redirect(reverse('webapp_dashboard'))

        return super(CreateEmployeeView, self).dispatch(*args, **kwargs)

class UpdateEmployeeView(UpdateView):
    model = Profile
    def get_template_names(self):
        if self.request.user.instances[0].iframes :
            return 'clock/skel_employee_form.html'
        else:
            return 'clock/employee_form.html'
    fields = ['first_name', 'last_name', 'email', 'employment_type', 'geo_radius', 'employees', ]
    configurable_fields = ['pay_type', 'overtime', 'salary', 'pay_period', 'geo_frecuency'] 
    fields += configurable_fields

    def get_success_url(self):
        if self.request.user.instances[0].iframes :
            return reverse('clock_form_employee', kwargs={'pk': self.get_object().id})
        return reverse('clock_list_employees')

    def get_object(self, queryset=None):
        obj = super(UpdateEmployeeView, self).get_object(queryset)
        if obj.is_active and not obj.employers.filter(id=self.request.user.id) : return None
        if self.request.user.instances[0].multi_manager and self.request.user == self.request.user.instances[0].admin :
            obj.employees = obj.employers.all()
        return obj
        
    def get_context_data(self, **kwargs):

        context = super(UpdateEmployeeView, self).get_context_data(**kwargs)
        nform = context['form']
        object = context['object']
        if self.request.user.instances[0].multi_manager and self.request.user == self.request.user.instances[0].admin : 
            nform.fields["employees"].queryset = self.request.user.groups.all().first().user_set.all().exclude(id=self.request.user.id)
            nform.fields["employees"].label = _('Managers')
            object.employees.clear()

        if not self.request.user.employees.filter(id=object.id) and object.is_active == True : return None

        if object.groups.filter(name__in=['PPI Employee']):
            if object.pay_period == 3 :
                wentries = entries_by_week([object.id],'monthly') 
            else :
                wentries = entries_by_week([object.id],'biweekly') 
        else :
            wentries = entries_by_week([object.id],hist=12)

        es = elasticsearch.Elasticsearch(es_host)
        employees = '{"term": {"user_id": %d }}' % object.id
        term = '{"terms": {"type": [%d,%d] }}' % (0,6)
        sort = '"sort": {"time": {"order":"desc"}}'
        query='{"size" : 100,"query": {"filtered":{"filter": {"and" : [%s,%s] }}},%s}' % (term,employees,sort)
        writeups = es.search(index='alerts', body=query)
        writeups = writeups['hits']
        if self.request.user.instances[0].memos :
            new_term = '{"terms": {"type": [%d,%d] }}' % (10,11)
            new_query='{"size" : 100,"query": {"filtered":{"filter": {"and" : [%s,%s] }}},%s}' % (new_term,employees,sort)
            memos = es.search(index='alerts', body=new_query)
            memos = memos['hits']
        else : memos = {'hits': [], 'total': 0}
        if self.request.user.instances[0].manager_messages :
            mes_term = '{"terms": {"type": [%d,%d,%d] }}' % (7,8,9)
            mes_query='{"size" : 100,"query": {"filtered":{"filter": {"and" : [%s,%s] }}},%s}' % (mes_term,employees,sort)
            messages = es.search(index='alerts', body=mes_query)
            messages = messages['hits']
        else : messages = {'hits': [], 'total': 0}

        hidden_fields = [field for field in self.configurable_fields if field not in self.request.user.instances[0].user_configs]
        if not ( self.request.user.instances[0].multi_manager and self.request.user == self.request.user.instances[0].admin ): 
            hidden_fields.append("employees")
        for field in hidden_fields :
                nform.fields[field].widget.attrs['hidden'] = True
                nform.fields[field].label = ''
                nform.fields[field].help_text = ''

        if len(self.request.GET):
            data = self.request.GET
            if data.get('l') :
                list = data['l'].split(",")
                item = list.index(object.id.__str__())
                if item != 0 :
                    context['previous'] = list[item-1]
                    context['prev_employee'] = Profile.objects.get(id=list[item-1]).get_full_name()
                if item != list.__len__()-1 :
                    context['next'] = list[item+1] 
                    context['next_employee'] = Profile.objects.get(id=list[item+1]).get_full_name()
                context['list'] = data['l']

        context['action'] = reverse('clock_form_employee', kwargs={'pk': object.id})
        context['wentries'] = wentries
        context['writeups'] = writeups
        context['memos'] = memos
        context['mesages'] = messages
        context['form'] = nform

        return context

    def form_valid(self, form) :
        super(UpdateEmployeeView, self).form_valid(form)

        if self.request.user.instances[0].multi_manager and self.request.user == self.request.user.instances[0].admin : 
            pf = self.get_object()
            pf.employers.clear()
            pf.employees.clear()
            pf.save()
            instance_manager = self.request.user.instances[0].admin
            instance_manager.employees.add(pf)
            instance_manager.save()
            for manager in form.cleaned_data['employees']:
                if manager != instance_manager :
                    manager.employees.add(pf)
                    manager.save()

        return redirect(self.get_success_url())

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        if not is_manager(self.request.user):
            return redirect(reverse('webapp_dashboard'))

        return super(UpdateEmployeeView, self).dispatch(*args, **kwargs)

class AppDashboard(UpdateView):

    template_name = 'clock/webapp.html'

    def authenticate(self, request):
        Token.objects.get_or_create(user=request.user)
        return Token.objects.get(user=request.user)

    def localize(self, request, key):

        local_request = request
        local_request.META['HTTP_AUTHORIZATION'] = 'Token ' + self.authenticate(request).key
        local_request.auth = True

        return local_request

    def get(self, request):

        if self.request.user.groups.all():
            if is_manager(self.request.user) or self.request.user.groups.filter(name='Reclutant'):
                return redirect(reverse('clock_dashboard'))
            elif 'Console' in self.request.user.groups.first().name :
                return redirect(reverse('tax_identify_client'))
        else:
            return redirect(reverse('register_detail_applicant', kwargs={'pk':self.request.user.pk}))

        local_request = self.localize(request, self.authenticate(request))
        location_geo = request.GET.get('location_geo')
        set_up = setup(local_request, location_geo)
        status = user(local_request, location_geo)
        status_data = status.data
        for key in status_data: 
            if key != 'detail' : setattr(status_data, key, status_data[key])
        if status_data.status in [3,4]:
            for key in status_data.data: setattr(status_data.data, key, status_data.data[key])

        if len(self.request.GET):
            data = self.request.GET
            if data.get('i') == 'text' :
                form = WriteupForm
                status = {'status': 1, 'writeup': False}
                if self.request.user.instances[0].manager_messages :
                    es = elasticsearch.Elasticsearch(es_host)
                    employees = '{"term": {"user_id": %d }}' % self.request.user.id
                    term = '{"terms": {"type": [%d,%d,%d] }}' % (7,8,9)
                    sort = '"sort": {"time": {"order":"desc"}}'
                    query='{"size" : 10,"query": {"filtered":{"filter": {"and" : [%s,%s] }}},%s}' % (term,employees,sort)
                    messages = es.search(index='alerts', body=query)
                    messages = messages['hits']
                else : messages = {'hits': [], 'total': 0}

                return render(request, self.template_name, {'messages': messages, 'status': status, 'form': form, 'site_name': self.request.user.sites.all()})

        if status_data.status == 2 and 'Affiliate' in self.request.user.groups.first().name :
            return redirect(reverse('tax_home'))#,kwargs={'status': status, }))

        if status_data.status == 1 :
            form = SignForm
            status_data.writeup = True
            return render(request, self.template_name, {'status': status_data, 'form': form, 'site_name': self.request.user.sites.all()})

        return render(request, self.template_name, {'status': status_data, 'rest_reminder': set_up.data['rest_reminder'], 'location_geo': location_geo, 'site_name': status_data.get('site_name') })

    def post(self, request, **kwargs):

        class Add():
           pass

        DATA = Add()
        DATA.validation = request.POST.get('validation')
        DATA.site_name = request.POST.get('site_name')
        DATA.list = request.POST.get('list')
        DATA.end = request.POST.get('end')
        DATA.start = request.POST.get('start')
        DATA.worked = request.POST.get('worked')

        local_request = self.localize(request, self.authenticate(request))
        local_request.method = 'PUT'

        if request.POST.get('text'):
            time = message(local_request)
            if time.status_code == 201:
                status = {'status': 9, 'data': 'Message sent'}
            else:   
                status = {'status': 9, 'data': 'There was a problem!'}
            return render(request, self.template_name, {'status': status, 'site_name': self.request.user.sites.all() })

        if request.POST.get('password'):
            time = writeup(local_request)
            if time.status_code == 200:
                status = {'status': 9, 'data': 'Signed!'}
            else:   
                status = {'status': 9, 'data': 'NOT signed!'}
            return render(request, self.template_name, {'status': status, 'site_name': self.request.user.sites.all() })

        if request.POST.get('ID'):

            if DATA.validation == '2' :

                time = checkout(local_request)

                time.data['site_name'] = DATA.site_name
                for key in time.data: setattr(time.data, key, time.data[key])
                time.data['worked'] = time.data.end - stripdecimal(time.data.start)
                status = {'status': 11, 'data': time.data }

            else:
                time = validate_entry(local_request)

                for key in time.data: setattr(time.data, key, time.data[key])
                time.data['start'] = DATA.start
                time.data['end'] = DATA.end
                time.data['worked'] = DATA.worked
                time.data['site_name'] = DATA.site_name

                if time.status_code != 201 :
                    return redirect(reverse('clock_list_entries',args=('',)))

                if time.data.get('status') == 3:
                    status = {'status': 13, 'data': time.data}
                else:
                    status = {'status': 12, 'data': time.data}

                # this is missleading since entry has not been updated yet!
                if DATA.list == '1':
                    return redirect(reverse('clock_list_entries',args=('',)))

        else:  
            time = checkin(local_request)
            time.data['site_name'] = DATA.site_name
            for key in time.data: setattr(time.data, key, time.data[key])

            status = {'status': 10, 'data': time.data}
            if time.status_code == 201 and 'Affiliate' in self.request.user.groups.first().name :
                from time import sleep
                sleep(5)
                return redirect(reverse('tax_home'))#,kwargs={'status': status, }))

        if time.status_code == 201 :
            return render(request, self.template_name, {'status': status })
        elif time.status_code == 417 :
            return render(request, self.template_name, {'status': status['data'] })
        else:
            return time

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(AppDashboard, self).dispatch(*args, **kwargs)

linea = 0

@login_required
def report(request, opt):
    data = request.GET

    es = elasticsearch.Elasticsearch(es_host)
    sort = '"sort": [{"start": "asc" }]'

    instance = "Fernic"
    include_date =  pytz.utc.localize(datetime.today(), is_dst=None).astimezone (local)
    if data.get('d') :
        try :
            include_date = datetime.strptime(data['d'], '%Y-%m-%d')
            include_date = include_date.replace(tzinfo=local)
        except ValueError :
            request.error = 'Incorrect date format'
            return dashboard(request)
    if request.user.instances[0].report == 5 :
        if data.get('p') == "monthly" :
            instance = "monthly"
            if include_date.day > 25 :
                new_month = include_date.month + 1
                new_year = include_date.year
                if new_month == 13 : 
                    new_month = 1
                    new_year = include_date.year + 1
                include_date = include_date.replace(day=25,month=new_month,year=new_year) 
            else : include_date = include_date.replace(day=25)
        else : instance = "biweekly"
    week_end = week_ending(instance, include_date)
    if int(week_end.strftime('%U')) % 2 == 0 :
        if instance == "Fernic" : week_end += timedelta(days=7)
    elif instance == "biweekly" :
        week_end += timedelta(days=7)
    if instance in ["monthly", ] :
        week_end += timedelta(days=7)
    fina = (week_end-timedelta(days=42))
    fin0 = (week_end-timedelta(days=35))
    fin1 = (week_end-timedelta(days=28))
    fin2 = (week_end-timedelta(days=21))
    fin3 = (week_end-timedelta(days=14))
    fin4 = (week_end-timedelta(days=7))
    fin5 = week_end
    range5=(' "range" : { "start" : { "gte" : "%s"} } ' % fina.isoformat(),' "range" : { "start" : { "lte" : "%s"} } ' % fin0.isoformat())
    range4=(' "range" : { "start" : { "gte" : "%s"} } ' % fin0.isoformat(),' "range" : { "start" : { "lte" : "%s"} } ' % fin1.isoformat())
    range0=(' "range" : { "start" : { "gte" : "%s"} } ' % fin1.isoformat(),' "range" : { "start" : { "lte" : "%s"} } ' % fin2.isoformat())
    range1=(' "range" : { "start" : { "gte" : "%s"} } ' % fin2.isoformat(),' "range" : { "start" : { "lte" : "%s"} } ' % fin3.isoformat())
    range2=(' "range" : { "start" : { "gte" : "%s"} } ' % fin3.isoformat(),' "range" : { "start" : { "lte" : "%s"} } ' % fin4.isoformat())
    range3=(' "range" : { "start" : { "gte" : "%s"} } ' % fin4.isoformat(),' "range" : { "start" : { "lte" : "%s"} } ' % fin5.isoformat())
    if 'p' not in opt and 'l' not in opt:
        weeks = [range2,range3]
        range = [fin3,fin5]
    else:
        weeks = [range0,range1]
        range = [fin1,fin3]

    if request.user.groups.first().name == 'QS Manager' :
        weeks = [range3]
        range = [fin4,fin5]

    if 'u' in opt :
        employees = SearchQuerySet().models(Profile).order_by('last_name').filter(text__icontains=request.user.instances[0].name+' Employee')

    else : employees = request.user.employees.all().order_by('last_name')

    deduce_lunch = False
    if data.get('p') :
        deduce_lunch = True
        if data['p'] == "monthly" :
            employee_type = "Monthly employees"
            employees = employees.filter(pay_period=3)
            finl = include_date+timedelta(days=1)
            if finl > fin5 :
                rangel = (' "range" : { "start" : { "gte" : "%s"} } ' % fin5.isoformat(),' "range" : { "start" : { "lte" : "%s"} } ' % finl.isoformat())
                weeks = [range4,range0,range1,range2,range3,rangel]
            else :
                rangel = (' "range" : { "start" : { "gte" : "%s"} } ' % fin4.isoformat(),' "range" : { "start" : { "lte" : "%s"} } ' % finl.isoformat())
                weeks = [range4,range0,range1,range2,rangel]
            range = [fin0,finl]

        else :
            employee_type = "Biweekly employees"
            if 'p' in opt :
                weeks = [range5,range4]
                range = [fina,fin1]
            employees = employees.filter(pay_period=2)
            if data.get('e') :
                employees = employees.filter(id=data['e'])
                opt += 'e'

    if data.get('d') == '2017-01-01' and request.user.groups.first().name == 'Fernic Manager' :
        first_date = datetime.strptime('2016-12-19', '%Y-%m-%d')
        first_date = first_date.replace(tzinfo=local)
        mid_date = datetime.strptime('2017-01-01', '%Y-%m-%d')
        mid_date = mid_date.replace(tzinfo=local)
        last_date = datetime.strptime('2017-01-02', '%Y-%m-%d')
        last_date = last_date.replace(tzinfo=local)
        rangex=(' "range" : { "start" : { "gte" : "%s"} } ' % first_date.isoformat(),' "range" : { "start" : { "lte" : "%s"} } ' % mid_date.isoformat())
        rangey=(' "range" : { "start" : { "gte" : "%s"} } ' % mid_date.isoformat(),' "range" : { "start" : { "lte" : "%s"} } ' % last_date.isoformat())
        weeks = [rangex,rangey]
        range = [first_date,last_date]

    if request.user.groups.first().name != 'PPI Manager' :
        import csv
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="report.csv"'
        response.write(u'\ufeff'.encode("utf-8"))
        writer = csv.writer(response, dialect = 'excel')
        write = writer.writerow
    else :
        import io
        from xlsxwriter.workbook import Workbook
        output = io.BytesIO()
        workbook = Workbook(output, {'in_memory': True, 'default_date_format': 'hh:mm'})
        worksheet = workbook.add_worksheet()       
        def write(row=[], col=0, num=-1) :
            global linea
            if num >= 0 : 
                linea = num
            else :
                linea += 1 
            worksheet.write_row(linea, col, row)

    if data.get('f') :
        if data['f'] == "detailed" : 
            opt += 'x'
            if request.user.groups.first().name == 'PPI Manager' :
                opt += 'e'
        
    desde = range[0].date()
    hasta = range[1].date()
    if 'x' in opt :
        if 'e' in opt :
            bold = workbook.add_format({'bold': 1})
            format_dt = workbook.add_format({'num_format': 'yyyy-mm-dd hh:mm', 'font_size': 8})
            format_he = workbook.add_format({'bold': 1, 'font_size': 14})
            worksheet.write(1, 0, 'Pacific Plus Int\'l Inc.', format_he)
            worksheet.write(3, 0, 'Daily Report')
            worksheet.write(3, 3, employee_type)
            worksheet.write(5, 0, 'From', bold)
            worksheet.write(5, 1, desde.isoformat())
            worksheet.write(6, 0, 'To', bold)
            worksheet.write(6, 1, (hasta-timedelta(days=1)).isoformat())
        elif deduce_lunch : write(['Last name','First name','Date','Total','Break','Overtime','Notes'])
        elif request.user.groups.first().name == 'QS Manager' :
            write(['last_name','first_name','date','start','end','worked_hours','total'])
        else : write(['last_name','first_name','date','worked_hours','total'])
        write([None,None,None,None,None])
    else :
        if 'u' in opt :
            write(['last_name','first_name','username','active','managed'])
            write([None,None,None,None,None,None,pytz.utc.localize(datetime.now(), is_dst=None).astimezone (local)])
        else : write(['From',desde,'To',hasta-timedelta(days=1),None])

    for worker in employees :
        global linea
        if 'u' in opt :
            managed = True
            if worker.employers.__len__() < 2 : managed = False
            write([worker.last_name.encode("utf-8"),worker.first_name.encode("utf-8"),worker.username,worker.object.is_active,managed])
            continue
        if 'e' in opt :
            worksheet = workbook.add_worksheet()
            worksheet.set_column("A:A", 10)
            worksheet.set_column("J:J", 12)
            worksheet.write(0, 9, pytz.utc.localize(datetime.now(), is_dst=None).astimezone (local).replace(tzinfo=None), format_dt)
            worksheet.write(1, 3, 'Employee Timecard Report', format_he)
            worksheet.write(2, 4, 'Pacific Plus Int\'l Inc.', bold)
            worksheet.write(3, 4, desde.isoformat()+' - '+(hasta-timedelta(days=1)).isoformat())
            worksheet.write(5, 0, worker.last_name+' '+worker.first_name, bold)
            worksheet.write_row(6, 0, ['Date','In','Out','In','Out', 'Total', 'Overtime', 'HTO', 'Break', 'Notes'])
            linea = 6
        term_1='{"term":{"clock_entry.user_id":%d}}' %worker.pk
        term_2='{"terms":{"clock_entry.status":[%d,%d,%d,%d,%d,%d]}}' %(1,2,3,4,6,7)
        extra = 0
        total = 0
        total_lunch=timedelta(minutes=0)
        notes = []
        for range in weeks :
            status = []
            row=[None,None,None,None,None,None,None]
            erow=[None,None,None,None,None,None,None,None,None,None]
            row[0]=worker.last_name.encode("utf-8")
            row[1]=worker.first_name.encode("utf-8")
            extraw = timedelta(minutes=0)
            week=timedelta(minutes=0)
            hweek=timedelta(minutes=0)
            lunch=timedelta(minutes=0)
            query='{"size" : 50,"query": {"filtered":{"filter":{"and":[{%s},{%s},%s,%s]}}},%s}' % (range[0],range[1],term_1,term_2,sort ) 
            entradas=es.search(index=ES_INDICES, fields='start,end,status,note',body=query)
            lprint = True
            for entry in entradas['hits']['hits'] :
                if entry['fields']['status'][0] == 2 : status.append("To approve")
                if entry['fields']['status'][0] == 3 : status.append("Declined")
                if entry['fields']['status'][0] == 4 : status.append("Accounted")
                if entry['fields']['status'][0] == 6 : status.append("Admin Forced")
                if entry['fields']['status'][0] == 7 : status.append("System Forced")
                if entry['fields'].get('note') : notes.append(entry['fields']['note'][0])
                start_utc = stripdecimal(entry['fields']['start'][0])
                end_utc = stripdecimal(entry['fields']['end'][0])
                start = pytz.utc.localize(start_utc, is_dst=None).astimezone (local)
                end = pytz.utc.localize(end_utc, is_dst=None).astimezone (local)
                date = start.date()
                if instance == "monthly" :
                    new_month = include_date.month - 1
                    new_year = include_date.year
                    if new_month == 0 : 
                        new_month = 12
                        new_year = include_date.year -1
                    previous_include = include_date.replace(day=26,month=new_month,year=new_year) 
                    lprint = date > previous_include.date()
                if not row[2] : # primera
                
                    row[2]=date
                    erow[1] = start.time()
                    erow[2] = end.time()
                    row[3]=end-start
                    if deduce_lunch :
                            if row[3] > timedelta(hours=7) :
                                row[4] = timedelta(hours=1)
                                row[3] -= timedelta(hours=1)
                            else : row[4] = None
                else :
                    if date == row[2] : # mismo dia 
                        if row[4] and end-start != timedelta(minutes=0) :
                            row[3] += timedelta(hours=1)
                            row[4] = None
                        if not erow[3] : erow[3] = start.time()
                        if not erow[4] : erow[4] = end.time()
                        if end-start == timedelta(minutes=0) and notes.__len__() > 0 :
                            status.pop()
                            row[6] = notes.__len__()
                            erow[9] = notes.__len__()
                            erow[3] = None
                            erow[4] = None
                        row[3] += end-start
                    else : # nuevo dia
                        week += row[3]
                        if week + hweek > timedelta(hours=40) :
                            if extraw > timedelta(minutes=0) and row[3] > timedelta(minutes=0) : extraw = row[3]
                            elif hweek > timedelta(minutes=0) : extraw = hweek + week - timedelta(hours=40)
                            else : extraw = week - timedelta(hours=40)
                        if lprint and row[4] : lunch += row[4]
                        if deduce_lunch : row[5] = "%.2f" % (extraw.total_seconds()/3600)
                        row[3]= "%.2f" % (row[3].total_seconds()/3600)
                        if 'e' in opt :
                            erow[0] = row[2].isoformat()
                            erow[6] = "%.2f" % (extraw.total_seconds()/3600)
                            erow[5] = row[3]
                            erow[7] = "%.2f" % (week.total_seconds()/3600)
                            erow[8] = row[4]
                        if 'x' in opt : 
                            if row[3] == 0 and notes.__len__() > 0 :
                                note = notes.pop()
                                row[6] = note
                                status = []
                                erow[2] = note
                                for k in [1,3,4,5,6,7,8,9] : erow[k] = None
                            if 'e' in opt :
                                write(erow)
                                erow=[None,None,None,None,None,None,None,None,None,None]
                            else :
                                if 'x' in opt and not deduce_lunch and status : row.extend(status)
                                if lprint : 
                                    if row[3] == 0 : 
                                        write([row[0],row[1],row[2],None,row[6]])
                                    elif request.user.groups.first().name == 'QS Manager' :
                                        write([row[0],row[1],row[2],erow[1],erow[2],row[3],row[4],row[5],row[6]])
                                        erow=[None,None,None,None,None,None,None,None,None,None]
                                    else :
                                        write(row)
                                    row[6] = None 
                                else :
                                    hweek += week
                                    week = timedelta(minutes=0)
                                if status.__len__() > 0 :
                                    for state in status :
                                        if state in row : row.remove(state)
                                    status = []
                        row[2]=date
                        erow[1] = start.time()
                        erow[2] = end.time()
                        row[3]=end-start
                        if deduce_lunch :
                            if row[3] > timedelta(hours=7) :
                                row[4] = timedelta(hours=1)
                                row[3] -= timedelta(hours=1)
                            else : row[4] = None
                if entry == entradas['hits']['hits'][int(len(entradas['hits']['hits']))-1] and lprint : # escribir ultima y sub-totales
                    week+= row[3]
                    if hweek > timedelta(minutes=0) : hweek += week
                    if week > timedelta(hours=40) or hweek > timedelta(hours=40) :
                        if extraw > timedelta(hours=0) : extraw = row[3]
                        elif hweek > timedelta(minutes=0) : extraw = hweek  - timedelta(hours=40)
                        else : extraw = week - timedelta(hours=40)
                    if row[4] : lunch += row[4]
                    if deduce_lunch : row[5] = "%.2f" % (extraw.total_seconds()/3600)
                    row[3]= "%.2f" % (row[3].total_seconds()/3600)
                    if 'e' in opt :
                        erow[0] = row[2].isoformat()
                        if not erow[1] : erow[1] = start.time()
                        if not erow[2] : erow[2] = end.time()
                        erow[6] = "%.2f" % (extraw.total_seconds()/3600)
                        erow[5] = row[3]
                        erow[7] = "%.2f" % (week.total_seconds()/3600)
                        erow[8] = row[4]
                    if row[3] == 0 and notes.__len__() > 0 :
                        note = notes.pop()
                        erow = [row[2],note]
                        row[3] = note
                    if 'x' in opt :
                        if deduce_lunch : row[5] = "%.2f" % (extraw.total_seconds()/3600)
                        elif status : row.extend(status)
                        if 'e' in opt :
                            write(erow)
                            erow=[None,None,None,None,None,None,None,None,None,None]
                        elif request.user.groups.first().name == 'QS Manager' :
                            write([row[0],row[1],row[2],erow[1],erow[2],row[3],row[4],row[5],row[6]])
                            erow=[None,None,None,None,None,None,None,None,None,None]
                        else : write(row)
                    total+=week.total_seconds()
                    if week.total_seconds() > 40*3600 or hweek.total_seconds() > 40*3600 :
                        if hweek > timedelta(hours=40) :
                            extraw = hweek.total_seconds()-(40*3600)
                        else : extraw = week.total_seconds()-(40*3600)
                        extra += extraw
                        if 'x' in opt :
                            write([None,'Sub-Total', "%.2f" % ((week.total_seconds()-extraw)/3600),' regular hrs.',
                                            "%.2f" % (extraw/3600),' hrs. overtime'])
                    elif week.total_seconds() != 0 :
                        if 'x' in opt : write([None,None,None,'Sub-Total',"%.2f" % (week.total_seconds()/3600)])
            if lunch > timedelta(minutes=0) :
                total_lunch += lunch 
                if 'x' in opt and lprint : write([None,None,None,'Deduced lunch-time: ',lunch])
        if extra > 0:
                if 'x' in opt : write([None,'Total', "%.2f" % ((total-extra)/3600),' regular hrs. ', "%.2f" % (extra/3600),' hrs. overtime'])
        elif total != 0 or not request.user.instances[0].iframes :
                if 'x' in opt :
                    if total == 0 : write([row[0],row[1]])
                    write([None,None,None,'Total: ', "%.2f" % (total/3600)])

        if not 'x' in opt :
            if total_lunch > timedelta(minutes=0) :
                 write([row[0]+', '+row[1],'Total', "%.2f" % ((total-extra)/3600),' regular hrs. ', "%.2f" % (extra/3600),' hrs. overtime',
                                'Deduced lunch-time: ',total_lunch])
            elif total != 0 or not request.user.instances[0].iframes :
                write([row[0]+', '+row[1],'Total', "%.2f" % ((total-extra)/3600),' regular hrs. ', "%.2f" % (extra/3600),' hrs. overtime'])

        if 'x' in opt :
            write([None,None,None,None,None])

        if 'e' in opt :
            format_sg = workbook.add_format({'top' : 1})
            linea += 2
            worksheet.write(linea, 0, 'Employee Signature', format_sg)
            worksheet.write(linea, 1, '', format_sg)
            worksheet.write(linea, 3, 'Date', format_sg)
            linea += 3
            worksheet.write(linea, 0, 'Approved By', format_sg)
            worksheet.write(linea, 1, '', format_sg)
            worksheet.write(linea, 3, 'Date', format_sg)

        if notes.__len__() > 0 :
                i = 0 
                erow=[None,None,None,None,None,None,None,None,None]
                write(erow)
                write(['Notes'])
                while i < notes.__len__() :
                    write([ i+1 , notes[i]])
                    i += 1

    if request.user.groups.first().name == 'PPI Manager' :
        workbook.close()
        output.seek(0)
        response = HttpResponse(output.read(), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        response['Content-Disposition'] = "attachment; filename=report.xlsx"

    return response
