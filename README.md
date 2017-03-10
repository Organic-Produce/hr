## HR Power code

### Local deployment

- [Download](https://www.virtualbox.org/wiki/Downloads) [VirtualBox](https://www.virtualbox.org/). (*[windows installer](https://s3-us-west-2.amazonaws.com/clockwork-files/VirtualBox-5.1.14-112924-Win.exe)*)

- [Download](https://www.vagrantup.com/downloads.html) [Vagrant](https://www.vagrantup.com). (*[windows installer](https://s3-us-west-2.amazonaws.com/clockwork-files/vagrant_1.9.2.msi)*)
    
- Run,

    - vagrant box add clock https://s3-us-west-2.amazonaws.com/clockwork-files/hrpower.box (*beware*: the box is about 1Gb)
    - git pull (to update the code from *gitlab* -[this repository](https://gitlab.com/picassosweb/hrpower)-)
    - vagrant up (this will run the setup using the code in host directory **salt/src/app** for the webserver)
	
- Access:

    - **web**: http://localhost:8080/
	    - for admin: 
	        - username: clock
	        - passwd: clock
    - **Elasticsearch**: http://localhost:9209/_plugin/head/
    - **database**: *postgressql*
        - name: clock
        - user: clock_data
        - password: clock
        - host: localhost
        - port: 54324
    - **ssh**: ( username: clock , passwd: clock )
        - with either:
		    - vagrant ssh 
		    - ssh clock@localhost:2222
    	- activate-virtualenv
        - eg. to create the weekly index for elasticsearch:

<pre>

Using username "clock".
Authenticating with public key "imported-openssh-key"
Welcome to Ubuntu 12.04.5 LTS (GNU/Linux 3.2.0-123-generic-pae i686)

 * Documentation:  https://help.ubuntu.com/
New release '14.04.5 LTS' available.
Run 'do-release-upgrade' to upgrade to it.

Welcome to your Vagrant-built virtual machine.
Last login: Sun Mar  5 23:58:06 2017 from 10.0.2.2
------------------------------------------------------------
~ » cd CLOCK                                                        clock@clock
~CLOCK
------------------------------------------------------------
~CLOCK(branch:a7d4bdd*) » activate-virtualenv                       clock@clock
------------------------------------------------------------
~CLOCK(branch:a7d4bdd*) » python manage.py create_index -m dataprep/mappings/entry.json
No handlers could be found for logger "elasticsearch"
------------------------------------------------------------
~CLOCK(branch:a7d4bdd*) »                                           clock@clock
~CLOCK(branch:a7d4bdd*) » sudo service uwsgi restart
</pre>
