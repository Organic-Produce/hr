from django.core.management.base import BaseCommand, CommandError
from datetime import datetime,timedelta
from profiles.models import Profile
from clock.templatetags.dicgetatt import stripdecimal

import elasticsearch
import logging
import pytz
from django.conf import settings

local = pytz.timezone("America/Chicago")
es_host = settings.ELASTICSEARCH_HOST 
ES_INDICES = '2016-4*,2016-5*,2017-*'

class Command(BaseCommand):

    def handle(*args, **options):
        es = elasticsearch.Elasticsearch(es_host)
        date = datetime.now()

        # ForceClose at +9 hrs. all open entries older than 9 hours for Fernic employees
        term = '{"term":{"status":0}}'
        delta = timedelta(hours=9)
        query = '{"size": 1000, "query": {"filtered":{"filter":{"and":[%s]}}}}' % term
        forced_entries = es.search(index=ES_INDICES, body=query).get('hits').get('hits')
        if forced_entries.__len__() > 0 : from django.core.mail import EmailMessage
        for entry in forced_entries:
            if entry['_source']['location_id'] in [2,3,7,16,21,22,32,42,43,44,49,50,53,54,55,56,57,58,60,62,63,64,65,66,72,75,76,77,84,87,88,90,92,93,100,101,104,105,109,115,120,121] :
                start = stripdecimal(entry['_source']['start'])
                if entry['_source'].get('worked') :
                        start -= timedelta(seconds=entry['_source']['worked'])
                if date - start > delta :
                        new_time = (start + delta).isoformat()
                        entry['_source']['status'] = 7
                        entry['_source']['end'] = new_time
                        entry['_source']['ID'] = entry['_id']
                        es.index(entry['_index'], 'clock_entry', entry['_source'], id=entry['_id'])
                        employee = Profile.objects.get(id=entry['_source']['user_id'])
                        email = EmailMessage('[HR Power] Clock-out forced', 'A clock-out has been forced for %s\nstart:\t%s\nend:\t%s\n' %(employee.get_full_name(),pytz.utc.localize(start, is_dst=None).astimezone(local).strftime('%a %d %H:%M'),pytz.utc.localize(start + delta, is_dst=None).astimezone(local).strftime('%a %d %H:%M')), to=[man.email for man in employee.employers.all()])
                        email.send()

        # Change status of "all" entries older than 42 days as "accounted"
        nstat = '{"not":{"terms":{"status":[4,5]}}}'
        range = '{"range": {"start": {"lte": "%s"}}}' % (date-timedelta(days=42)).isoformat()
        ac_query = '{"size": 1000, "query": {"filtered":{"filter":{"and":[%s, %s]}}}}' % (range,nstat)
        accounted_entries = es.search(index=ES_INDICES, body=ac_query).get('hits').get('hits')
        for entry in accounted_entries:
            entry['_source']['status'] = 4
            es.index(entry['_index'], 'clock_entry', entry['_source'], id=entry['_id'])

        Index = date.strftime('%Y-%U')
        if es.indices.exists(Index):

            # Midnigh open/close procedure
            term = '{"term":{"status":0}}'
            new_query = '{"size": 1000, "query": {"filtered":{"filter": %s }}}' % term
            open_entries = es.search(index=Index, body=new_query).get('hits').get('hits')
            for new_entry in open_entries:
                    new_entry['_source']['worked'] = (date - stripdecimal(new_entry['_source']['start'])).total_seconds()
                    new_entry['_source']['start'] = date.isoformat()
                    es.index(index=Index, doc_type='clock_entry', body=new_entry['_source'])

            new_range = '{"range": {"start": {"lt": "%s"}}}' % date.isoformat()
            close_query = '{"size": 1000, "query": {"filtered":{"filter":{"and":[%s, %s]}}}}' % (new_range,term)
            close_entries = es.search(index=Index, body=close_query).get('hits').get('hits')
            for entry in close_entries:
                    entry['_source']['status'] = 1
                    entry['_source']['end'] = date.isoformat()
                    entry['_source']['ID'] = entry['_id']
                    es.index(Index, 'clock_entry', entry['_source'], id=entry['_id'])

