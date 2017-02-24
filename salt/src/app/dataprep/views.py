from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from dataprep.serializers import (ClockinSerializer, ClockoutSerializer, ValidateSerializer,
    StatusSerializer, ClockedinSerializer, HistentrySerializer, HistorySerializer, AlertSerializer,
    SiteinfoSerializer, WriteupSerializer, SetupSerializer, WithinSerializer, FenceSerializer, MessageSerializer)
from dataprep.tasks import insert_entry, end_entry, edit_entry, edit_profile, round_time, insert_alert
from rest_framework.parsers import JSONParser
from django.shortcuts import redirect
from datetime import datetime, timedelta
from clock.templatetags.dicgetatt import stripdecimal
from django.utils.translation import ugettext_lazy as _

import elasticsearch
from django.conf import settings
es_host = settings.ELASTICSEARCH_HOST
ES_INDICES = '2016-4*,2016-5*,2017-*'
#max_writeups = settings.COMPANY['MAX_WRITEUPS']
max_writeups = 2000

#EMPLOYEE_STATUS = ( (1, 'Pendig WriteUp'), (2, 'ClockedIn'), (3, 'In Schedule'), (4, 'Out Schedule'), (5, 'Forbidden') )
#ENTRY_STATUS = ( (0, 'Not ClockedOut'), (1, 'Approved'), (2, 'To be approved'), (3, 'Not approved'), (4, 'Rolled up'), (5, 'Superseded'), (6, 'System Forced'), (7, 'Manager forced') )

@api_view(['GET'])
def setup(request, location_geo):
    if request.method == 'GET':

        if request.auth:

            user_id = request.user.pk
            if location_geo :
                    es = elasticsearch.Elasticsearch(es_host)
                    profile = es.get(index='search', id='profiles.profile.%d' % user_id )
                    profile['_source']['last_location'] = location_geo
                    profile['_source']['last_time'] = datetime.now()
                    edit_profile.delay('search', profile['_source'], profile['_id'])

            response = SetupSerializer( { 'full_name': request.user.get_full_name(),
            'geo_frecuency': request.user.geo_frecuency*60, 'rest_reminder': request.user.pay_type,
            'desired_accuracy': request.user.desired_accuracy, 'stationary_radius': request.user.stationary_radius,
            'distance_filter': request.user.distance_filter, 'location_timeout': request.user.location_timeout,
            'IOS_config': request.user.IOS_config } )

            return Response(response.data)

        return Response('Not authenticated', status=status.HTTP_401_UNAUTHORIZED)

