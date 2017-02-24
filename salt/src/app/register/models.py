from django.db import models
from profiles.models import Applicant

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

PHONE_CHOICES = (
    ('m', 'Mobile'),
    ('h', 'Home'),
)

DOCUMENT_CHOICES = (
    ('a', 'Certificate'),
    ('b', 'Medical Record'),
)

class Telephone_number(models.Model):
    id = models.AutoField(primary_key=True)
    number = models.CharField(max_length=512, default='')
    type = models.CharField(max_length=2, choices=PHONE_CHOICES, default='m')
    applicant = models.ForeignKey(Applicant, related_name='telephones')

    @models.permalink
    def get_absolute_url(self):
        return ('register_detail_telephone', (), {'pk': self.pk})

class Previous_Job(models.Model):
    id = models.AutoField(primary_key=True)
    place = models.CharField(max_length=512, default='')
    state = models.CharField(max_length=2, choices=STATE_CHOICES, default='tx')
    date_ended = models.DateField()
    applicant = models.ForeignKey(Applicant, related_name='worked')

    @models.permalink
    def get_absolute_url(self):
        return ('register_detail_job', (), {'pk': self.pk})

class Education(models.Model):
    id = models.AutoField(primary_key=True)
    place = models.CharField(max_length=512, default='')
    year = models.IntegerField(max_length=4, default=1900)
    state = models.CharField(max_length=2, choices=STATE_CHOICES, default='tx')
    applicant = models.ForeignKey(Applicant, related_name='education')

    @models.permalink
    def get_absolute_url(self):
        return ('register_detail_education', (), {'pk': self.pk})

class Extra_document(models.Model):
    id = models.AutoField(primary_key=True)
    description = models.CharField(max_length=512, default='')
    document = models.FileField(upload_to='.')
    type = models.CharField(max_length=2, choices=DOCUMENT_CHOICES, null=True, editable=False)
    applicant = models.ForeignKey(Applicant, related_name='documentation')

    @models.permalink
    def get_absolute_url(self):
        return ('register_detail_document', (), {'pk': self.pk})

