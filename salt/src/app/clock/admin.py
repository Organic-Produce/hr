from django.contrib import admin
from utils.bitchoices import BitWidget
from clock.models import Site, Schedule, ScheduleEntry, Instance
import floppyforms as forms

class GMapWidget(forms.gis.BaseGMapWidget, forms.gis.PolygonWidget):
    map_srid = 900913 # Use the google projection

    class Media:
        js = (
            'http://openlayers.org/dev/OpenLayers.js',
             'floppyforms/js/MapWidget.js',
             'http://maps.google.com/maps/api/js?sensor=false',
)

class SiteAdminForm(forms.ModelForm):
    class Meta:
        model = Site
        widgets = {
            'location': GMapWidget
        }

class WorkersInline(admin.StackedInline):
    model = Site.workers.through
    extra = 0

    fields = ('worker', 'changeform_link',)
    readonly_fields = ('changeform_link',)

class ScheduleEntryForm(forms.ModelForm):
    class Meta:
        model = ScheduleEntry
#        widgets = {
#            'weekdays': BitWidget
#        }

class ScheduleEntryInline(admin.TabularInline):
    model = ScheduleEntry
    extra = 0
    form = ScheduleEntryForm

class ScheduleAdmin(admin.ModelAdmin):
    model = Schedule
    list_display = ('worker', 'site' )
    inlines = (ScheduleEntryInline,)

class SiteAdmin(admin.ModelAdmin):
    inlines = (WorkersInline,)
    form = SiteAdminForm

class InstanceAdmin(admin.ModelAdmin):
    model = Instance
    list_display = ('name', 'admin', 'site', 'url', 'ganlytics_code', 'multi_manager', 'multi_site', 'iframes', 'report', 'strict_restriction')

admin.site.register(Site, SiteAdmin)
admin.site.register(Instance, InstanceAdmin)
admin.site.register(Schedule, ScheduleAdmin)
