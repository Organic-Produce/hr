from django.db import models
from django.core.validators import MaxValueValidator
from django.contrib.auth.models import BaseUserManager, AbstractUser
from django.utils.translation import ugettext_lazy as _

EMPLOYMENT_TYPES = (
    (1, _('Full Time')),
    (2, _('Part Time')),
    (3, _('Floater')),
)

REMINDER_TYPES = (
    (0, _('No reminder')),
    (120, _('Every 2 hours')),
    (300, _('Every 5 hours')),
)

PAY_TYPES = (
    (1, _('Hourly')),
    (2, _('Salary')),
)

PAY_PERIODS = (
    (2, _('Biweekly')),
    (3, _('Monthly')),
)

EXEMPT_TYPES = (
    (0, _('Exempt')),
    (1, _('Non exempt')),
)

SITE_BOUND = (
    (0, _('Un-restrcited')),
    (1, _('Restricted')),
)

GEO_FENCING = (
    (0, _('No Geofencing')),
    (5, _('5 minutes')),
    (15, _('15 minutes')),
    (30, _('30 minutes')),
)

STATE_CHOICES = (
    ('al', 'Alabama'),
    ('ak', 'Alaska'),
    ('az', 'Arizona'),
    ('ar', 'Arkansas'),
    ('ca', 'California'),
    ('co', 'Colorado'),
    ('ct', 'Connecticut'),
    ('de', 'Delaware'),
    ('fl', 'Florida'),
    ('ga', 'Georgia'),
    ('hi', 'Hawaii'),
    ('id', 'Idaho'),
    ('il', 'Illinois'),
    ('in', 'Indiana'),
    ('ia', 'Iowa'),
    ('ks', 'Kansas'),
    ('ky', 'Kentucky'),
    ('la', 'Louisiana'),
    ('me', 'Maine'),
    ('md', 'Maryland'),
    ('ma', 'Massachusetts'),
    ('mi', 'Michigan'),
    ('mn', 'Minnesota'),
    ('ms', 'Mississippi'),
    ('mo', 'Missouri'),
    ('mt', 'Montana'),
    ('ne', 'Nebraska'),
    ('nv', 'Nevada'),
    ('nh', 'New Hampshire'),
    ('nj', 'New Jersey'),
    ('nm', 'New Mexico'),
    ('ny', 'New York'),
    ('nc', 'North Carolina'),
    ('nd', 'North Dakota'),
    ('oh', 'Ohio'),
    ('ok', 'Oklahoma'),
    ('or', 'Oregon'),
    ('pa', 'Pennsylvania'),
    ('ri', 'Rhode Island'),
    ('sc', 'South Carolina'),
    ('sd', 'South Dakota'),
    ('tn', 'Tennessee'),
    ('tx', 'Texas'),
    ('ut', 'Utah'),
    ('vt', 'Vermont'),
    ('va', 'Virginia'),
    ('wa', 'Washington'),
    ('wv', 'West Virginia'),
    ('wi', 'Wisconsin'),
)

IOS_CHOICES = (
    (1, 'AutomotiveNavigation'),
    (2, 'OtherNavigation'),
    (3, 'Fitness'),
    (4, 'Other'),
)

ACCURACY_CHOICES = (
    (0, '0 - high power use'),
    (10, '10'),
    (100, '100'),
    (1000, '1000 - low power use'),
)

MARITAL_CHOICES = (
    ('si', 'Single'),
    ('ma', 'Married'),
)

STATUSES = (
    (0, 'None'),
    (1, 'New'),
    (2, 'Submitted'),
    (3, 'Selected'),
    (4, 'Invited'),
    (5, 'Testing'),
    (6, 'Rejected'),
    (7, 'Hired'),
)

