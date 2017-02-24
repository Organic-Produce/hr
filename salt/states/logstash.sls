openjdk-7-jre-headless:
    pkg.installed

/home/logstash/:
    file.directory:
        - makedirs: True
        - user: logstash
        - group: logstash
        - require:
            - user: logstash

/home/logstash/log/:
    file.directory:
        - makedirs: True
        - user: logstash
        - group: logstash
        - require:
            - user: logstash

/etc/logstash/:
    file.directory:
        - makedirs: True
        - user: logstash
        - group: logstash

/etc/logstash/logstash.conf:
    file.managed:
        - source: salt://elasticsearch/logstash.conf
        - template: jinja

/etc/init/logstash.conf:
    file.managed:
        - source: salt://elasticsearch/logstash.init

logstash:
    file.managed:
        - source: https://download.elasticsearch.org/logstash/logstash/logstash-1.2.2-flatjar.jar
        - source_hash: md5=f2ec9e54e13428ed6d5c96b218126a0e
        - name: /usr/share/logstash/logstash-latest-monolithic.jar
        - user: root
        - group: root
        - mode: 664
        - makedirs: True
        - require:
            - pkg: openjdk-7-jre-headless
    service:
        - running
        - watch:
            - file: /etc/init/logstash.conf
            - file: /etc/logstash/logstash.conf
        - require:
            - file: logstash
            - user: logstash
    user.present:
        - fullname: Logstash User
        - home: /home/logstash
        - system: true
