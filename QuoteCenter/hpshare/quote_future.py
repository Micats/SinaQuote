#coding:utf-8

import os

from  ._base import get_quotes

if __name__=="__main__":
    from ..utils import Util

from utils import Util


def filter_future():
    """过滤期货"""
    name = os.path.join(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),"config"),"future_stocks_unfilter.txt")
    ret = []
    prefix = "hf_"
    with open(name,"r",encoding="utf8") as f:
        for code in f.readlines():
            symbol = code.replace("\n","").split("\t")[0]
            ret.append(prefix+symbol)
            if(symbol=="ZSD"):prefix = "nf_"
    name = os.path.join(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),"config"),"future_stocks.txt")
    with open(name,"w") as f:
        for code in ret:
            f.write(code)
            f.write("\n")
    return ret




def get_future_code(local = False):
    """获取期货的代码，从行情快照中抽取"""
    name = os.path.join(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),"config"),"future_stocks.txt")
    if(local):
        ret = []
        with open(name,"r") as f:
            for code in f.readlines():
                ret.append(code.replace("\n",""))
        return ret
    else:
        return None  #没有在线的



def get_future_shot(_symbols:list):
    """返回基金实时行情"""
    return get_quotes(_symbols,_handle_ret_str)


def _handle_ret_str(_quote_str):
    #temp_list = _quote_str.split(";")
    _quote_str =_quote_str.replace("\n","").replace('"',"").replace('=',",").replace(';',",")
    if(_quote_str==""):return None
    stocks_str = _quote_str.split("var hq_str_")[1:]  #分割
    stocks_li = [x.split(",")[:-1] for x in stocks_str]
    for i in range(len(stocks_li)-1, -1, -1):
        if(len(stocks_li[i])<3):
            del stocks_li[i]
            continue
        prefix,code =stocks_li[i][0].split("_")
        stocks_li[i][0] = code
        if(prefix=="hf"):stocks_li[i][2] = stocks_li[i][7]
        else:
            #print(stocks_li[i][2])
            try:
                stocks_li[i][2] = Util.time_str_to_str(stocks_li[i][2],"%H%M%S","%H:%M:%S")
            except:
                stocks_li[i].insert(2,stocks_li[i][38])  #上海的格式不太一样
                pass

    return stocks_li




