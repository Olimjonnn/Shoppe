# Generated by Django 3.2.9 on 2022-07-26 09:57

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0006_alter_review_rating_alter_review_text'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='user',
            options={'verbose_name': 'user', 'verbose_name_plural': 'users'},
        ),
    ]
