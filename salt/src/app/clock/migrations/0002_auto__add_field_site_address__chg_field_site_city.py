# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Site.address'
        db.add_column('clock_sites', 'address',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=512),
                      keep_default=False)


        # Changing field 'Site.city'
        db.alter_column('clock_sites', 'city', self.gf('django.db.models.fields.CharField')(max_length=256))

    def backwards(self, orm):
        # Deleting field 'Site.address'
        db.delete_column('clock_sites', 'address')


        # Changing field 'Site.city'
        db.alter_column('clock_sites', 'city', self.gf('django.db.models.fields.CharField')(max_length=512))

    models = {
        u'clock.site': {
            'Meta': {'object_name': 'Site', 'db_table': "'clock_sites'"},
            'address': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '512'}),
            'city': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location': ('django.contrib.gis.db.models.fields.PolygonField', [], {}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'state': ('django.db.models.fields.CharField', [], {'default': "'tx'", 'max_length': '2'}),
            'zip': ('django.db.models.fields.CharField', [], {'max_length': '9'})
        }
    }

    complete_apps = ['clock']