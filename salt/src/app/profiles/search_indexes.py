from haystack import indexes
from profiles.models import Profile, Applicant

class ProfileIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)

    first_name = indexes.CharField(model_attr='first_name')
    last_name = indexes.CharField(model_attr='last_name')

    email = indexes.CharField(model_attr='email')
    username = indexes.CharField(model_attr='username')
    last_login = indexes.DateTimeField(model_attr='last_login')

    employment_type = indexes.CharField(use_template=True)
    pay_type = indexes.CharField(use_template=True)

    schedules = indexes.MultiValueField(model_attr='schedules')
    last_location = indexes.LocationField(indexed=False)
    last_time = indexes.DateTimeField(indexed=False)

    geo_frecuency = indexes.IntegerField(model_attr='geo_frecuency')
    geo_radius = indexes.CharField(use_template=True)
    desired_accuracy = indexes.IntegerField(model_attr='desired_accuracy')
    stationary_radius = indexes.IntegerField(model_attr='stationary_radius')
    distance_filter = indexes.IntegerField(model_attr='distance_filter')
    location_timeout = indexes.IntegerField(model_attr='location_timeout')
    IOS_config = indexes.IntegerField(model_attr='IOS_config')
    pay_period = indexes.CharField(use_template=True)

    #employers = indexes.MultiValueField(model_attr='employers')
    employers = indexes.MultiValueField(model_attr='employer_pk_list')

    def get_model(self):
        return Profile

    def prepare_schedules(self, obj):
        if len(obj.schedules) != 0 :
            res = []
            for schedule in obj.schedules:
                for entry in schedule.entries.all():
                    res.append((entry.weekdays,entry.start,entry.end))
            return res

        else : return ''

    def prepare_employers(self, obj):
        return [employer.pk for employer in obj.employers.all()]

class ApplicantIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)

    first_name = indexes.CharField(model_attr='first_name')
    last_name = indexes.CharField(model_attr='last_name')
    username = indexes.CharField(model_attr='username')
    last_login = indexes.DateTimeField(model_attr='last_login')
    last_location = indexes.LocationField(indexed=False)
    last_time = indexes.DateTimeField(indexed=True)

    groups = indexes.CharField()
    social_security = indexes.CharField(model_attr='social_security')
    employers = indexes.MultiValueField(model_attr='employer_pk_list')

    def get_model(self):
        return Applicant

    def prepare_groups(self, obj):
        return [group.name for group in obj.groups.all()]
