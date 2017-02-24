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
from clock.models import Site, Instance, Schedule
from tax.forms import AffiliateForm, ExpectedForm, FinishForm, ClientForm
from clock.templatetags.dicgetatt import stripdecimal
from dataprep.views import user as get_status #setup, checkin, checkout, validate_entry, writeup, message
from dataprep.tasks import edit_profile, edit_entry
from django.utils.translation import ugettext_lazy as _

from datetime import datetime, timedelta, time
import pytz
import elasticsearch

es_host = settings.ELASTICSEARCH_HOST
local = pytz.timezone("America/Chicago")

def instance(detail=None):
    return u'RR'

class MapForm(forms.Form):
    map = forms.Field(widget=GoogleMap(attrs={'width':500, 'height':300}))

class CreateClientView(CreateView):
    model = Applicant
    template_name = 'tax/start.html'
    fields = ['first_name', 'last_name', 'social_security']

    def form_valid(self, form):
        if not form.cleaned_data['first_name'] or not form.cleaned_data['last_name'] :
            form._errors[forms.forms.NON_FIELD_ERRORS] = forms.util.ErrorList ([ u'Your name is required' ])
            return self.form_invalid(form)

        first_name = form.cleaned_data['first_name']
        last_name = form.cleaned_data['last_name']
        if form.cleaned_data['social_security'] : ssn = int(form.cleaned_data['social_security'])
        else : ssn = None

        es = elasticsearch.Elasticsearch(es_host)
        first_term = '{"term": {"first_name": "%s" }}' %first_name
        last_term = '{"term": {"last_name": "%s" }}' %last_name
        query = (first_term,last_term)
        cli_query='{"size" : 100,"query": {"filtered":{"filter": {"and" : [%s,%s] }}}}' % query
        if ssn : 
            ssn_term= '{"term": {"social_security": "%d" }}' %ssn
            query = (first_term,last_term,ssn_term)
            cli_query='{"size" : 100,"query": {"filtered":{"filter": {"and" : [%s,%s,%s] }}}}' % query
        #pending_term = '{"exists": {"field": "pending" }}'
        clients = es.search(index='clients', body=cli_query).get('hits')
        af = None

        if clients['total'] == 1 :
            cl = clients['hits'][0]['_source']
            ID = clients['hits'][0]['_id']

            if cl['employer'] :
                af = es.get(index='search',
                    id='profiles.applicant.%d' % cl['employer'])['_source']
                af = af['first_name']+" "+af['last_name']

            if cl['pending'] : # and instance()+" Client" in cl['groups'] 
                pending = es.get(index='t2017-01t', id=cl['pending'])['_source']
                return render(self.request, 'tax/select_affiliate.html',
                    {'client': cl, 'affiliate': af, 'pending': pending, 'client_id': ID, 'form': AffiliateForm()})

        else :
            data = { 'first_name': first_name, 'last_name': last_name, 'social_security': ssn, 
                    'groups': [], 'employer': None, 'last_time': None, 'ID': None, 'pending': None}
            new_entry = es.index(index='clients', doc_type='client', body=data)
            ID = new_entry['_id']
            cl = data

        affiliates = SearchQuerySet().models(Applicant).order_by('last_name').filter(groups__contains=instance()+" Affiliate") 
        data = {'client_id': ID }

        return render(self.request, 'tax/select_affiliate.html', {'affiliates': affiliates,
        'client': cl, 'client_id': ID, 'affiliate': af, 'form': AffiliateForm(initial = data)})

    @method_decorator(login_required)                                                                                                                                           
    def dispatch(self, *args, **kwargs):
        return super(CreateClientView, self).dispatch(*args, **kwargs)

