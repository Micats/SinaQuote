# -*- coding:utf-8 -*-
# /usr/bin/env python


import datetime

import requests
import pandas as pd
import os
import re

from  ._base import get_quotes


zh_sina_index_stock_url = "http://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeDataSimple"
zh_sina_index_stock_payload = {
    "page": "1",
    "num": "80",
    "sort": "symbol",
    "asc": "1",
    "node": "hs_s",
    "_s_r_a": "page"
}
zh_sina_index_stock_count_url = "http://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeStockCountSimple?node=hs_s"

def _get_zh_index_page_count():
    res = requests.get(zh_sina_index_stock_count_url)
    page_count = int(re.findall(re.compile(r"\d+"), res.text)[0]) / 80
    if isinstance(page_count, int):
        return page_count
    else:
        return int(page_count) + 1


def _stock_zh_index_spot():
    big_df = pd.DataFrame()
    page_count = _get_zh_index_page_count()
    zh_sina_stock_payload_copy = zh_sina_index_stock_payload.copy()
    for page in range(1, page_count + 1):
        # print(page)
        zh_sina_stock_payload_copy.update({"page": page})
        res = requests.get(zh_sina_index_stock_url, params=zh_sina_stock_payload_copy)
        data_json = demjson.decode(res.text)
        big_df = big_df.append(pd.DataFrame(data_json), ignore_index=True)
    return big_df


def get_index_code(local = False) -> list:
    """获取指数股票代码列表"""
    name = os.path.join(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),"config"),"index_stocks.txt")

    if(local):
        li = []
        with open(name,"r") as f:
            for line in f.readlines():
                li.append(line.replace("\n",""))
        return li
    else:
        df = _stock_zh_index_spot()
        li = []

        for index,row in df.iterrows():
            li.append(row["symbol"])

        with open(name,"w") as f:
            for symbol in li:
                f.write(symbol)
                f.write("\n")
        return ["s_"+x for x in li]



def get_index_shot(_symbols:list) -> list:
    """获取指数的行情"""
    return get_quotes(_symbols,_handle_ret_str)


def _handle_ret_str(_quote_str):
    temp_list = _quote_str.split(";")
    #_quote_str = _quote_str.replace("\n","").replace('var hq_str_gb_',"").replace('var hq_str_',"").replace('"',"").replace('=',",").replace(" ","")
    _quote_str =_quote_str.replace("\n","").replace('"',"").replace('=',",").replace(';',",")
    if(_quote_str==""):return None
    stocks_str = _quote_str.split("var hq_str_")[1:]  #分割
    stocks_li = [x.split(",")[:-1] for x in stocks_str]
    for i in range(len(stocks_li)-1, -1, -1):
        if(len(stocks_li[i])<3):del stocks_li[i]
    return stocks_li


