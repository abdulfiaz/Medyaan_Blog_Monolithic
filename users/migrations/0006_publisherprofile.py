# Generated by Django 3.0.6 on 2024-11-05 11:37

from django.conf import settings
import django.contrib.postgres.fields
import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('adminapp', '0001_initial'),
        ('users', '0005_auto_20241029_1037'),
    ]

    operations = [
        migrations.CreateModel(
            name='PublisherProfile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.IntegerField(blank=True, null=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('modified_by', models.IntegerField(blank=True, null=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('experience', models.TextField(blank=True, null=True)),
                ('document', django.contrib.postgres.fields.ArrayField(base_field=django.contrib.postgres.fields.jsonb.JSONField(), blank=True, default=list, size=None)),
                ('website_link', models.TextField(blank=True, null=True)),
                ('approved_status', models.CharField(default='pending', max_length=50)),
                ('role_type', models.CharField(blank=True, max_length=50, null=True)),
                ('reason', models.TextField(blank=True, null=True)),
                ('is_rejected', models.BooleanField(default=False)),
                ('iu_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='publisher_iu', to='adminapp.IUMaster')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='publisher_user_id', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'publisher_profile',
                'ordering': ['created_at'],
            },
        ),
    ]