class QueueInView(FormView):
    form_class = AffiliateForm
    template_name = 'tax/select_affiliate.html'

    def form_valid(self, form):

        es = elasticsearch.Elasticsearch(es_host)

        af_id = int(form.cleaned_data['affiliate'])
        cl = es.get(index='clients', id=form.cleaned_data['client_id'])
        if af_id != 0 :
            af = es.get(index='search', id='profiles.applicant.%d' % af_id)['_source']
            af = af['first_name']+" "+af['last_name']
            cl['_source']['employer'] = af_id
        else :
            af = u'the next affiliate'
            cl['_source']['employer'] = None 

        cl['_source']['groups'].append(instance()+" Client")
        cl['_source']['ID'] = cl['_id']
        if not cl['_source']['last_time'] : cl['_source']['last_time'] = datetime.now()
        if cl['_source']['pending'] :
            if form.cleaned_data['social_security'] :
                if not cl['_source']['social_security'] :
                    cl['_source']['social_security'] = form.cleaned_data['social_security']
                elif form.cleaned_data['social_security'] != cl['_source']['social_security'] : 
                    form._errors[forms.forms.NON_FIELD_ERRORS] = forms.util.ErrorList ([ u'Verify your SSN' ])
                    return self.form_invalid(form)
            else :
                form._errors[forms.forms.NON_FIELD_ERRORS] = forms.util.ErrorList ([ u'Provide your SSN' ])
                return self.form_invalid(form)
        edit_entry.delay('clients', cl['_source'], cl['_id'], 'client')

        return render(self.request, 'tax/standby.html', {'client': cl['_source'], 'affiliate': af})

    @method_decorator(login_required)                                                                                                                                           
    def dispatch(self, *args, **kwargs):
        return super(QueueInView, self).dispatch(*args, **kwargs)

class QueueStartView(FormView):
    form_class = ExpectedForm
    template_name = 'tax/select.html'
    es = elasticsearch.Elasticsearch(es_host)

    def get_context_data(self, **kwargs):
        context = super(QueueStartView, self).get_context_data(**kwargs)
        open_term = '{"term": {"status": %d }}' % 2
        #pending_term = '{"exists": {"field": "pending" }}'
        afi_ents = '{"term": {"affiliate_id": %s }}' % self.request.user.id
        afi_query='{"size" : 100,"query": {"filtered":{"filter": {"and" : [%s,%s] }}}}' % (open_term,afi_ents)
        open = self.es.search(index='t2017-01t', body=afi_query).get('hits')
        if open['total'] != 0 :
            entry = open['hits'][0]
            cl = self.es.get(index='clients', id=entry['_source']['client_id'])['_source']
            options = ({ 'key': 1, 'value': u'Issue totaly completed.' },
                   { 'key': 0, 'value': u'Issue not completed.'})
            context['client_id'] = cl['ID']
            context['options'] = options
            context['element'] = "finished"
            context['client'] = cl['first_name']+' '+cl['last_name']
            context['action'] = reverse('tax_end',args=(cl['ID'],))
            context['effect'] = "Finish"
            context['form'] = FinishForm()
            context['ID'] = entry['_id']

            return context
        
        cl = self.es.get(index='clients', id=self.kwargs['client_id'])['_source']
        if not cl['last_time'] :
            return None

        NEW = { 'key': 0, 'value': "Not expected"}
        EXP = { 'key': 1, 'value': "Expected" } 
        if cl['pending'] :
            if self.request.user.id == cl['employer'] :
                pending = self.es.get(index='t2017-01t', id=cl['pending'])['_source']
                context['hide'] = { 'key': 3, 'value': "Returning" } 
                context['pending'] = pending
            else :
                return None
        options = ( EXP, NEW )
        context['client_id'] = cl['ID']
        context['client'] = cl['first_name']+' '+cl['last_name']
        context['options'] = options
        context['action'] = reverse('tax_start',args=(self.kwargs['client_id'],))
        context['effect'] = "Start"
        context['element'] = "expected"

        return context

    def form_valid(self, form):
        cl_id = str(form.cleaned_data['client_id'])
        af_id = self.request.user.id
        expected = int(form.cleaned_data['expected'])
        cl = self.es.get(index='clients', id=cl_id)['_source']
        if not cl['last_time'] :
            form._errors[forms.forms.NON_FIELD_ERRORS] = forms.util.ErrorList ([ u'Client already beeing attended' ])
            return self.form_invalid(form)
        if expected == 1 : # cambiar a la instancia
            clients = SearchQuerySet().models(Applicant).order_by('last_name').filter(employers__in=[self.request.user.id])# .filter(groups__contains=instance()+" Client") 
            options = [ { 'key': cli.pk, 'value': cli.object.get_full_name() } for cli in clients ]
            return render(self.request, 'tax/select.html', { 'client_id': cl_id,
        'element': "expected", 'options': options, 'client': cl['first_name']+" "+cl['last_name'],
        'action': reverse('tax_start',args=(cl['ID'],)),
        'effect': "Start", 'form': ExpectedForm() })

        doc = {'client_id':cl_id, 'client': cl['first_name']+" "+cl['last_name']+" "+str(cl['social_security']),
                'affiliate_id': af_id, 'queue':cl['last_time'], 'status': 2,
                'start':datetime.now(), 'expected':expected, 'start_geo': self.request.POST.get('start_geo')}
        if cl['pending'] :
            doc.update({'previous': cl['pending']})
        new_entry = self.es.index(index='t2017-01t', doc_type='tax_entry', body=doc)
        ID = new_entry['_id']

        af = self.es.get(index='search', id='profiles.applicant.%d' % af_id)['_source']
        af['last_location'] = self.request.POST.get('start_geo')
        edit_profile.delay('search', af, 'profiles.applicant.%d' % af_id)
        cl['last_time'] = None
        cl['employer'] =  self.request.user.id 
        edit_entry.delay('clients', cl, cl_id, 'client')

        options = ({ 'key': 1, 'value': "Issue totaly completed." }, { 'key': 0, 'value': "Issue not completed."})

        return render(self.request, 'tax/select.html', { 'client_id': cl_id,
        'element': "finished", 'options': options, 'client': cl['first_name']+" "+cl['last_name'],
        'action': reverse('tax_end',args=(self.kwargs['client_id'],)),
        'effect': "Finish", 'form': FinishForm(), 'ID': ID })

    @method_decorator(login_required)                                                                                                                                           
    def dispatch(self, *args, **kwargs):
        if not self.request.user.groups.filter(name=instance()+" Affiliate"):
            return redirect(reverse('webapp_dashboard'))

        return super(QueueStartView, self).dispatch(*args, **kwargs)

