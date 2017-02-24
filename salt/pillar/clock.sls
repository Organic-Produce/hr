main_user: clock
domain: http://hrpower.com/
master_ip: 172.31.44.152
module_app: app
nginx_conf: nginx

directories:
    src: /home/clock/src/app
    env: /home/clock/env
    logs: /home/clock/logs
    socket: /var/uwsgi/uwsgi.sock
    vassals: /etc/uwsgi/vassals

elasticsearch:
    engine: haystack.backends.elasticsearch_backend.ElasticsearchSearchEngine
    url: http://charmander.clock-internals.com:9200/
    data: /var/lib/elasticsearch/elasticsearch
    host: charmander.clock-internals.com

rabbit:
    host: pidgei.clock-internals.com
    user: clock
    password: eSCxjQPGawjdbHutrt2qPLn7XE
    port: 5672

database:
    engine: django.contrib.gis.db.backends.postgis
    name: clock
    user: clock_data
    password: wYU>tQ*5f95_D{H
    host: bulbasaur.clock-internals.com
    port: 5432
    version: 9.1