@api_view(['PUT'])
def checkin(request):
    if request.method == 'PUT':

        if not request.auth:
            return Response('Not authenticated', status=status.HTTP_401_UNAUTHORIZED)

        serializer = ClockinSerializer(data=request.DATA)

        if serializer.is_valid() and request.auth:

            date = datetime.now()

            serializer.data['user_id'] = request.user.pk

            if not serializer.data['start'] : serializer.data['start'] = date
            es = elasticsearch.Elasticsearch(es_host)

            location_geo = serializer.data.get('location_geo')
            location_id = serializer.data.get('location_id')

            profile_id = 'profiles.profile.%d' % serializer.data['user_id']
            profile = es.get(index='search', id=profile_id )
            profile = profile['_source']

            if location_geo : profile['last_location'] = location_geo
            profile['last_time'] = date
            edit_profile.delay('search', profile, profile_id)

            period = 15
            if request.user.employment_type == 3:
                period = 0

            if request.user.geo_radius == 1 or request.user.geo_frecuency != 0 :

                if location_geo :
                    if 'SuperRestricted' in profile['text'] :
                        if location_id :
                            site = es.get(index='search', id='clock.site.%d' % location_id)
                            site = site['_source']

                            term = '{"last_location": {"points": %s }}' % site['location'][0]
                            query='{"query": {"filtered":{"filter": {"geo_polygon" : %s }}}}' % term
                            user_in = es.search(index='search', fields='django_id', body=query)

                        if not location_id or [profile['django_id']] not in [worker['fields']['django_id'] for worker in user_in['hits']['hits'] ]:
                            initial = StatusSerializer({ 'status': 5, 'data': _('Clockin not allowed out of configured site, location')+': '+location_geo })
                            return Response(initial.data, status=status.HTTP_417_EXPECTATION_FAILED)

                    # elif 'Fernic' in profile['text'] :
                        # buscar el query para encontrar el site dentro del cual esta
                        # user_in = es.search(index='search', fields='django_id', body=query)

                else :
                        initial = StatusSerializer({ 'status': 5, 'data': _('Clockin not allowed without geo-location data') })
                        return Response(initial.data, status=status.HTTP_417_EXPECTATION_FAILED)
                

            doc = insert_entry.delay(serializer.data, period)

            resp = ClockedinSerializer({'start': round_time(serializer.data.get('start'), period) })

            return Response(resp.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT'])
def checkout(request):
    if request.method == 'PUT' :

        if not request.auth:
            return Response('Not authenticated', status=status.HTTP_401_UNAUTHORIZED)

        serializer = ClockoutSerializer(data=request.DATA)

        if serializer.is_valid() and request.auth:

            date = datetime.now()
            date_string = date.strftime('%Y-%U')

            if not serializer.data['end'] : serializer.data['end'] = date

            es = elasticsearch.Elasticsearch(es_host)

            pk = serializer.data['ID']

            doc = es.get(index=date_string, id=pk)
            doc = doc.get('_source')
            site_name = serializer.data['site_name']
            start = doc['start']

            if doc['status'] != 0:  # raise Exception('Already checkout')
                resp = HistentrySerializer({'ID': pk, 'week': date_string,
                        'start': start, 'end': stripdecimal(doc['end']), 'site_name': site_name})
                return Response(resp.data, status=status.HTTP_201_CREATED)

            if doc['user_id'] != request.user.pk: raise Exception('Wrong user')

            profile_id = 'profiles.profile.%d' % request.user.pk
            profile = es.get(index='search', id=profile_id )
            profile = profile['_source']

            period = 15
            if request.user.employment_type ==  3 :
                period =0

            delta = timedelta(hours=9)
            yesterday_worked = timedelta(seconds=0)
            if doc.get('worked') :
                yesterday_worked = timedelta(seconds=doc.get('worked'))
            if 'Fernic' in profile['text'] and (date - stripdecimal(start) + yesterday_worked) > delta :
                serializer.data['end'] = stripdecimal(start) + delta - yesterday_worked

            end_task = end_entry.delay(serializer, doc, date_string, period)

            end = round_time(serializer.data['end'], period)

            #if doc['location_id'] and not site_name:
            #    sid = 'clock.site.%d' % doc['location_id']
            #    site = es.get(index='search', id=sid)
            #    site_name = site.get('_source')['name']

            resp = HistentrySerializer({'ID': pk, 'week': date_string,
                        'start': start, 'end': end, 'site_name': site_name})

            return Response(resp.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT'])
def writeup(request):
    if request.method == 'PUT':

        if not request.auth:
            return Response('Not authenticated', status=status.HTTP_401_UNAUTHORIZED)

        serializer = WriteupSerializer(data=request.DATA)

        if serializer.is_valid() and request.auth:

            user_id = request.user.pk
            from profiles.models import Profile
            employee = Profile.objects.get(pk=user_id)

            if employee.check_password(serializer.data.get('password')):

                es = elasticsearch.Elasticsearch(es_host)

                term_1 = '{"term":{"user_id":%d}}' % user_id
                term_2 = '{"terms":{"type":[%d,%d]}}' % (0,10)
                sort = '"sort": { "time" : {"order" : "desc", "ignore_unmapped" : true }}'
                query='{"query": {"filtered":{"filter": {"and" : [%s,%s] }}},%s}' % (term_1,term_2,sort)
                writeups = es.search(index='alerts', body=query)
                writeup = writeups['hits']['hits'][0]['_source']

                if writeup['type'] == 0 : writeup['type'] = 6
                if writeup['type'] == 10 : writeup['type'] = 11
                writeup['date'] = datetime.now()

                edit_entry.delay('alerts', writeup, writeups['hits']['hits'][0]['_id'], 'alert_entry')

                resp = StatusSerializer({'status': 1})

                return Response(resp.data, status=200)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT'])
def validate_entry(request):
    if request.method == 'PUT':

        if not request.auth:
            return Response('Not authenticated',
                status=status.HTTP_401_UNAUTHORIZED)

        serializer = ValidateSerializer(data=request.DATA)

        if serializer.is_valid() and request.auth:

            date = datetime.now()

            es = elasticsearch.Elasticsearch(es_host)

            ID = serializer.data['ID']
            week = serializer.data.get('week')

            if week: index_name = week
            else:
                index_name = date.strftime('%Y-%U')

            doc = es.get(index=index_name, id=ID)
            doc = doc.get('_source')

            if doc['status'] == 0 : return Response(serializer.data,
                                    status=status.HTTP_400_BAD_REQUEST)

            if ( doc['status'] == 2 and serializer.data.get('unvalidate') != True) or doc['status'] == 3:
                doc['status'] = 1
                doc['validate_time'] = date

            else:
                doc['status'] = 3
                doc['validate_time'] = None

            new_status = doc['status']

            doc = edit_entry.delay(index_name, doc, ID, 'clock_entry')
            resp = StatusSerializer({ 'status': new_status })

            return Response(resp.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def user(request, location_geo):
    if request.method == 'GET' :

        if request.auth:
            user_id = request.user.pk

            es = elasticsearch.Elasticsearch(es_host)
            userstatus = 5

            if location_geo :
                    profile = es.get(index='search', id='profiles.profile.%d' % user_id )
                    profile['_source']['last_location'] = location_geo
                    profile['_source']['last_time'] = datetime.now()
                    edit_profile.delay('search', profile['_source'], profile['_id'])

            term_1 = '{"term":{"user_id":%d}}' % user_id
            term_2 = '{"terms":{"type": [%d,%d,%d,%d] }}' % (0,6,10,11)
            sort = '"sort": { "time" : {"order" : "desc", "ignore_unmapped" : true }}'
            query='{"query": {"filtered":{"filter": {"and" : [%s,%s] }}},%s}' % (term_1,term_2,sort)
            writeups = es.search(index='alerts', fields=('text','type'), body=query)
            if writeups['hits']['total'] >= 1:
                for writeup in writeups['hits']['hits'] :
                    if  writeup['fields']['type'] == [0] or writeup['fields']['type'] == [10] :
                        pre_text = 'WriteUp: '
                        if  writeup['fields']['type'] == [10] : pre_text = 'Memorandum: '
                        userstatus = 1
                        text = writeup['fields']['text']
                        text[0] = pre_text + text[0]
                        initial = StatusSerializer({ 'status': userstatus, 'data': text })
                        return Response(initial.data)

                if writeups['hits']['total'] >= max_writeups :
                    userstatus = 5
                    text = _('Writeup count limit reached!')
                    initial = StatusSerializer({ 'status': userstatus, 'data': text })
                    return Response(initial.data)

            date = datetime.now()
            date_string = date.strftime('%Y-%U')

            term_1 = '{"term": {"user_id": %d }}' % user_id
            term_2 = '{"term": {"status": %d }}' % 0
            query='{"query": {"filtered":{"filter": {"and" : [%s,%s] }}}}' % (term_1,term_2)
            entryid = es.search(index=date_string, fields='', body=query)

            site_name = _('Unknown')
            location_id = 0
            if location_geo :
                (loc_x,loc_y) = location_geo.split(',')
                sort = '"sort" : { "_geo_distance" : { "centre" : { "lat" : %s,  "lon" : %s }, "order" : "asc", "unit" : "km" }}' %(loc_x,loc_y)
                new_query = '{%s, "filter" : { "geo_distance" : { "distance" : "1km", "distance_type": "plane", "centre" : { "lat" : %s, "lon" : %s } } }}' %(sort,loc_x,loc_y)
                near_sites = es.search(index='search', body=new_query)

                if near_sites['hits']['hits'] : 
                    site = near_sites['hits']['hits'][0]['_source']
                    location_id = int(site['django_id'])
                    site_name = site['name']

            site_identity = SiteinfoSerializer({ 'site_name': site_name })
            site_identity.data['location_id'] = location_id

            if entryid['hits']['hits']:
                userstatus = 2
                text = entryid['hits']['hits'][0]['_id']
                initial = StatusSerializer({ 'status': userstatus, 'data': text, 'site_name': site_name })

            else :
                term = '{"term":{"workers": %d}}' % user_id
                query = '{"query": {"filtered":{"filter":%s}}}' % term
                site = es.search(index='search', body=query)

                if site['hits']['hits']:
                    userstatus = 3
                    text = site_identity.data
                else:
                    text = _('User: %s, not assigned to an instance, please visit Human Resources office.') % (request.user.get_full_name())

                initial = StatusSerializer({ 'status': userstatus, 'data': text })

            return Response(initial.data)
        return Response('Not authenticated', status=status.HTTP_401_UNAUTHORIZED)

@api_view(['GET'])
def history(request):
    if request.method == 'GET':

        if request.auth:
            user_id = request.user.pk

            es = elasticsearch.Elasticsearch(es_host)

            term_1 = '{"term":{"user_id":%s}}' % str(user_id)
            term_2 = '{"not": {"term" : {"status":%d}}}' % 5
            sort = '"sort": { "start" : {"order" : "desc", "ignore_unmapped" : true }}'
            query = '{"size" : 100, "query": {"filtered": {"filter": {"and": [%s,%s] }}},%s}' % (term_1,term_2,sort )
            list = es.search(index=ES_INDICES, body=query).get('hits').get('hits')
            history_list = []
            for entry in list:
                entry['_source']['week'] = entry['_index']

                if entry['_source']['location_id'] and not entry['_source'].get('site_name'):
                    site = es.get(index='search', id='clock.site.%d' % entry['_source']['location_id'])
                    site_name = site.get('_source')['name']
                    entry['_source']['site_name'] = site_name

                serialized_entry = HistentrySerializer(entry['_source'])
                history_list.append(serialized_entry.data)

            if request.user.pay_period == 3 :
                offset = 6
            else:
                if 'PPI Employee' in [group.name for group in request.user.groups.all()]:
                    offset = 0 
                else:
                    offset = 1

            history = HistorySerializer({'status':4, 'offset': offset, 'entries':history_list})

            return Response(history.data)
        return Response('Not authenticated', status=status.HTTP_401_UNAUTHORIZED)

@api_view(['PUT'])
def message(request):

    if request.method == 'PUT':

        if not request.auth:
            return Response('Not authenticated', status=status.HTTP_401_UNAUTHORIZED)

        user_id = request.user.pk
        now = datetime.now()

        serializer = MessageSerializer(data=request.DATA)

        if serializer.is_valid() :
            a_serializer = AlertSerializer({'user_id': request.user.pk, 'location_geo': serializer.data['location_geo'], 'text': serializer.data['text'], 'type': 9, 'time': now})
            insert_alert.delay(a_serializer)

            resp = StatusSerializer({'status': 0 })

            return Response(resp.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def fence(request):

    if request.method == 'POST':

        if not request.auth:
            return Response('Not authenticated', status=status.HTTP_401_UNAUTHORIZED)

        user_id = request.user.pk

        serializer = FenceSerializer(data=request.DATA)

        if serializer.is_valid() :
            es = elasticsearch.Elasticsearch(es_host)

            location_geo = serializer.data['location_geo']
            location_id = serializer.data['location_id']

            profile_id = 'profiles.profile.%d' % user_id
            profile = es.get(index='search', id=profile_id )
            profile = profile['_source']

            insite = 1
            notification = _('The system cannot find you within the configured fence, the issue will be reported')
            a_serializer = AlertSerializer({'user_id': request.user.pk, 'location_geo': location_geo, 'text': _('Detected out of fence'), 'type': 1, 'time': datetime.now()})
            within = WithinSerializer({'within': insite, 'notification': notification})
            date = datetime.now()
            date_string = date.strftime('%Y-%U')
            term_1 = '{"term": {"user_id": %d }}' % user_id
            term_2 = '{"term": {"status": %d }}' % 0
            qquery='{"query": {"filtered":{"filter": {"and" : [%s,%s] }}}}' % (term_1,term_2)

            if location_id != 0 :
                site = es.get(index='search', id='clock.site.%d' % location_id)
                site = site['_source']

                term = '{"last_location": {"points": %s }}' % site['location'][0]
                query='{"query": {"filtered":{"filter": {"geo_polygon" : %s }}}}' % term
                user_in = es.search(index='search', fields='django_id', body=query)

                if [profile['django_id']] in [worker['fields']['django_id'] for worker in user_in['hits']['hits'] ]:
                    insite = 0
                    within = WithinSerializer({'within': insite})

                else: 
                    entryid = es.search(index=date_string, fields='', body=qquery)
                    if entryid['hits']['hits']:
                        ID = entryid['hits']['hits'][0]['_id']
                    else : raise Exception('No checkin')
                    new_serializer = ClockoutSerializer({'ID': ID, 'end': date, 'location_geo': location_geo})
                    doc = es.get(index=date_string, id=ID)
                    doc = doc.get('_source')

                    if doc['status'] != 0: raise Exception('Already checkout')
                    if doc['user_id'] != request.user.pk: raise Exception('Wrong user')

                    end_task = end_entry.delay(new_serializer, doc, date_string, 0)

                    a_serializer = AlertSerializer({'user_id': request.user.pk, 'location_geo': location_geo, 'text': _('Detected out of fence and clockout forced'), 'type': 1, 'entry_id': ID, 'time': datetime.now()})
                    insite = 1
                    notification = _('The system cannot find you within the configured fence, a clok-out has been foreced and the issue will be reported')
                    within = WithinSerializer({'within': insite, 'notification': notification})

            else :
                notification = _("The system doesn't know where are you supposed to be, the issue will be reported")
                within = WithinSerializer({'within': insite, 'notification': notification})

            if insite != 0 :
                insert_alert.delay(a_serializer)

            profile['last_location'] = location_geo
            profile['last_time'] = datetime.now()
            edit_profile.delay('search', profile, profile_id)

            return Response(within.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