class QueueEndView(FormView):
    form_class = FinishForm
    template_name = 'tax/select.html'

    def get_context_data(self, **kwargs):
        context = super(QueueEndView, self).get_context_data(**kwargs)
        options = ({ 'key': 1, 'value': "YES" }, { 'key': 0, 'value': "NO"})
        context['options'] = options
        context['action'] = reverse('tax_end',args=(self.kwargs['client_id'],))
        context['effect'] = "Finish"
        context['element'] = "finished"

        return context

    def form_valid(self, form):
        def authenticate(request):
            Token.objects.get_or_create(user=request.user)
            return Token.objects.get(user=request.user)

        def localize(request, key):

            local_request = request
            local_request.META['HTTP_AUTHORIZATION'] = 'Token ' + authenticate(request).key
            local_request.auth = True

            return local_request

        es = elasticsearch.Elasticsearch(es_host)
        cl = es.get(index='clients', id=form.cleaned_data['client_id'])
        if self.request.user.id != cl['_source']['employer'] :
            form._errors[forms.forms.NON_FIELD_ERRORS] = forms.util.ErrorList ([ u'You are not attending this client!' ])
            return self.form_invalid(form)
        finished = int(form.cleaned_data['finished'])
        fees = float(form.cleaned_data['fees'])
        if  form.cleaned_data['phone'] == "" and finished == 0 :
            form._errors[forms.forms.NON_FIELD_ERRORS] = forms.util.ErrorList ([ u'A telephone number must be provided' ])
            return self.form_invalid(form)
        if fees == 0.0 and finished == 1 :
            form._errors[forms.forms.NON_FIELD_ERRORS] = forms.util.ErrorList ([ u'Fees must be nonzero' ])
            return self.form_invalid(form)

        tax_federal = float(form.cleaned_data['tax_federal'])
        tax_state = float(form.cleaned_data['tax_state'])
        phone = form.cleaned_data['phone']
        note = form.cleaned_data['note']
        ID = form.cleaned_data['ID']
        entry = es.get(index='t2017-01t', id=ID)['_source']
        if entry.get('status') != 2 :
            form._errors[forms.forms.NON_FIELD_ERRORS] = forms.util.ErrorList ([ u'Cannot finish again!' ])
            return self.form_invalid(form)
        entry['end'] = datetime.now()
        entry['status'] = finished
        entry['fees'] = fees
        entry['tax_federal'] = tax_federal
        entry['tax_state'] = tax_state
        entry['phone'] = phone
        entry['note'] = note
        edit_entry.delay('t2017-01t', entry, ID, 'tax_entry')

        worked = entry['end'] - stripdecimal(entry['start'])
        waited = stripdecimal(entry['start']) - stripdecimal(entry['queue'])
        expected = int(entry['expected'])
        if expected == 1 : 
            comission = fees * 0.4
        else :
            comission = fees * 0.2

        if finished == 1 : 
            es.delete(index='clients', doc_type='client', id=cl['_id'])
        else:
            cl['_source']['last_time'] = None
            cl['_source']['pending'] = ID
            cl['_source']['phone'] = phone
            edit_entry.delay('clients', cl['_source'], cl['_id'], 'client')

        return render(self.request, 'tax/end.html', { 'client': cl['_source'],
        'affiliate': self.request.user.get_full_name(), 'worked': worked, 'waited': waited,
        'finished': finished, 'charges': fees, 'comission': comission })

    @method_decorator(login_required)                                                                                                                                           
    def dispatch(self, *args, **kwargs):
        if not self.request.user.groups.filter(name=instance()+" Affiliate"):
            return redirect(reverse('webapp_dashboard'))

        return super(QueueEndView, self).dispatch(*args, **kwargs)

