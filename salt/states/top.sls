base:
    '*':
        - users
        - requirements
        - vim

    # Local dev servers
    '*local':
        - postgres
        - elasticsearch
        - rabbitmq
        - cron

    'pidgey*':
        - rabbitmq

    'pidgei*':
        - django
        - rabbitmq

    'squirtle*':
        - webserver
        - cron
        - logstash

    'charmander*':
        - elasticsearch

    'bulbasaur*':
        - postgres

    'mosquito*':
        - webserver

    'cucaracha*':
        - webserver
        - logstash

    'tequila*':
        - postgres
        - elasticsearch

    'mezcal*':
        - webserver

