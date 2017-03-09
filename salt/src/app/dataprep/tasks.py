from celery import task
import elasticsearch
from datetime import timedelta
from django.utils.timezone import now
from dataprep.serializers import AlertSerializer
from clock.templatetags.dicgetatt import stripdecimal

from django.conf import settings
es_host = settings.ELASTICSEARCH_HOST

tolerance = timedelta(minutes=4) # before raising an alarm when times are manually entered

#ALERT_TYPE = ( (0, 'Open WriteUp'), (1, 'No GPS'), (2, 'Data out of time'), (3, 'Worked extra time'),
#               (4, 'Out of fence'), (5,'Clocked out of schedule'), (6,'Signed WriteUp'),
#               (7, 'Declined message'), (8, 'Approved message'), (9, 'Request message to manager') )
#               (10, 'Unsigned memo'), (11, 'Signed memo') )

def round_time(time, period=15, limit=8, schedule_minutes=0):

    if period == 0 : return time

    if not ( 60 % (2*period) == 0 and limit <= period and schedule_minutes % period == 0 ):
        raise Exception('Site setup incorrect')

    excess = timedelta(minutes=time.minute % period,
                       seconds=time.second, microseconds=time.microsecond)

    time -= excess
    if excess >= timedelta(minutes=limit) and ( time.minute - schedule_minutes ) % 2*period == 0:
        time += timedelta(minutes=period)
    elif excess >= timedelta(minutes=period-limit) and ( time.minute - schedule_minutes ) % 2*period == period:
        time += timedelta(minutes=period)

    return time


@task(name='app.tasks.insert_alert')
def insert_alert(serializer):
    es = elasticsearch.Elasticsearch(es_host)

    try:
        es.index(index='alerts', doc_type='alert_entry', body=serializer.data)
    except (Exception) as exc:
        raise self.retry(exc=exc)

@task(name='app.tasks.edit_profile')
def edit_profile(index, data, pk):
    es = elasticsearch.Elasticsearch(es_host)

    try:
        es.index(index, 'modelresult', data, id=pk)
    except (Exception) as exc:
        raise self.retry(exc=exc)

@task(name='app.tasks.insert_entry',ignore_result=True)
def insert_entry(data, period):
    es = elasticsearch.Elasticsearch(es_host)

    date = now()
    date_string = date.strftime('%Y-%U')

    term_1 = '{"term": {"user_id": %d }}' % data['user_id']
    term_2 = '{"term": {"status": %d }}' % 0
    query='{"query": {"filtered":{"filter": {"and" : [%s,%s] }}}}' % (term_1,term_2)
    entryid = es.search(index=date_string, fields='', body=query)
    if entryid['hits']['hits']: raise Exception('Trying to clockin again')

    start = data['start']

    # need schedule minutes from location_id or user_id if != 0 or 30
    data['start'] = round_time(start, period)

    doc = es.index(index=date_string, doc_type='clock_entry', body=data)

    user_id = data['user_id']
    profile = es.get(index='search', id='profiles.profile.%d' % user_id)

    location_geo = data.get('location_geo')
    location_id = data.get('location_id')

    if location_geo:

        profile['_source']['last_location'] = location_geo

        if location_id and profile['_source']['geo_radius'] in ["Restricted\n", "Restringido\n"] :
            site = es.get(index='search', id='clock.site.%d' % location_id)
            site = site['_source']

            term = '{"last_location": {"points": %s }}' % site['location'][0]
            query='{"query": {"filtered":{"filter": {"geo_polygon" : %s }}}}' % term
            user_in = es.search(index='search', fields='django_id', body=query)

            if [profile['_source']['django_id']] not in [worker['fields']['django_id'] for worker in user_in['hits']['hits'] ]:
                a_serializer = AlertSerializer({'user_id': data['user_id'], 'type': 1, 'entry_id': doc['_id'], 'time': date, 'text': u'Checkin outside site polygon'})
                # insert_alert.delay(a_serializer)

    elif profile['_source']['geo_radius'] in ["Restricted\n", "Restringido\n"] :
        a_serializer = AlertSerializer({'user_id': data['user_id'], 'type': 1, 'entry_id': doc['_id'], 'time': date, 'text': u'No geolocation information at checkin'})
        # insert_alert.delay(a_serializer)

    profile['_source']['last_time'] = date
    edit_profile.delay('search', profile['_source'], profile['_id'])

    if not location_id:
        a_serializer = AlertSerializer({'user_id': data['user_id'], 'type': 1, 'entry_id': doc['_id'], 'time': date, 'text': u'No site information at checkin'})
        # insert_alert.delay(a_serializer)

    if date - start > tolerance or start - date > tolerance:
        a_serializer = AlertSerializer({'user_id': data['user_id'], 'type': 2, 'entry_id': doc['_id'], 'time': date, 'text': u'Start time manually entered at checkin'})
        # insert_alert.delay(a_serializer)

    return doc

