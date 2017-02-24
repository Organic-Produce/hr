#!/home/clock/env/bin/python

import requests
import json
import time
import getpass

headers = {'content-type': 'application/json'}
base_url = 'https://valid.hrpower.com/api/'

username = 'za'#raw_input('Username: ').rstrip('\n')
password = '1997'#getpass.getpass()
li_data= { u'username': username, u'password': password }
token = requests.post(base_url+'user/token/', data=json.dumps(li_data), headers=headers)
if token.status_code == 200:
    token_json = json.loads(token.content)
    key = token_json['token']
    headers = {'Authorization': 'Token '+key, 'content-type': 'application/json'}
    print 'Got token for: %s' % username
else: print 'incorrect login'

location = '19.3262519,-99.1084216'

setup = requests.get(base_url+'user/setup/%s' % location, headers=headers)
#print setup.content
if setup.status_code == 200:
    setup_json= json.loads(setup.content)
    Employee = setup_json['full_name']
    print 'Atendiendo a: %s' %Employee
    if setup_json['rest_reminder'] != 0 : print u'No olvides tomar descansos cada %d horas' % setup_json['rest_reminder']
else: print setup.content

status = requests.get(base_url+'user/status/%s' % location, headers=headers)
#print status.content
if status.status_code ==200:
    status_json = json.loads(status.content)
    if status_json['status'] == 3 :
        location_id = status_json['data']['location_id']
        site_name = status_json['data']['site_name']
        in_data = {u'location_id': location_id,u'location_geo': location}
        clockin = requests.put(base_url+'entry/clockin/', data=json.dumps(in_data), headers=headers)
        clockin_json = json.loads(clockin.content)
        if clockin.status_code == 201 :
            print 'You have checked in at %s in %s' % (clockin_json['start'],site_name)

    if setup_json['geo_frecuency'] !=0 and status_json['status'] == 3 :
        print u'Estas atrapado en tanto no hagas ClockOut'
        i = 0
        time.sleep(15)
        status = requests.get(base_url+'user/status/%s' % location, headers=headers)
        #print status.content
        status_json = json.loads(status.content)
        while i < 4 and status_json['status'] == 2 :
            i += 1
            if i < 2 : location =  '19.325,-99.106'
            else : location = '19.28,-99.20'
            fence = {'location_id': location_id, 'location_geo': location}
            within = requests.post(base_url+'user/fence/', data=json.dumps(fence), headers=headers)
            if within.status_code == 100:
                within_json = json.loads(within.content)
                if within_json['within'] == 0 : print 'In fence'
                else: print 'Out fence'
            else : print within.content
            time.sleep(15)
            status = requests.get(base_url+'user/status/%s' % location, headers=headers)
            status_json = json.loads(status.content)
            #print status.content

else: print status.content

time.sleep(3)

status = requests.get(base_url+'user/status/%s' % location, headers=headers)
if status.status_code == 200 : 
  status_json = json.loads(status.content)
  if status_json['status'] == 2 :
    ID = status_json['data']
    in_data = {u'ID': ID, u'location_geo': location}
    clockout = requests.put(base_url+'entry/clockout/', data=json.dumps(in_data), headers=headers)
    clockout_json = json.loads(clockout.content)
    if clockout.status_code == 201 : print 'You checked out at %s' % clockout_json['end']
    time.sleep(3)
    in_data = {u'ID': ID}#, u'unvalidate': True }
    validate = requests.put(base_url+'entry/validate/', data=json.dumps(in_data), headers=headers)
    if validate.status_code == 201 : print "validated" #json.loads(validate.content)
else: print status.content

history = requests.get(base_url+'user/history/', headers=headers)
if history.status_code == 200 :
    history_json = json.loads(history.content)
    print 'Offset: %d' % history_json['offset']
    for ent in history_json['entries'][:5]:
        print ent #u'Start: '+ent.get('start')+u'\t End: '+ent.get('end')+u'\t Location: '+ent.get('site_name')
else: print history.content


