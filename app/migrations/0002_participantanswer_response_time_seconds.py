from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='participantanswer',
            name='response_time_seconds',
            field=models.FloatField(
                blank=True,
                null=True,
                verbose_name='Время ответа (сек)',
            ),
        ),
    ]
