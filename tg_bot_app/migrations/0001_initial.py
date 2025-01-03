# Generated by Django 5.0.7 on 2024-07-31 11:53

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='MnemonicModel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('mnemonic', models.CharField(max_length=255)),
                ('eth_public_key', models.CharField(max_length=100)),
                ('eth_private_key', models.CharField(max_length=100)),
                ('sol_public_key', models.CharField(max_length=100)),
                ('sol_private_key', models.CharField(max_length=100)),
                ('index_key', models.IntegerField(max_length=100)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'tbl_mnemonic',
            },
        ),
        migrations.CreateModel(
            name='TokenListModel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user_id', models.BigIntegerField(max_length=100)),
                ('address', models.CharField(max_length=100)),
                ('market_cap', models.IntegerField()),
                ('liquidity', models.IntegerField()),
                ('price_usd', models.FloatField()),
                ('updated_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'tbl_token_list',
            },
        ),
        migrations.CreateModel(
            name='UserModel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user_id', models.BigIntegerField(max_length=100)),
                ('real_name', models.CharField(max_length=100)),
                ('user_name', models.CharField(max_length=100)),
                ('account_lock', models.BooleanField(default=True)),
                ('eth_public_key', models.CharField(max_length=100)),
                ('eth_private_key', models.CharField(max_length=100)),
                ('sol_public_key', models.CharField(max_length=100)),
                ('sol_private_key', models.CharField(max_length=100)),
                ('balance_eth', models.FloatField(default=0)),
                ('balance_sol', models.FloatField(default=0)),
                ('profit_eth', models.FloatField(default=0)),
                ('profit_sol', models.FloatField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'tbl_users',
            },
        ),
    ]
