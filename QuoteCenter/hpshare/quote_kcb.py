#coding : utf -8
import datetime
import re
import os
import pandas as pd
import requests
import json
from ._base import get_quotes

zh_sina_kcb_stock_payload = {
    "page": "1",
    "num": "80",
    "sort": "symbol",
    "asc": "1",
    "node": "kcb",
    "symbol": "",
    "_s_r_a": "auto"
}

#js股票行情，不使用此url获取行情，来获取code到本地
zh_sina_kcb_stock_url = "http://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeData"

#股票数量
zh_sina_kcb_stock_count_url = "http://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeStockCount?node=kcb"


def _get_zh_kcb_page_count() -> int:
    """
    所有股票的总页数
    http://vip.stock.finance.sina.com.cn/mkt/#hs_a
    :return: int 需要抓取的股票总页数
    """
    res = requests.get(zh_sina_kcb_stock_count_url)
    page_count = int(re.findall(re.compile(r"\d+"), res.text)[0]) / 80
    if isinstance(page_count, int):
        return page_count
    else:
        return int(page_count) + 1

def _get_kcb_spot() -> pd.DataFrame:
    """
    从新浪财经-A股获取所有A股的实时行情数据, 大量抓取容易封IP   不用此函数来获取行情，来获取code代码
    http://vip.stock.finance.sina.com.cn/mkt/#qbgg_hk
    :return: pandas.DataFrame
    """
    big_df = pd.DataFrame()
    page_count = _get_zh_kcb_page_count()
    zh_sina_stock_payload_copy = zh_sina_kcb_stock_payload.copy()
    for page in range(1, page_count+1):
        zh_sina_stock_payload_copy.update({"page": page})
        res = requests.get(
            zh_sina_kcb_stock_url,
            params=zh_sina_stock_payload_copy)
        try:
            data_json =json.loads(res.text)
        except:
            data_json = demjson.decode(res.text)
        big_df = big_df.append(pd.DataFrame(data_json), ignore_index=True)
    return big_df

def get_kcb_code(_local =False):
    name = os.path.join(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),"config"),"kcb_stocks.txt")
    if(_local):
        ret = []
        with open(name,"r",encoding="utf-8") as f:
            for code in f.readlines():
                ret.append(code.replace("\n",""))
        return ret
    else:
        df = _get_kcb_spot()
        ret =[] 
        for i,row in df.iterrows():
            ret.append("sh"+row["code"])

        with open(name,"w",encoding="utf-8") as fw:
            for code in ret:
                fw.write(code)
                fw.write("\n")

        return ret 


def get_kcb_shot(_symbols:list):
    """返回科创板实时行情"""
    return get_quotes(_symbols,_handle_ret_str)
    


def _handle_ret_str(_quote_str):
    temp_list = _quote_str.split(";")
    #_quote_str = _quote_str.replace("\n","").replace('var hq_str_gb_',"").replace('var hq_str_',"").replace('"',"").replace('=',",").replace(" ","")
    _quote_str =_quote_str.replace("\n","").replace('"',"").replace('=',",").replace(';',",")
    if(_quote_str==""):return None
    stocks_str = _quote_str.split("var hq_str_")  #分割
    stocks_li = [x.split(",")[:-1] for x in stocks_str]
    for i in range(len(stocks_li)-1, -1, -1):
        if(len(stocks_li[i])<3):del stocks_li[i]
    return stocks_li

if __name__=="__main__":
    li = get_kcb_code(False)
    ret = get_kcb_shot(li)
    print(ret)