@task(name='app.tasks.end_entry')
def end_entry(serializer, doc, date_string, period):
    es = elasticsearch.Elasticsearch(es_host)

    date = now()

    pk = serializer.data.get('ID')
    end = serializer.data.get('end')
    location_geo = serializer.data.get('location_geo')
    site_name = serializer.data.get('site_name')

    if pk: doc['ID'] = pk
    if end: doc['end'] = round_time(end, period)
    doc['checkout_geo'] = location_geo
    doc['status'] = 2
    doc['worked'] = (end - stripdecimal(doc['start'])).total_seconds()
    doc['site_name'] = site_name

    user_id = doc['user_id']

    if not doc['location_id'] and site_name and site_name != 'Unknown':
        term = '{"term":{"name": "%s"}}' % site_name.lower()
        query = '{"query": {"filtered":{"filter": %s }}}' % term
        site = es.search(index='search', body=query)
        if site['hits']['hits']:
            doc['location_id'] = int(site['hits']['hits'][0]['_source']['django_id'])
            a_serializer = AlertSerializer({'user_id': user_id, 'text' : u'location manually recorded',
                        'type': 1, 'entry_id': pk, 'time': date })
            # insert_alert.delay(a_serializer)

    es.index(date_string, 'clock_entry', doc, id=pk)

    profile = es.get(index='search', id='profiles.profile.%d' % user_id)

    if location_geo:
        profile['_source']['last_location'] = location_geo

    else:
        a_serializer = AlertSerializer({'user_id': user_id, 'type': 1, 'entry_id': pk, 'time': date })

        if doc['location_id']:
            a_serializer.data['text'] = u'No geo position at checkout'
        else:
            a_serializer.data['text'] = u'No location info and site name not found: %s' %site_name

        # insert_alert.delay(a_serializer)

    profile['_source']['last_time'] = date
    edit_profile.delay('search', profile['_source'], profile['_id'])

    if doc['location_id'] and location_geo and profile['_source']['geo_radius'] in ["Restricted\n", "Restringido\n"] :
       site = es.get(index='search', id='clock.site.%d' % doc['location_id'])
       site = site['_source']

       term = '{"last_location": {"points": %s }}' % site['location'][0]
       query='{"query": {"filtered":{"filter": {"geo_polygon" : %s }}}}' % term
       user_in = es.search(index='search', fields='django_id', body=query)

       if not user_in['hits']['hits']:
            a_serializer = AlertSerializer({'user_id': user_id, 'location_geo': location_geo, 'type': 1,
                        'entry_id': pk, 'time': date, 'text': u'Outside location polygon at checkout'})

            # insert_alert.delay(a_serializer)

    if date - end > tolerance or end - date > tolerance:
        a_serializer = AlertSerializer({'user_id': user_id, 'location_geo': location_geo, 'entry_id': pk,
                    'time': date, 'type': 2, 'text': u'End time manually entered at checkout: %s' % end })

        # insert_alert.delay(a_serializer)

    return doc

@task(name='app.tasks.edit_entry')
def edit_entry(index, data, pk, type):
    es = elasticsearch.Elasticsearch(es_host)

    return es.index(index, type, data, id=pk)

