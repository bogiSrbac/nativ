# Generated by Django 3.1.1 on 2020-10-07 10:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fakture', '0004_auto_20201006_1401'),
    ]

    operations = [
        migrations.AddField(
            model_name='faktura',
            name='ident_brojevi',
            field=models.CharField(choices=[('210', '210'), ('220', '220'), ('230', '230'), ('240', '240'), ('300', '300'), ('400', '400')], default='210', max_length=5),
        ),
        migrations.AddField(
            model_name='ponuda',
            name='ident_brojevi',
            field=models.CharField(choices=[('210', '210'), ('220', '220'), ('230', '230'), ('240', '240'), ('300', '300'), ('400', '400')], default='210', max_length=5),
        ),
    ]