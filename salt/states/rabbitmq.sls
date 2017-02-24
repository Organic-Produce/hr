add-rabbitmq-signing-key:
    cmd.run:
        - name: wget -q http://www.rabbitmq.com/rabbitmq-signing-key-public.asc -O- | sudo apt-key add -
        - unless: sudo apt-key list | grep RabbitMQ

rabbit-packages:
    pkgrepo.managed:
        - humanname: Rabbit Package
        - name: deb http://www.rabbitmq.com/debian/ testing main
        - key_url: http://www.rabbitmq.com/rabbitmq-signing-key-public.asc
    pkg.installed:
        - names:
            - rabbitmq-server

rabbitmq-service:
    service:
        - name: rabbitmq-server
        - running
        - enable: True
        - require:
            - pkg: rabbit-packages

management-console:
    cmd.run:
        - name: rabbitmq-plugins enable rabbitmq_management
        - user: root
        - require:
            - service: rabbitmq-service

rabbit-user:
    rabbitmq_user.present:
        - name: {{ pillar['rabbit']['user'] }}
        - password: {{ pillar['rabbit']['password'] }}
        - tags:
            - administrator
            - user
        - force: True
        - runas: root
        - perms:
            - '/':
                - '.*'
                - '.*'
                - '.*'
        - require:
            - cmd: management-console

rabbit-guest:
    rabbitmq_user.absent:
        - name: guest

rabbit-admin:
    cmd.run:
        - name: rabbitmqctl set_user_tags {{ pillar['rabbit']['user'] }} administrator
        - require:
            - rabbitmq_user: rabbit-user

rabbit-vhost:
    rabbitmq_vhost.present:
        - name: /
        - user: {{ pillar['rabbit']['user'] }}
        - conf: .*
        - write: .*
        - read: .*
        - require:
            - rabbitmq_user: rabbit-user
