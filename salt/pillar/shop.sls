main_user: shop
domain: http://genetic.com.mx/
master_ip: 54.186.202.192
module_app: zapateria
nginx_conf: sh-nginx

directories:
    src: /home/shop/src/zapateria
    env: /home/shop/env
    logs: /home/shop/logs
    socket: /var/uwsgi/uwsgi.sock
    vassals: /etc/uwsgi/vassals

database:
    engine: django.db.backends.postgresql_psycopg2
    name: shop
    user: shop_data
    password: wYU>tQ*6f75_D{H
    host: tequila.shop-internals.com
    port: 5432
    version: 9.3

elasticsearch:
    engine: haystack.backends.elasticsearch_backend.ElasticsearchSearchEngine
    url: http://tequila.shop-internals.com:9200/
    data: /var/lib/elasticsearch/elasticsearch
    host: teqila.shop-internals.com

