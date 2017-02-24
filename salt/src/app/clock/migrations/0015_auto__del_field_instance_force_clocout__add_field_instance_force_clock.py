# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting field 'Instance.force_clocout'
        db.delete_column('clock_instances', 'force_clocout')

        # Adding field 'Instance.force_clockout'
        db.add_column('clock_instances', 'force_clockout',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)


    def backwards(self, orm):
        # Adding field 'Instance.force_clocout'
        db.add_column('clock_instances', 'force_clocout',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)

        # Deleting field 'Instance.force_clockout'
        db.delete_column('clock_instances', 'force_clockout')


    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'clock.instance': {
            'Meta': {'object_name': 'Instance', 'db_table': "'clock_instances'"},
            'admin': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'instance'", 'to': u"orm['profiles.Profile']"}),
            'biweekly_parity': ('django.db.models.fields.IntegerField', [], {'default': '0', 'max_length': '1'}),
            'branch_list': ('django.db.models.fields.CommaSeparatedIntegerField', [], {'max_length': '1024', 'null': 'True', 'blank': 'True'}),
            'daily_notes': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'force_clockout': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'force_hours': ('django.db.models.fields.IntegerField', [], {'default': '9', 'max_length': '2'}),
            'ganlytics_code': ('django.db.models.fields.CharField', [], {'default': "'UA-53621908-1'", 'max_length': '16'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'iframes': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'manager_messages': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'memos': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'multi_manager': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'multi_site': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'personal_report': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'report': ('django.db.models.fields.IntegerField', [], {'default': '0', 'max_length': '1'}),
            'site': ('django.db.models.fields.related.ForeignKey', [], {'default': '1', 'to': u"orm['clock.Site']"}),
            'strict_restriction': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'url': ('django.db.models.fields.URLField', [], {'default': "'https://preprod.hrpower.com/'", 'max_length': '200'}),
            'user_configs': (u'select_multiple_field.models.SelectMultipleField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'week_ending_day': ('django.db.models.fields.IntegerField', [], {'default': '0', 'max_length': '2'}),
            'week_ending_hour': ('django.db.models.fields.IntegerField', [], {'default': '0', 'max_length': '2'})
        },
        u'clock.schedule': {
            'Meta': {'object_name': 'Schedule'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'site': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['clock.Site']"}),
            'worker': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['profiles.Profile']"})
        },
        u'clock.scheduleentry': {
            'Meta': {'object_name': 'ScheduleEntry'},
            'end': ('django.db.models.fields.TimeField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'schedule': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'entries'", 'to': u"orm['clock.Schedule']"}),
            'start': ('django.db.models.fields.TimeField', [], {}),
            'weekdays': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'})
        },
        u'clock.site': {
            'Meta': {'object_name': 'Site', 'db_table': "'clock_sites'"},
            'address': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '512'}),
            'city': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location': ('django.contrib.gis.db.models.fields.PolygonField', [], {'default': '[]'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'state': ('django.db.models.fields.CharField', [], {'default': "'tx'", 'max_length': '2'}),
            'workers': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'sites'", 'symmetrical': 'False', 'through': u"orm['clock.Schedule']", 'to': u"orm['profiles.Profile']"}),
            'zip': ('django.db.models.fields.CharField', [], {'max_length': '9'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'profiles.profile': {
            'IOS_config': ('django.db.models.fields.IntegerField', [], {'default': '4', 'max_length': '16', 'null': 'True', 'blank': 'True'}),
            'Meta': {'object_name': 'Profile', 'db_table': "'clock_profiles'"},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'desired_accuracy': ('django.db.models.fields.IntegerField', [], {'default': '1000', 'max_length': '16', 'null': 'True', 'blank': 'True'}),
            'distance_filter': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'null': 'True', 'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'employees': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'employers'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['profiles.Profile']"}),
            'employment_type': ('django.db.models.fields.IntegerField', [], {'default': '1', 'max_length': '16'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'geo_frecuency': ('django.db.models.fields.IntegerField', [], {'default': '0', 'max_length': '16'}),
            'geo_radius': ('django.db.models.fields.IntegerField', [], {'default': '1', 'max_length': '16'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Group']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'location_timeout': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'null': 'True', 'blank': 'True'}),
            'overtime': ('django.db.models.fields.IntegerField', [], {'default': '1', 'max_length': '16'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'pay_period': ('django.db.models.fields.IntegerField', [], {'default': '2', 'max_length': '16'}),
            'pay_type': ('django.db.models.fields.IntegerField', [], {'default': '1', 'max_length': '16'}),
            'salary': ('django.db.models.fields.DecimalField', [], {'default': '7.25', 'max_digits': '16', 'decimal_places': '2'}),
            'stationary_radius': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'null': 'True', 'blank': 'True'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Permission']"}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        }
    }

    complete_apps = ['clock']
