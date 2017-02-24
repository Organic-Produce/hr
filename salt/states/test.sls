{% for host, hostinfo in  salt['mine.get']('*', 'grains.items').items() %}

    {{ hostinfo['ip_interfaces']['eth0'] }}
    {{ hostinfo['ip_interfaces']['eth0'][0] }}

{% endfor %}

{{ grains['ip_interfaces'] }}
{{ grains['ip_interfaces']['eth0'] }}
{{ grains['ip_interfaces']['eth0'][0] }}