class Profile(AbstractUser):
    employment_type = models.IntegerField(max_length=16, choices=EMPLOYMENT_TYPES, default=1, verbose_name=_("Employment type"), help_text=_("<small>Time rounding <b>OFF</b> for <i>Floater</i> only</small>"))
    pay_type = models.IntegerField(max_length=16, choices=REMINDER_TYPES, default=1, verbose_name=_("Rest reminder"))
    pay_period = models.IntegerField(max_length=16, choices=PAY_PERIODS, default=2, verbose_name=_("Pay period"))
    overtime = models.IntegerField(max_length=16, choices=EXEMPT_TYPES, default=1, verbose_name=_("Overtime"))
    salary = models.DecimalField(max_digits=16, decimal_places=2, default=7.25, verbose_name=_("Salary"))
    geo_frecuency = models.IntegerField(max_length=16, default=0, choices=GEO_FENCING, verbose_name=_("Geofencing frequency"))
    geo_radius = models.IntegerField(max_length=16, choices=SITE_BOUND, default=1, verbose_name=_('Geo location'))
    desired_accuracy = models.IntegerField(max_length=16, default=1000, choices=ACCURACY_CHOICES, null=True, blank=True)
    stationary_radius = models.PositiveIntegerField(default=0,validators=[MaxValueValidator(1000)], null=True, blank=True)
    distance_filter = models.PositiveIntegerField(default=0,validators=[MaxValueValidator(1000)], null=True, blank=True)
    location_timeout = models.PositiveIntegerField(default=0,validators=[MaxValueValidator(1000)], help_text="<small>Only Android</small>", null=True, blank=True)
    IOS_config = models.IntegerField(max_length=16, default=4, choices=IOS_CHOICES, help_text="<small>Only IOS</small>", null=True, blank=True)

    employees = models.ManyToManyField('profiles.Profile', related_name='employers', null=True, blank=True, verbose_name=_("Employees"))

    @property
    def employer_count(self):
        return self.employers.count()

    @property
    def employer_pk_list(self):
        return [employer.pk for employer in self.employers.all()]

    @property
    def employee_pk_list(self):
        return [employee.pk for employee in self.employees.all()]

    @property
    def employees_sites_pk_list(self):
        site_lists = [worker.sites.all() for worker in self.employees.all()]
        pk_list = []
        for sitel in site_lists :
            if sitel :
                for site in sitel : pk_list.append(site.pk)
        return pk_list

    @property
    def schedules(self):
        return [site.schedule_set.get(worker_id=self.pk) for site in self.sites.all()]

    @property
    def groups_list(self):
        return [group for group in self.groups.all()]

    @property
    def instances(self):
        from clock.models import Instance
        return Instance.objects.filter(name__in=[group.name.split(' ')[0] for group in self.groups.all()])

    class Meta:
        db_table = 'clock_profiles'

    def __unicode__(self):
        return self.get_full_name()

    class Migration:
        needed_by = (( 'authtoken', '0001_initial'),)

class Applicant(Profile):
    birth_date = models.DateField(null=True)
    address = models.CharField(max_length=512, null=True)
    city = models.CharField(max_length=256, null=True)
    state = models.CharField(max_length=2, choices=STATE_CHOICES, default='tx')
    zip = models.CharField(max_length=9, null=True)
    emergency_contact = models.CharField(max_length=512, null=True)
    marital_status = models.CharField(max_length=2, choices=MARITAL_CHOICES, default='si')
    social_security = models.CharField(max_length=9, null=True, blank=True)
    licence_number = models.CharField(max_length=9, null=True, blank=True)
    licence_expiration = models.DateField(null=True, blank=True)
    licence_state = models.CharField(max_length=2, choices=STATE_CHOICES, default='tx', null=True, blank=True)
    weekdays = models.BooleanField(default=False)
    weekends = models.BooleanField(default=False)
    first = models.BooleanField(default=False)
    second = models.BooleanField(default=False)
    third = models.BooleanField(default=False)
    criminal_record = models.BooleanField(default=False)
    criminal_note = models.CharField(max_length=512, null=True, blank=True)
    resume = models.FileField(upload_to=".", null=True, blank=True)
    status = models.IntegerField(max_length=2, choices=STATUSES, default=1, editable=False)
    note = models.CharField(max_length=512, null=True, blank=True, editable=False)
    available_by = models.DateField(null = True)

    def __unicode__(self): return self.username

