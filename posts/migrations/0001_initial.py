# Generated by Django 3.0.6 on 2024-11-05 09:06

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('adminapp', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='PostCategory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.IntegerField(blank=True, null=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('modified_by', models.IntegerField(blank=True, null=True)),
                ('category_name', models.CharField(max_length=50)),
                ('description', models.CharField(blank=True, max_length=100, null=True)),
                ('is_archived', models.BooleanField(default=False)),
                ('iu_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='postcategory_iu', to='adminapp.IUMaster')),
            ],
            options={
                'db_table': 'PostCategory',
                'ordering': ['created_at'],
            },
        ),
    ]
