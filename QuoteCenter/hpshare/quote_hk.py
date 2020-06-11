#coding:utf-8

import akshare as ak
import os

from  ._base import get_quotes

def get_hk_code(local = False):
    """获取港股的代码，从行情快照中抽取"""
    name = os.path.join(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),"config"),"hk_stocks.txt")
    if(local):
        ret = []
        with open(name,"r") as f:
            for code in f.readlines():
                ret.append(code.replace("\n",""))
        return ret
    else:
        df = ak.stock_hk_spot()
        ret = []
        for index,row in df.iterrows():
            ret.append("hk"+row["symbol"])
        with open(name,"w") as f:
            for code in ret:
                f.write(code)
                f.write("\n")
        return ret



def get_hk_shot(_symbols:list):
    """返回美股实时行情"""
    return get_quotes(_symbols,_handle_ret_str)


def _handle_ret_str(_quote_str):
    #temp_list = _quote_str.split(";")
    #_quote_str = _quote_str.replace("\n","").replace('var hq_str_gb_',"").replace('var hq_str_',"").replace('"',"").replace('=',",").replace(" ","")
    _quote_str =_quote_str.replace("\n","").replace('"',"").replace('=',",").replace(';',",")
    if(_quote_str==""):return None
    stocks_str = _quote_str.split("var hq_str_")[1:]  #分割
    stocks_li = [x.split(",")[:-1] for x in stocks_str]
    for i in range(len(stocks_li)-1, -1, -1):
        if(len(stocks_li[i])<3):del stocks_li[i]
    return stocks_li




