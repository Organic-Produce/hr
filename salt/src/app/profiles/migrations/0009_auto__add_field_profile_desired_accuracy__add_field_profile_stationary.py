# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Profile.desired_accuracy'
        db.add_column('clock_profiles', 'desired_accuracy',
                      self.gf('django.db.models.fields.IntegerField')(default=1000, max_length=16),
                      keep_default=False)

        # Adding field 'Profile.stationary_radius'
        db.add_column('clock_profiles', 'stationary_radius',
                      self.gf('django.db.models.fields.PositiveIntegerField')(default=0),
                      keep_default=False)

        # Adding field 'Profile.distance_filter'
        db.add_column('clock_profiles', 'distance_filter',
                      self.gf('django.db.models.fields.PositiveIntegerField')(default=0),
                      keep_default=False)

        # Adding field 'Profile.location_timeout'
        db.add_column('clock_profiles', 'location_timeout',
                      self.gf('django.db.models.fields.PositiveIntegerField')(default=0),
                      keep_default=False)

        # Adding field 'Profile.IOS_config'
        db.add_column('clock_profiles', 'IOS_config',
                      self.gf('django.db.models.fields.IntegerField')(default=4, max_length=16),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'Profile.desired_accuracy'
        db.delete_column('clock_profiles', 'desired_accuracy')

        # Deleting field 'Profile.stationary_radius'
        db.delete_column('clock_profiles', 'stationary_radius')

        # Deleting field 'Profile.distance_filter'
        db.delete_column('clock_profiles', 'distance_filter')

        # Deleting field 'Profile.location_timeout'
        db.delete_column('clock_profiles', 'location_timeout')

        # Deleting field 'Profile.IOS_config'
        db.delete_column('clock_profiles', 'IOS_config')


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
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'profiles.applicant': {
            'Meta': {'object_name': 'Applicant', '_ormbases': [u'profiles.Profile']},
            'address': ('django.db.models.fields.CharField', [], {'max_length': '512', 'null': 'True'}),
            'availability': ('django.db.models.fields.CharField', [], {'default': "'wd'", 'max_length': '2'}),
            'birth_date': ('django.db.models.fields.DateField', [], {'null': 'True'}),
            'city': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True'}),
            'criminal_note': ('django.db.models.fields.CharField', [], {'max_length': '512', 'null': 'True', 'blank': 'True'}),
            'criminal_record': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'emergency_contact': ('django.db.models.fields.CharField', [], {'max_length': '512', 'null': 'True'}),
            'licence_expiration': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'licence_number': ('django.db.models.fields.CharField', [], {'max_length': '9', 'null': 'True', 'blank': 'True'}),
            'licence_state': ('django.db.models.fields.CharField', [], {'default': "'tx'", 'max_length': '2', 'null': 'True', 'blank': 'True'}),
            'marital_status': ('django.db.models.fields.CharField', [], {'default': "'si'", 'max_length': '2'}),
            'note': ('django.db.models.fields.CharField', [], {'max_length': '512', 'null': 'True', 'blank': 'True'}),
            u'profile_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['profiles.Profile']", 'unique': 'True', 'primary_key': 'True'}),
            'resume': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'shift': ('django.db.models.fields.CharField', [], {'default': "'f'", 'max_length': '2'}),
            'social_security': ('django.db.models.fields.CharField', [], {'max_length': '9', 'null': 'True'}),
            'state': ('django.db.models.fields.CharField', [], {'default': "'tx'", 'max_length': '2'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '0', 'max_length': '2'}),
            'zip': ('django.db.models.fields.CharField', [], {'max_length': '9', 'null': 'True'})
        },
        u'profiles.education': {
            'Meta': {'object_name': 'Education'},
            'applicant': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'education'", 'to': u"orm['profiles.Applicant']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'place': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '512'}),
            'state': ('django.db.models.fields.CharField', [], {'default': "'tx'", 'max_length': '2'}),
            'year': ('django.db.models.fields.IntegerField', [], {'default': '1900', 'max_length': '4'})
        },
        u'profiles.extra_document': {
            'Meta': {'object_name': 'Extra_document'},
            'applicant': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'documentation'", 'to': u"orm['profiles.Applicant']"}),
            'description': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '512'}),
            'document': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'profiles.previous_job': {
            'Meta': {'object_name': 'Previous_Job'},
            'applicant': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'worked'", 'to': u"orm['profiles.Applicant']"}),
            'date_ended': ('django.db.models.fields.DateField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'place': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '512'}),
            'state': ('django.db.models.fields.CharField', [], {'default': "'tx'", 'max_length': '2'})
        },
        u'profiles.profile': {
            'IOS_config': ('django.db.models.fields.IntegerField', [], {'default': '4', 'max_length': '16'}),
            'Meta': {'object_name': 'Profile', 'db_table': "'clock_profiles'"},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'desired_accuracy': ('django.db.models.fields.IntegerField', [], {'default': '1000', 'max_length': '16'}),
            'distance_filter': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'employees': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'employers'", 'symmetrical': 'False', 'to': u"orm['profiles.Profile']"}),
            'employment_type': ('django.db.models.fields.IntegerField', [], {'default': '1', 'max_length': '16'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'geo_frecuency': ('django.db.models.fields.IntegerField', [], {'default': '0', 'max_length': '16'}),
            'geo_radius': ('django.db.models.fields.IntegerField', [], {'default': '0', 'max_length': '16'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Group']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'location_timeout': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'overtime': ('django.db.models.fields.IntegerField', [], {'default': '1', 'max_length': '16'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'pay_period': ('django.db.models.fields.IntegerField', [], {'default': '2', 'max_length': '16'}),
            'pay_type': ('django.db.models.fields.IntegerField', [], {'default': '1', 'max_length': '16'}),
            'salary': ('django.db.models.fields.DecimalField', [], {'default': '7.25', 'max_digits': '16', 'decimal_places': '2'}),
            'stationary_radius': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Permission']"}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'profiles.telephone_number': {
            'Meta': {'object_name': 'Telephone_number'},
            'applicant': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'telephones'", 'to': u"orm['profiles.Applicant']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'number': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '512'}),
            'type': ('django.db.models.fields.CharField', [], {'default': "'m'", 'max_length': '2'})
        }
    }

    complete_apps = ['profiles']