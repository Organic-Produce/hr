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
        optparse.make_option('-m', '--mapping',
            type='string',
            dest='mapping',
            default=None,
            help='Mapping to be used by .'),
    )

    def handle(*args, **options):
        es = elasticsearch.Elasticsearch(es_host)

        Index = 'productos'

        create_options = {
            'index': Index
        }

        if options['mapping']:
            create_options['body'] = json.loads(open(options['mapping'], 'r').read())

        if not es.indices.exists(Index):
            es.indices.create(**create_options)
