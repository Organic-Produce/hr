duplicity --log-file /opt/server/database.log /opt/server rsync://clock@clock.mew//opt/backups/postgres :
    cmd.run :
        - user : root
        - env :
            - PASSPHRASE : clock    
