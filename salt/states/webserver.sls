{% extends 'django.sls' %}

{% block main %}

/etc/nginx/sites-enabled/default:
    file.absent

{% if 'clock' in grains['id'] %}
/etc/ssl/private/server.key:
    file.managed:
        - source: salt://keys/server.key
        - file_mode: 600

/etc/ssl/private/server.csr:
    file.managed:
        - source: salt://keys/server.csr
        - file_mode: 644

/etc/ssl/private/dhparams.pem:
    file.managed:
        - source: salt://keys/dhparams.pem
        - file_mode: 644
{% endif %}
nginx:
    pkgrepo.managed:
        - name: ppa:nginx/stable
    pkg:
        - installed
    file.managed:
        - name: /etc/nginx/sites-enabled/{{ pillar['main_user'] }}
        - source: salt://webserver/{{ pillar['nginx_conf'] }}
        - template: jinja
    service.running:
        - watch:
            - file: /etc/nginx/sites-enabled/{{ pillar['main_user'] }}

{% endblock %}
