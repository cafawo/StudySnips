# Generated by Django 4.1 on 2024-03-22 08:26

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("snips", "0003_classroom_updated_at_snip_updated_at_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="snip",
            name="claim_attempts",
            field=models.IntegerField(default=0),
        ),
    ]
