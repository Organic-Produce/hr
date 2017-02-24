from django.core.management.base import BaseCommand, CommandError
from datetime import datetime

import elasticsearch
import optparse
import json
import logging
from django.conf import settings                                                                                                                            

es_host = settings.ELASTICSEARCH_HOST 

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        optparse.make_option('-a', '--alerts',
            type='string',
            dest='alerts',
            default=None,
            help='Mapping for alerts index.'),
        optparse.make_option('-m', '--mapping',
            type='string',
            dest='mapping',
            default=None,
            help='Mapping to be used by the new weekley index.'),
        optparse.make_option('-t', '--taxmap',
            type='string',
            dest='taxmap',
            default=None,
            help='Mapping to be used by the tax new weekley index.'),
        optparse.make_option('-c', '--clients',
            type='string',
            dest='clients',
            default=None,
            help='Mapping to be used by the tax client index.'),
    )

    def handle(*args, **options):
        es = elasticsearch.Elasticsearch(es_host)

        date = datetime.now()
        Index = date.strftime('%Y-%U')
        previous = date.strftime('%Y')+'-'+str(int(date.strftime('%U'))-1)

        if options['alerts']:
            Index = 'alerts'

        if options['taxmap']:
            Index = "t"+Index+"t"

        if options['clients']:
            Index = 'clients'

        create_options = {
            'index': Index
        }

        if options['mapping']:
            create_options['body'] = json.loads(open(options['mapping'], 'r').read())

        if options['alerts']:
            create_options['body'] = json.loads(open(options['alerts'], 'r').read())

        if options['taxmap']:
            create_options['body'] = json.loads(open(options['taxmap'], 'r').read())

        if options['clients']:
            create_options['body'] = json.loads(open(options['clients'], 'r').read())

        if not es.indices.exists(Index):
            es.indices.create(**create_options)

        if options['mapping']:
            if es.indices.exists(previous): # copy non closed entries to new index
                    term = '{"term":{"status":0}}'
                    query = '{"size": 1000, "query": {"filtered":{"filter": %s }}}' % term
                    open_entries = es.search(index=previous, body=query).get('hits').get('hits')
                    for entry in open_entries:
                        ndoc = es.index(index=Index, doc_type='clock_entry', body=entry['_source'])
                        entry['_source']['status'] = 5
                        es.index(previous, 'clock_entry', entry['_source'], id=entry['_id'])

        if options['taxmap']:
            previous = "t"+previous+"t"
            if es.indices.exists(previous): # copy non closed entries to new index
                    term = '{"term":{"status":0}}'
                    query = '{"size": 1000, "query": {"filtered":{"filter": %s }}}' % term
                    open_entries = es.search(index=previous, body=query).get('hits').get('hits')
                    for entry in open_entries:
                        ndoc = es.index(index=Index, doc_type='tax_entry', body=entry['_source'])
                        entry['_source']['status'] = 5
                        es.index(previous, 'tax_entry', entry['_source'], id=entry['_id'])
