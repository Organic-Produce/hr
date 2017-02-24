zsh-shell:
    pkg.installed:
        - names:
            - zsh
            - git-core

www-data:
    group:
        - present

{{ pillar['main_user'] }}:
    user.present:
        - fullname: Server
        - home: /home/{{ pillar['main_user'] }}
        - shell: /bin/zsh
        - name: {{ pillar['main_user'] }}
        - gid_from_name: True
        - groups:
            - admin
            - www-data
    ssh_auth:
        - present
        - user: {{ pillar['main_user'] }}
        - names:
             {% for user in pillar['users'] %}
             - {{ user['key'] }}
             {% endfor %}
        - require:
            - user: {{ pillar['main_user'] }}

omz:
    git.latest:
        - name: https://github.com/robbyrussell/oh-my-zsh.git
        - rev: c79e5a97a906457d1778197bd4f29640d1917201
        - target: /home/{{ pillar['main_user'] }}/.oh-my-zsh
        - force:

/home/{{ pillar['main_user'] }}/.zshrc:
    file.managed:
        - user: {{ pillar['main_user'] }}
        - source: salt://zsh/zshrc
        - template: jinja

{% if grains['virtual'] == 'VirtualBox' %}
vagrant:
    ssh_auth:
        - present
        - user: {{ pillar['main_user'] }}
        - source: salt://keys/vagrant.pub
{% endif %}

/etc/sudoers:
    file.managed:
        - source: salt://sudo/sudoers
        - template: jinja
        - user: root
        - mode: 440
