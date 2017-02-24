{% if 'squirtle' in grains['id'] or 'cucaracha' in grains['id'] or 'mosquito' in grains['id'] %}
psql-pkg-repo:
    pkgrepo.managed:
        - ppa: ubuntugis/ppa {% endif %}

lxml-pkgs:
    pkg.installed:
        - names:
            - libxslt1-dev
            - libxml2-dev
            - libxml2
            - libproj-dev 
            - gdal-bin{% if 'squirtle' in grains['id'] or 'cucaracha' in grains['id'] or 'mosquito' in grains['id'] %}
            - postgresql-client 
            - postgresql-{{ pillar['database']['version'] }}-postgis-2.0 {% else %}
            - python-reportlab{% endif %} 

python-pip:
    pkg.installed

{{ pillar['directories']['env'] }}:
    file.directory:
        - dir_mode: 755
        #- file_mode: 644
        - user: {{ pillar['main_user'] }}
        - runas: {{ pillar['main_user'] }}
        - group: {{ pillar['main_user'] }}
    virtualenv.managed:
        - system_site_packages: False
        - user: {{ pillar['main_user'] }}
        - require:
            - file: {{ pillar['directories']['env'] }}

sass:
    gem.installed

python-pkgs:
    pip.installed:
        - bin_env: {{ pillar['directories']['env'] }} {% if 'shop' in grains['id'] %}
        - requirements: salt://django/shop-requirements {% else %}
        - requirements: salt://django/dev-requirements{% if 'local' in grains['id'] %}, salt://django/local-requirements{% endif %}{% endif %}
        - user: {{ pillar['main_user'] }}
        - require:
            - pkg: python-pip
{% if 'clock' in grains['id'] %}
{{ pillar['directories']['src'] }}/app/settings.py:
    file.managed:
        - makedirs: True
        - source: salt://django/settings.py
        - template: jinja
{% endif %}
{% if not grains['virtual'] == 'VirtualBox' %}
{{ pillar['directories']['src'] }}:
    file.recurse: 
        - source: salt://{{ pillar['module_app'] }}
        - include_empty: True
        - file_mode: 774
        - dir_mode: 774
        - user: {{ pillar['main_user'] }}
        - group: www-data
{% endif %}

upstart:
    file.managed:
        - name: /etc/init/uwsgi.conf
        - source: salt://webserver/upstart
        - template: jinja

/var/uwsgi:
    file.directory:
        - group: www-data
        - user: {{ pillar['main_user'] }}
        - mode: 775

/var/log/uwsgi.log:
    file.managed:
        - name: /var/log/uwsgi.log
        - user: www-data

uwsgi:
    pip:
        - installed
    file.managed:
        - name: {{ pillar['directories']['vassals'] }}/clock.ini
        - source: salt://webserver/uwsgi
        - makedirs: True
        - template: jinja
    service.running:
        - watch:
            - file: {{ pillar['directories']['vassals'] }}/clock.ini
            - file: {{ pillar['directories']['src'] }}
{% block main %}
{% endblock %}
