# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Telephone_number'
        db.create_table(u'profiles_telephone_number', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('number', self.gf('django.db.models.fields.CharField')(default='', max_length=512)),
            ('type', self.gf('django.db.models.fields.CharField')(default='m', max_length=2)),
            ('applicant', self.gf('django.db.models.fields.related.ForeignKey')(related_name='telephones', to=orm['profiles.Applicant'])),
        ))
        db.send_create_signal(u'profiles', ['Telephone_number'])

        # Adding model 'Applicant'
        db.create_table(u'profiles_applicant', (
            (u'profile_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['profiles.Profile'], unique=True, primary_key=True)),
            ('birth_date', self.gf('django.db.models.fields.DateField')(null=True)),
            ('address', self.gf('django.db.models.fields.CharField')(max_length=512, null=True)),
            ('city', self.gf('django.db.models.fields.CharField')(max_length=256, null=True)),
            ('state', self.gf('django.db.models.fields.CharField')(default='tx', max_length=2)),
            ('zip', self.gf('django.db.models.fields.CharField')(max_length=9, null=True)),
            ('emergency_contact', self.gf('django.db.models.fields.CharField')(max_length=512, null=True)),
            ('marital_status', self.gf('django.db.models.fields.CharField')(default='si', max_length=2)),
            ('social_security', self.gf('django.db.models.fields.CharField')(max_length=9, null=True)),
            ('licence_number', self.gf('django.db.models.fields.CharField')(max_length=9, null=True, blank=True)),
            ('licence_expiration', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('licence_state', self.gf('django.db.models.fields.CharField')(default='tx', max_length=2, null=True, blank=True)),
            ('availability', self.gf('django.db.models.fields.CharField')(default='wd', max_length=2)),
            ('shift', self.gf('django.db.models.fields.CharField')(default='f', max_length=2)),
            ('criminal_record', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('criminal_note', self.gf('django.db.models.fields.CharField')(max_length=512, null=True, blank=True)),
            ('resume', self.gf('django.db.models.fields.files.FileField')(max_length=100, null=True, blank=True)),
            ('status', self.gf('django.db.models.fields.IntegerField')(default=0, max_length=2)),
            ('note', self.gf('django.db.models.fields.CharField')(max_length=512, null=True, blank=True)),
        ))
        db.send_create_signal(u'profiles', ['Applicant'])

        # Adding model 'Extra_document'
        db.create_table(u'profiles_extra_document', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('description', self.gf('django.db.models.fields.CharField')(default='', max_length=512)),
            ('document', self.gf('django.db.models.fields.files.FileField')(max_length=100)),
            ('applicant', self.gf('django.db.models.fields.related.ForeignKey')(related_name='documentation', to=orm['profiles.Applicant'])),
        ))
        db.send_create_signal(u'profiles', ['Extra_document'])

        # Adding model 'Previous_Job'
        db.create_table(u'profiles_previous_job', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('place', self.gf('django.db.models.fields.CharField')(default='', max_length=512)),
            ('state', self.gf('django.db.models.fields.CharField')(default='tx', max_length=2)),
            ('date_ended', self.gf('django.db.models.fields.DateField')()),
            ('applicant', self.gf('django.db.models.fields.related.ForeignKey')(related_name='worked', to=orm['profiles.Applicant'])),
        ))
        db.send_create_signal(u'profiles', ['Previous_Job'])

        # Adding model 'Education'
        db.create_table(u'profiles_education', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('place', self.gf('django.db.models.fields.CharField')(default='', max_length=512)),
            ('year', self.gf('django.db.models.fields.IntegerField')(default=1900, max_length=4)),
            ('state', self.gf('django.db.models.fields.CharField')(default='tx', max_length=2)),
            ('applicant', self.gf('django.db.models.fields.related.ForeignKey')(related_name='education', to=orm['profiles.Applicant'])),
        ))
        db.send_create_signal(u'profiles', ['Education'])


    def backwards(self, orm):
        # Deleting model 'Telephone_number'
        db.delete_table(u'profiles_telephone_number')

        # Deleting model 'Applicant'
        db.delete_table(u'profiles_applicant')

        # Deleting model 'Extra_document'
        db.delete_table(u'profiles_extra_document')

        # Deleting model 'Previous_Job'
        db.delete_table(u'profiles_previous_job')

        # Deleting model 'Education'
        db.delete_table(u'profiles_education')


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
            'Meta': {'object_name': 'Profile', 'db_table': "'clock_profiles'"},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
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
            'overtime': ('django.db.models.fields.IntegerField', [], {'default': '1', 'max_length': '16'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'pay_period': ('django.db.models.fields.IntegerField', [], {'default': '2', 'max_length': '16'}),
            'pay_type': ('django.db.models.fields.IntegerField', [], {'default': '1', 'max_length': '16'}),
            'salary': ('django.db.models.fields.DecimalField', [], {'default': '7.25', 'max_digits': '16', 'decimal_places': '2'}),
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