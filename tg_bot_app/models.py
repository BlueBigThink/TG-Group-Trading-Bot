from django.db import models

class Mnemonic(models.Model):
    mnemonic     = models.CharField(max_length=255)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'tbl_mnemonic'

    def __int__(self):
        return self.id

class User(models.Model):
    user_id = models.IntegerField()
    real_name = models.CharField(max_length=100)
    user_name = models.CharField(max_length=100)
    account_lock = models.BooleanField(default=True)
    public_key = models.CharField(max_length=100, null=False)
    private_key = models.CharField(max_length=100, null=False)
    deposit_eth = models.FloatField(default=0)
    deposit_sol = models.FloatField(default=0)
    profit_eth = models.FloatField(default=0)
    profit_sol = models.FloatField(default=0)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'tbl_users'

    def __int__(self):
        return self.user_id if self.user_id else self.id

class TokenList(models.Model):
    user_id = models.IntegerField()
    address     = models.CharField(max_length=100)
    market_cap = models.IntegerField(null=False)
    liquidity =  models.IntegerField(null=False)
    price_usd = models.FloatField(null=False)
    updated_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'tbl_token_list'

    def __int__(self):
        return self.user_id if self.user_id else self.id