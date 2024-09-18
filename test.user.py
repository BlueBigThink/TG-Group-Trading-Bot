class User:
    def init(self,id) -> None:
        self.Id = id
        self.EVM_Address = None       #evm地址
        self.EVM_key = None           #evm私钥
        self.SOL_Adress = None        #SOL 地址
        self.SOL_key = None           #实际私钥
        self.SOL_RAW = None           #原始list sol
        self.SOL_key_export = None    #导出用私钥
        self.mode = misc.BSC               #什么链
        self.gas = 10                 #Gas费用
        self.slippage = 0.1           #滑点
        self.Language = misc.CN            #语言
        self.cprice = 0.05     #默认价格
        self.inviter = None
        self.history = {misc.BSC:{},misc.SOL:{}}