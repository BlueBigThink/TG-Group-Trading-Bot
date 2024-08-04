# Generated by Django 5.0.7 on 2024-08-04 12:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tg_bot_app', '0002_depositmodel'),
    ]

    operations = [
        migrations.CreateModel(
            name='WithdrawModel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user_id', models.BigIntegerField(max_length=100)),
                ('token_type', models.CharField(max_length=10)),
                ('amount', models.FloatField()),
                ('tx', models.CharField(max_length=255)),
                ('withdraw_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'tbl_withdraw_history',
            },
        ),
    ]