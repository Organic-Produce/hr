from django import template
from datetime import datetime
register = template.Library()

@register.filter(name='getatt')
def getatt(dict, att):
    attval = dict.get(att)

    return  attval

@register.filter(name='stripdecimal')
def stripdecimal(datestr):
    if datestr :
        decimal = datestr.find('.')
        space = datestr.find(' ')
        tzaware = datestr.find('+')
        if space >= 8 : datestr = datestr.replace(' ','T')
        if datestr.find(':') < 0 :
            datestr = datetime.strptime(datestr, '%Y-%m-%d')
        elif tzaware >= 10 and decimal >= 18 :
            datestr = datetime.strptime(datestr, '%Y-%m-%dT%H:%M:%S.%f+00:00')
            datestr = datestr.replace(microsecond=0)
            datestr = datestr.replace(second=0)
        elif tzaware >= 10 :
            datestr = datetime.strptime(datestr, '%Y-%m-%dT%H:%M:%S+00:00')
            datestr = datestr.replace(second=0)
        elif decimal >= 18 :
            datestr = datetime.strptime(datestr, '%Y-%m-%dT%H:%M:%S.%f')
            datestr = datestr.replace(microsecond=0)
            datestr = datestr.replace(second=0)
        elif decimal >= 8 :
            datestr = datetime.strptime(datestr, 'H:%M:%S.%f')
            datestr = datestr.replace(microsecond=0)
            datestr = datestr.replace(second=0)
        elif datestr.find(':') == datestr.rfind(':'):
            datestr = datetime.strptime(datestr, '%H:%M')
        elif datestr.find('T') == -1 :
            datestr = datetime.strptime(datestr, '%H:%M:%S')
            datestr = datestr.replace(second=0)
        else:
            datestr = datetime.strptime(datestr, '%Y-%m-%dT%H:%M:%S')
            datestr = datestr.replace(second=0)

    return  datestr

@register.filter(name='getpklist')
def getpklist(list):
    resp = ""
    for ob in list :
        resp += ob.pk.__str__()
        resp += ","
    resp = resp.strip(",")
    return resp