class CreateApplicantView(CreateView):
    model = Profile
    template_name = 'tax/add_affiliate.html'
    fields = ['first_name', 'last_name', 'username', 'password']

    def form_valid(self, form):

        first_name = form.cleaned_data['first_name']
        last_name = form.cleaned_data['last_name']
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']

        if self.kwargs['subclass'] == "normal" :
            af = Profile.objects.create_user(username=username, first_name=first_name, last_name=last_name, password=password)
            af.groups.add(Group.objects.get(name=instance()+' Employee'))
        elif self.kwargs['subclass'] == "affiliate" :
            af = Applicant.objects.create_user(username=username, first_name=first_name, last_name=last_name, password=password, social_security="fake")
            af.groups.add(Group.objects.get(name=instance()+' Affiliate'))
            af.save()
            af = Profile.objects.get(id=af.pk)
        af.employment_type = 3
        af.geo_raduis = 0
        af.employers.add(self.request.user)
        af.save()
        generic = self.request.user.instances[0].site
        sch = Schedule.objects.create(site=generic, worker=af)
        generic.save()

        return render(self.request, 'tax/created.html', {'affiliate': af})

    @method_decorator(login_required)                                                                                                                                           
    def dispatch(self, *args, **kwargs):
        if not self.request.user.groups.filter(name=instance()+" Manager"):
            return redirect(reverse('webapp_dashboard'))

        return super(CreateApplicantView, self).dispatch(*args, **kwargs)

class CreateExpectedView(FormView):
    form_class = ClientForm
    template_name = 'tax/client.html'

    def form_valid(self, form):
        from random import randint

        first_name = form.cleaned_data['first_name']
        last_name = form.cleaned_data['last_name']
        social_security = form.cleaned_data.get('social_security')
        if not social_security : social_security = "fake"
        affiliate = int(self.kwargs['affiliate'])

        af = Applicant.objects.create_user(username=first_name[:2].lower()+last_name[:2].lower()+str(randint(1000,9999)),
                        first_name=first_name, last_name=last_name, password='', social_security=social_security)
        af.groups.add(Group.objects.get(name='Tax Client'))
        af.employment_type = 3
        af.geo_raduis = 0
        af.is_active = False
        af.employers.add(affiliate)
        af.save()

        return render(self.request, 'tax/created.html', {'affiliate': af})

    @method_decorator(login_required)                                                                                                                                           
    def dispatch(self, *args, **kwargs):
        if not self.request.user.groups.filter(name=instance()+" Manager"):
            return redirect(reverse('webapp_dashboard'))

        return super(CreateExpectedView, self).dispatch(*args, **kwargs)

@login_required
def dashboard(request):
    def authenticate(request):
        Token.objects.get_or_create(user=request.user)
        return Token.objects.get(user=request.user)

    def localize(request, key):

        local_request = request
        local_request.META['HTTP_AUTHORIZATION'] = 'Token ' + authenticate(request).key
        local_request.auth = True

        return local_request

    if request.user.groups.filter(name=instance()+" Manager"):
        OPCIONES = { 'mapTypeId': maps.MapTypeId.ROADMAP, 'mapTypeControlOptions': { 'style': maps.MapTypeControlStyle.DROPDOWN_MENU } }
        center = maps.LatLng(32.82, -96.73)
        zoom = 8
        #OPCIONES.update({ 'center': center , 'zoom': zoom })
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

        context = {'form': MapForm(initial={'map': gmap}), }
    
        return render(request, 'tax/admin_dashboard.html', context )

    elif not request.user.groups.filter(name=instance()+" Affiliate"):
        return redirect(reverse('tax_identify_client'))

    status_data = get_status(localize(request, authenticate(request)),
                        request.GET.get('location_geo')).data

    if status_data.get('status') != 2 :
        return redirect(reverse('webapp_dashboard'))

    es = elasticsearch.Elasticsearch(es_host)
    cli_group = instance()+" Client"
    term = '"match": {"groups": "%s" }' % cli_group
    cli_query='{"size" : 100,"query": { %s }}' % term
    clients = es.search(index='clients', body=cli_query).get('hits').get('hits')
    clients = [ client['_source'] for client in clients]

    for user in clients :
        if user['employer'] :
            user['affiliates'] = [ es.get(index='search', id='profiles.applicant.%d' % int(user['employer']))['_source'] ]

    context = {'waiting': clients, 'affiliate': request.user.get_full_name(), 'pk': str(request.user.id), 'status': status_data }
    
    return render(request, 'tax/dashboard.html', context )

