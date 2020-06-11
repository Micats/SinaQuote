#coding:utf-8

import os

from  ._base import get_quotes


def filter_fund():
    name = os.path.join(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),"config"),"fund_stocks_unfilter.txt")
    ret = []
    with open(name,"r",encoding="utf8") as f:
        for code in f.readlines():
            symbol = code.replace("\n","").split("\t")[0]
            if(len(symbol)==8):
                ret.append(symbol)
            else:
                if(int(symbol[0:3])<500):ret.append("sz"+symbol)
                else:ret.append("sh"+symbol)
    name = os.path.join(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),"config"),"fund_stocks.txt")
    with open(name,"w") as f:
        for code in ret:
            f.write(code)
            f.write("\n")
    return ret




def get_fund_code(local = False):
    """获取港股的代码，从行情快照中抽取"""
    name = os.path.join(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),"config"),"fund_stocks.txt")
    if(local):
        ret = []
        with open(name,"r") as f:
            for code in f.readlines():
                ret.append(code.replace("\n",""))
        return ret
    else:
        return None  #没有在线的



def get_fund_shot(_symbols:list):
    """返回基金实时行情"""
    return get_quotes(_symbols,_handle_ret_str)


def _handle_ret_str(_quote_str):
    #temp_list = _quote_str.split(";")
    _quote_str =_quote_str.replace("\n","").replace('"',"").replace('=',",").replace(';',",")
    if(_quote_str==""):return None
    stocks_str = _quote_str.split("var hq_str_")[1:]  #分割
    stocks_li = [x.split(",")[:-1] for x in stocks_str]
    for i in range(len(stocks_li)-1, -1, -1):
        if(len(stocks_li[i])<3):del stocks_li[i]
    return stocks_li




