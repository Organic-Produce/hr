es-requirements:
    pkg.installed:
        - names:
            - openjdk-7-jre-headless
            - curl
            - bup

{{ pillar['elasticsearch']['data'] }}:
    file.directory:
        - user: elasticsearch
        - group: elasticsearch
        - makedirs: True
        - require:
            - pkg: es-package

es-package:
    pkg.installed:
        - name: elasticsearch
        - sources:
            - elasticsearch: https://download.elasticsearch.org/elasticsearch/elasticsearch/elasticsearch-1.0.1.deb
        - require:
            - pkg: es-requirements
es-conf:
    file.managed:
        - name: /etc/elasticsearch/elasticsearch.yml
        - replace: False
        - require:
            - pkg: es-package

es-service:
    service:
        - name: elasticsearch
        - running
        - watch:
            - file: /etc/elasticsearch/elasticsearch.yml
            # - file: /etc/security/limits.conf