class GenericSearchView(SearchView):
    @method_decorator(login_required)
    def __call__(self, *args, **kwargs):
        return super(GenericSearchView, self).__call__(*args, **kwargs)

    def extra_context(self):
        return {
            'request': self.request
        }

class ListAffiliateSearchForm(SearchForm):
    def no_query_found(self):
        return self.searchqueryset.models(Profile).all()

class ListAffiliateSearchView(GenericSearchView):
    def get_template(self): 
            return 'tax/list_affiliates.html'

    def __init__(self, *args, **kwargs):
        if kwargs.get('template') is None:
            kwargs['template'] = self.get_template()

        if kwargs.get('form_class') is None:
            kwargs['form_class'] = ListAffiliateSearchForm

        super(ListAffiliateSearchView, self).__init__(*args, **kwargs)

    def build_form(self, form_kwargs=None):
        data = None
        kwargs = {'load_all': self.load_all}

        if form_kwargs: kwargs.update(form_kwargs)

        qs = SearchQuerySet().models(Profile).filter(id__in=self.request.user.employee_pk_list).order_by('last_name')

        if len(self.request.GET):
            data = self.request.GET
            if data.get('q') :
                kwargs['searchqueryset'] = qs.filter(text__icontains=data.get('q'))
        else :
            qs = qs.filter(id__in=self.request.user.employee_pk_list)

        kwargs['searchqueryset'] = qs

        return self.form_class(data, **kwargs)

    def __name__(self):
        return 'ListAffiliateSearchView'
 
class ListExpectedSearchForm(SearchForm):
    def no_query_found(self):
        return self.searchqueryset.models(Applicant).all()

class ListExpectedSearchView(GenericSearchView):
    def get_template(self): 
            return 'tax/list_expected.html'

    def __init__(self, *args, **kwargs):
        if kwargs.get('template') is None:
            kwargs['template'] = self.get_template()

        if kwargs.get('form_class') is None:
            kwargs['form_class'] = ListExpectedSearchForm

        super(ListExpectedSearchView, self).__init__(*args, **kwargs)

    def build_form(self, form_kwargs=None):
        data = self.request.GET
        kwargs = {'load_all': self.load_all, }

        if len(self.request.GET):
            if data.get('affiliate') :
                qs = SearchQuerySet().models(Applicant).order_by('last_name').filter(employers__in=[data['affiliate']])# .filter(groups__contains=instance()+" Client") 
            if data.get('q') :
                kwargs['searchqueryset'] = qs.filter(text__icontains=data.get('q'))
        else :
            qs = None

        kwargs['searchqueryset'] = qs

        return self.form_class(data, **kwargs)

    def __name__(self):
        return 'ListExpectedSearchView'
 
linea = 0

@login_required
def report(request, opt):
    data = request.GET

    es = elasticsearch.Elasticsearch(es_host)
    sort = '"sort": [{"start": "asc" }]'

    instance = "Fernic"
    include_date =    pytz.utc.localize(datetime.today(), is_dst=None).astimezone (local)
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

    if data.get('d') == '2016-01-01' and request.user.groups.first().name == 'Fernic Manager' :
        first_date = datetime.strptime('2015-12-28', '%Y-%m-%d')
        first_date = first_date.replace(tzinfo=local)
        mid_date = datetime.strptime('2016-01-01', '%Y-%m-%d')
        mid_date = mid_date.replace(tzinfo=local)
        last_date = datetime.strptime('2016-01-04', '%Y-%m-%d')
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
            entradas=es.search(index='2016-*', fields='start,end,status,note',body=query)
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
                        elif hweek > timedelta(minutes=0) : extraw = hweek    - timedelta(hours=40)
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
