essentials:
    pkg.installed:
        - names:
            - build-essential
            - libpq-dev
            - postgresql-client
            - curl
            - vim
            - git-core
            - ruby {% if 'clock' in grains['id'] %}
            - rubygems  {% endif %}

python-stuff:
    pkg.installed:
        - names:
            - python2.7-dev
            - python-setuptools
            - python-pip
            - python-dev
            - python-virtualenv
            - libzmq-dev
            - libevent-dev

imaging-stuff:
    pkg.installed:
        - names:
            - libtiff4-dev
            - libjpeg8-dev
            - zlib1g-dev
            - libfreetype6-dev
            - liblcms1-dev
            - tcl8.5-dev
            - tk8.5-dev
            - python-imaging

{% for link in pillar['imaging-link'] %}
{{ link }}-links:
    file.symlink:
        - name: /usr/lib/{{ link }}.so
        - target: /usr/lib/x86_64-linux-gnu/{{ link }}.so
{% endfor %}


/etc/hosts:
    file.managed:
        - source: salt://hosts/hosts
        - template: jinja

#banner:
#    file.managed:
#        - name: /etc/motd
#        - source: salt://ascii/{{ grains['host'] }}
