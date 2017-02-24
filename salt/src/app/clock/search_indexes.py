from haystack import indexes
from clock.models import Site

class SiteIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)

    name = indexes.CharField(model_attr='name')

    city = indexes.CharField(model_attr='city')
    state = indexes.CharField(model_attr='state')
    zip = indexes.CharField(model_attr='zip')
    address = indexes.CharField(model_attr='address')
    workers = indexes.MultiValueField(model_attr='workers_schedule')
    starttimes = indexes.MultiValueField(model_attr='workers_schedule')
    endtimes = indexes.MultiValueField(model_attr='workers_schedule')
    location = indexes.MultiValueField()
    centre = indexes.LocationField(model_attr='location__centroid')

    def get_model(self):
        return Site

    def prepare_workers(self, obj):
        return [schedule.instance.worker_id for schedule in obj.workers_schedule ]

    def prepare_endtimes(self, obj):
        times_list = []
        for schedule in obj.workers_schedule:
            if len(schedule.instance.entries.values()) != 0 :
                for schedule_entry in schedule.instance.entries.values():
                    times_list.append(schedule_entry['end'])
        return set(times_list)

    def prepare_starttimes(self, obj):
        times_list = []
        for schedule in obj.workers_schedule:
            if len(schedule.instance.entries.values()) != 0 :
                for schedule_entry in schedule.instance.entries.values():
                    times_list.append(schedule_entry['start'])
        return set(times_list)

    def prepare_location(self, obj):
        return obj.location.coords
