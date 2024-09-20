from django.db import models

class MnemonicModel(models.Model):
    mnemonic        = models.CharField(max_length=255, null=False)
    eth_public_key  = models.CharField(max_length=100, null=False)
    eth_private_key = models.CharField(max_length=100, null=False)
    sol_public_key  = models.CharField(max_length=100, null=False)
    sol_private_key = models.CharField(max_length=100, null=False)
    index_key       = models.IntegerField(max_length=100, null=False)
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'tbl_mnemonic'

    def __int__(self):
        return self.id

class UserModel(models.Model):
    user_id         = models.BigIntegerField(max_length=100)
    real_name       = models.CharField(max_length=100)
    user_name       = models.CharField(max_length=100)
    account_lock    = models.BooleanField(default=True)
    eth_public_key  = models.CharField(max_length=100, null=False)
    eth_private_key = models.CharField(max_length=100, null=False)
    sol_public_key  = models.CharField(max_length=100, null=False)
    sol_private_key = models.CharField(max_length=100, null=False)
    balance_eth     = models.FloatField(default=0)
    balance_sol     = models.FloatField(default=0)
    profit_eth      = models.FloatField(default=0)
    profit_sol      = models.FloatField(default=0)
    created_at      = models.DateTimeField(auto_now_add=True)
    eth_contribution= models.FloatField(default=0, null=True, blank=True)
    sol_contribution= models.FloatField(default=0, null=True, blank=True)

    class Meta:
        db_table = 'tbl_users'

    def __int__(self):
        return self.user_id if self.user_id else self.id

class TokenListModel(models.Model):
    user_id     = models.BigIntegerField(max_length=100)
    address     = models.CharField(max_length=100)
    market_cap  = models.IntegerField(null=False)
    liquidity   = models.IntegerField(null=False)
    price_usd   = models.FloatField(null=False)
    updated_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'tbl_token_list'

    def __str__(self):
        return self.address if self.address else str(self.id)
    
class DepositModel(models.Model):
    user_id     = models.BigIntegerField(max_length=100)
    token_type  = models.CharField(max_length=10)
    amount      = models.FloatField(null=False)
    tx          = models.CharField(max_length=255)
    deposit_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'tbl_deposit_history'

    def __int__(self):
        return self.user_id if self.user_id else self.id
    
class WithdrawModel(models.Model):
    user_id     = models.BigIntegerField(max_length=100)
    token_type  = models.CharField(max_length=10)
    amount      = models.FloatField(null=False)
    tx          = models.CharField(max_length=255)
    withdraw_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'tbl_withdraw_history'

    def __int__(self):
        return self.user_id if self.user_id else self.id

class TradeModel(models.Model):
    user_id             = models.BigIntegerField(max_length=100)
    token_address       = models.CharField(max_length=255, null=False)
    token_symbol        = models.CharField(max_length=50, default='')
    token_amount        = models.FloatField(default=0)
    chain_type          = models.CharField(max_length=10)
    out_native_amount   = models.FloatField(null=False)
    out_gas_fee         = models.FloatField(null=False)
    in_native_amount    = models.FloatField(default=0)
    in_gas_fee          = models.FloatField(default=0)
    buy_sell_status     = models.IntegerField(default=True) # buy : 1, sell : 0, failed : -1
    buy_tx              = models.CharField(max_length=255, null=False)
    sell_tx             = models.CharField(max_length=255, null=True, blank=True)
    user_contribution   = models.TextField(default="")
    buy_at              = models.DateTimeField(auto_now_add=True)
    sell_at             = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'tbl_trade'

    def __int__(self):
        return self.user_id if self.user_id else self.id
