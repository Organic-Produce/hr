domain: http://clock.local:8080/

elasticsearch:
    engine: haystack.backends.elasticsearch_backend.ElasticsearchSearchEngine
    url: http://localhost:9200/
    data: /var/lib/elasticsearch/elasticsearch
    host: localhost

rabbit:
    host: localhost
    user: clock
    password: clock
    port: 5672

database:
    engine: django.contrib.gis.db.backends.postgis
    name: clock
    user: clock_data
    password: clock
    host: localhost
    port: 5432
