from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('church_app', '0017_eventblock'),
    ]

    operations = [
        migrations.CreateModel(
            name='PodcastEpisode',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=300, verbose_name='Название')),
                ('speaker', models.CharField(blank=True, max_length=200, verbose_name='Спикер')),
                ('duration', models.CharField(blank=True, max_length=20, verbose_name='Длительность')),
                ('episode_url', models.URLField(blank=True, max_length=500, verbose_name='Ссылка на выпуск')),
                ('audio_url', models.URLField(blank=True, max_length=1000, verbose_name='Аудио')),
                ('order', models.PositiveIntegerField(default=0, verbose_name='Порядок')),
                ('is_active', models.BooleanField(default=True, verbose_name='Активен')),
            ],
            options={
                'verbose_name': 'Выпуск подкаста',
                'verbose_name_plural': 'Выпуски подкаста',
                'ordering': ['order', 'id'],
            },
        ),
    ]