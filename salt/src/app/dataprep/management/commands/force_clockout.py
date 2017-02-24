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

