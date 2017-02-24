from django.contrib import admin
from profiles.models import Profile
from register.models import Applicant, Telephone_number, Previous_Job, Education, Extra_document
from django.contrib.auth.admin import UserAdmin
import floppyforms as forms

# Register your models here.
class ProfileAdmin(UserAdmin):
    list_display = ('username', 'last_name', 'first_name', 'employer_pk_list', 'groups_list' )
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Information', {'fields': (
            'first_name',
            'last_name',
            'email',
            'employment_type',
            'pay_type',
            'geo_radius',
        )}),
        ('App Configuration', {'fields': (
            'geo_frecuency',
            'desired_accuracy',
            'stationary_radius',
            'distance_filter',
            'location_timeout',
            'IOS_config',
        )}),
        ('Relationships', {'fields': ('employees',)}),
        ('Important dates', {'fields': ('last_login',)}),
        ('Permissions', {'fields': (
            'is_active',
            'is_staff',
            'is_superuser',
            'groups',
            'user_permissions'
        )}),
    )

class ApplicantAdminForm(forms.ModelForm):
    class Meta:
        model = Applicant

class PhonesInline(admin.StackedInline):
    model = Telephone_number
    extra = 0
    fields = ('number', 'type',)

class JobsInline(admin.StackedInline):
    model = Previous_Job
    extra = 0
    fields = ('place', 'state')

class StudiesInline(admin.StackedInline):
    model = Education
    extra = 0
    fields = ('place', 'state')

class DocsInline(admin.StackedInline):
    model = Extra_document
    extra = 0
    fields = ('description', 'document')

class ApplicantAdmin(admin.ModelAdmin):
    list_display = ('last_name', 'first_name', 'status', 'note', 'groups_list' )
    inlines = (PhonesInline,JobsInline,StudiesInline,DocsInline)
    radio_fields = {"employment_type": admin.HORIZONTAL, "marital_status": admin.HORIZONTAL, }
    form = ApplicantAdminForm

admin.site.register(Applicant, ApplicantAdmin)
admin.site.register(Profile, ProfileAdmin)
