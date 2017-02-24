{% if 'clock' in grains['id'] %}
psql-pkg-repo:
    pkgrepo.managed:
        - ppa: ubuntugis/ppa 
{% endif %}
psql-packages:
    pkg.installed:
        - names:
            - postgresql-{{ pillar['database']['version'] }}
            - postgresql-client
            - postgresql-contrib {% if 'clock' in grains['id'] %}
            - postgresql-{{ pillar['database']['version'] }}-postgis-2.0 {% endif %}

pg_hba.conf:
    file.managed:
        - name: /etc/postgresql/{{ pillar['database']['version'] }}/main/pg_hba.conf
        - source: salt://postgres/pg_hba.conf
        - user: postgres
        - template: jinja
        - group: postgres
        - mode: 644
        - require:
            - pkg: postgresql-{{ pillar['database']['version'] }}

postgresql.conf:
    file.managed:
        - name: /etc/postgresql/{{ pillar['database']['version'] }}/main/postgresql.conf
        - source: salt://postgres/postgresql.conf
        - user: postgres
        - template: jinja
        - group: postgres
        - mode: 644
        - require:
            - pkg: postgresql-{{ pillar['database']['version'] }}

postgresql:
    service.running:
        - enable: True
        - watch:
            - file: /etc/postgresql/{{ pillar['database']['version'] }}/main/pg_hba.conf
            - file: /etc/postgresql/{{ pillar['database']['version'] }}/main/postgresql.conf

dbuser:
    postgres_user.present:
        - name: {{ pillar['database']['user'] }}
        - password: {{ pillar['database']['password'] }}
        - user: postgres
        - createdb: True
        - superuser: True

database:
    postgres_database.present:
        - name: {{ pillar['database']['name'] }}
        - owner: {{ pillar['database']['user'] }}
        - encoding: UTF8
        - lc_ctype: en_US.UTF8
        - lc_collate: en_US.UTF8
        - template: template0
        - require:
            - postgres_user: dbuser
{% if 'clock' in grains['id'] %}
postgis:
    postgres_extension.present:
        - maintenance_db: {{ pillar['database']['name'] }}
        - db_user: {{ pillar['database']['user'] }}
        - db_password: {{ pillar['database']['password'] }}
        - require:
            - pkg: postgresql-{{ pillar['database']['version'] }}
{% endif %}
psql-requirements:
    pkg.installed:
        - names:
            - duplicity
            - python-paramiko 
            - python-gobject-2

/opt/server:
    file.directory:
        - makedirs: True
        - user: root
        - group: root
        - mode: 555

/opt/server/sql:
    file.directory:
        - makedirs: True
        - user: postgres
        - group: root
        - mode: 555

