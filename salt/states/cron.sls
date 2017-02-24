UTC:
    timezone.system:
        - utc: True

/home/clock/env/bin/python /home/clock/src/app/manage.py create_index -m /home/clock/src/app/dataprep/mappings/entry.json > /tmp/week :
    cron.present:
        - identifier: WEEK
        - user: root
        - minute: 0
        - hour: 0
        - dayweek: 0

/home/clock/env/bin/python /home/clock/src/app/manage.py create_index -m /home/clock/src/app/dataprep/mappings/entry.json > /tmp/year :
    cron.present:
        - identifier: YEAR
        - user: root
        - minute: 0
        - hour: 0
        - daymonth: 1
        - month: 1

/home/clock/env/bin/python /home/clock/src/app/manage.py create_index -t /home/clock/src/app/dataprep/mappings/taxmap.json > /tmp/t-week :
    cron.present:
        - identifier: TWEEK
        - user: root
        - minute: 0
        - hour: 0
        - dayweek: 0

/home/clock/env/bin/python /home/clock/src/app/manage.py create_index -t /home/clock/src/app/dataprep/mappings/taxmap.json > /tmp/t-year :
    cron.present:
        - identifier: TYEAR
        - user: root
        - minute: 0
        - hour: 0
        - daymonth: 1
        - month: 1

/home/clock/env/bin/python /home/clock/src/app/manage.py week_ending:
    cron.present:
        - identifier: MIDNIGHT
        - user: root
        - minute: 0
        - hour: 6
        - dayweek: 0,1,2,3,4,5,6

/home/clock/env/bin/python /home/clock/src/app/manage.py force_clockout:
    cron.present:
        - identifier: FORCECO
        - user: root
        - minute: 50
        - hour: 4,8
        - dayweek: 0,1,2,3,4,5,6
