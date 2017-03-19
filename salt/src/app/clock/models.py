# -*- coding: utf-8 -*-
from django.contrib.gis.db import models
from django.core import urlresolvers
from django.contrib.gis.geos import Polygon
from django.contrib.auth.models import Group
from utils.bitchoices import BitChoices
from datetime import datetime,timedelta
from select_multiple_field.models import SelectMultipleField
from django.utils.translation import ugettext_lazy as _

STATE_CHOICES = (
    ('tx', 'Texas'),
    ('df', 'Ciudad de México'),
)

WEEKDAY_CHOICES = BitChoices((
    ('sun', 'Sunday'),
    ('mon', 'Monday'),
    ('tue', 'Tuesday'),
    ('wed', 'Wednesday'),
    ('thu', 'Thursday'),
    ('fri', 'Friday'),
    ('sat', 'Saturday'),
))

WEEK_DAYS=[]
base = datetime.now() - timedelta(days=datetime.now().weekday())
for d in range(0,7): WEEK_DAYS.append((d, (base+timedelta(days=d)).strftime('%A')))

DAY_HOURS=[]
for h in range(0,24): DAY_HOURS.append((h, h))

FORCE_HOURS=[]
for h in range(6,4): FORCE_HOURS.append((h, h))

FORMATS = (
    (0, 'Simple'),
    (1, 'Custom'),
)

RESTRICTIONS = (
    (0, 'Send data'),
    (1, 'Within site'),
)

CONFIGURATIONS = (
    ('geo_frecuency', 'Geofencing'),
    ('salary', 'Salary'),
    ('overtime', 'Overtime excemption'),
    ('pay_period', 'Pay period'),
    ('pay_type', 'Rest reminder'),
)

PARITY = (
    (0, 'Even'),
    (1, 'Odd'),
)

class Site(models.Model):
    name = models.CharField(max_length=256, editable=False, verbose_name=_("Name"))
    city = models.CharField(max_length=256, verbose_name=_("City"))
    state = models.CharField(max_length=2, choices=STATE_CHOICES, default='tx', verbose_name=_("State"))
    zip = models.CharField(max_length=9, verbose_name=_("ZIP"))
    address = models.CharField(max_length=512, default='', verbose_name=_("Address"))

    location = models.PolygonField(default=Polygon([[-108.61548,39.34060],[-108.62466,38.27049],[-107.19070,38.30412],[-107.21821,39.33449],[-108.61548,39.34060]]), verbose_name=_("Location"))
    workers = models.ManyToManyField('profiles.Profile', through='Schedule', related_name='sites', editable=False)

    @property
    def workers_schedule(self):
        return [schedule.entries for schedule in self.schedule_set.all()]

    objects = models.GeoManager()

    class Meta:
        db_table = 'clock_sites'

    def __unicode__(self): return self.name

class Instance(models.Model):
    name = models.CharField(max_length=256)
    admin = models.ForeignKey('profiles.Profile', related_name='instance')
    site = models.ForeignKey(Site, default=1)
    branch_list = models.CommaSeparatedIntegerField(max_length=1024,null=True, blank=True)
    ganlytics_code = models.CharField(max_length=16, default='UA-53621908-1')
    week_ending_day = models.IntegerField(max_length=2, choices=WEEK_DAYS, default=0)
    week_ending_hour = models.IntegerField(max_length=2, choices=DAY_HOURS, default=0)
    biweekly_parity = models.IntegerField(max_length=1, choices=PARITY, default=0)
    multi_manager = models.BooleanField(default=False)
    multi_site = models.BooleanField(default=False)
    iframes = models.BooleanField(default=False)
    report = models.IntegerField(max_length=1, choices=FORMATS, default=0)
    memos = models.BooleanField(default=False)
    personal_report = models.BooleanField(default=False) 
    daily_notes = models.BooleanField(default=False)
    manager_messages = models.BooleanField(default=False)
    force_clockout = models.BooleanField(default=False)
    force_hours = models.IntegerField(max_length=2, choices=FORCE_HOURS, default=9)
    user_configs = SelectMultipleField(max_length=50, choices=CONFIGURATIONS, null=True, blank=True)
    strict_restriction = models.BooleanField(default=False)
    url = models.URLField(default='https://preprod.hrpower.com/')
    class Meta:
        db_table = 'clock_instances'
    def __unicode__(self): return self.name

class Schedule(models.Model):
    site = models.ForeignKey(Site)
    worker = models.ForeignKey('profiles.Profile')

    def changeform_link(self):
        if self.id:
            changeform_url = urlresolvers.reverse(
                'admin:clock_schedule_change', args=(self.id,)
            )
            return '<a href="%s" target="_blank">Details</a>' % changeform_url
        return ''
    changeform_link.allow_tags = True
    changeform_link.short_description = ''

class ScheduleEntry(models.Model):
    id = models.AutoField(primary_key=True)
    start = models.TimeField()
    end = models.TimeField()

    weekdays = models.PositiveIntegerField(choices=WEEKDAY_CHOICES, default=0)

    schedule = models.ForeignKey(Schedule, related_name='entries')

class Task(models.Model):
    id = models.AutoField(primary_key=True)
    description = models.CharField(max_length=512, default='')
    worker = models.ForeignKey('profiles.Profile')