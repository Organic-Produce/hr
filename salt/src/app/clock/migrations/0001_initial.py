# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Site'
        db.create_table('clock_sites', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=256)),
            ('state', self.gf('django.db.models.fields.CharField')(default='tx', max_length=2)),
            ('zip', self.gf('django.db.models.fields.CharField')(max_length=9)),
            ('city', self.gf('django.db.models.fields.CharField')(max_length=512)),
            ('location', self.gf('django.contrib.gis.db.models.fields.PolygonField')()),
        ))
        db.send_create_signal(u'clock', ['Site'])


    def backwards(self, orm):
        # Deleting model 'Site'
        db.delete_table('clock_sites')


    models = {
        u'clock.site': {
            'Meta': {'object_name': 'Site', 'db_table': "'clock_sites'"},
            'city': ('django.db.models.fields.CharField', [], {'max_length': '512'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location': ('django.contrib.gis.db.models.fields.PolygonField', [], {}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'state': ('django.db.models.fields.CharField', [], {'default': "'tx'", 'max_length': '2'}),
            'zip': ('django.db.models.fields.CharField', [], {'max_length': '9'})
        }
    }

    complete_apps = ['clock']