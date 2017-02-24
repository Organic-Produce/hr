bup index -u {{ pillar['elasticsearch']['data'] }} :
    cmd.run :
        - user : clock

bup save -n elasticsearch {{ pillar['elasticsearch']['data'] }} :
    cmd.run :
        - user : clock
        - require :
            - cmd : bup index -u {{ pillar['elasticsearch']['data'] }}
    
rsync -az /home/clock/.bup/ clock@clock.mew":"/opt/backups/elasticsearch :
    cmd.run :
        - user : clock
        - require :
            - cmd : bup save -n elasticsearch {{ pillar['elasticsearch']['data'] }} 

