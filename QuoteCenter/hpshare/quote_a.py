# -*- coding:utf-8 -*-
# /usr/bin/env python
"""
Date: 2019/10/30 11:28
Desc: 新浪财经-A股-实时行情数据和历史行情数据(包含前复权和后复权因子)

------20200601
------修改此函数来提高市场行情的获取效率

"""
import re

import demjson
import json
import pandas as pd
import requests
import re
import asyncio
import aiohttp
import time
import os
from concurrent.futures import ThreadPoolExecutor,as_completed,wait
import functools

from .stock_info import stock_info_a_code_name

zh_sina_a_stock_count_url = "http://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeStockCount?node=hs_a"
zh_sina_a_stock_url = "http://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeData"
zh_sina_a_stock_payload = {
    "page": "1",
    "num": "80",
    "sort": "symbol",
    "asc": "1",
    "node": "hs_a",
    "symbol": "",
    "_s_r_a": "init"
}

def _get_zh_a_page_count() -> int:
    res = requests.get(zh_sina_a_stock_count_url)
    page_count = int(re.findall(re.compile(r"\d+"), res.text)[0]) / 80
    if isinstance(page_count, int):
        return page_count
    else:
        return int(page_count) + 1


def get_a_code(local = True):
    """本地 or 在线  获取A股市场股票所有代码"""
    if(local):
        li = []
        path=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),"config")
        full_name = os.path.join(path,"a_stocks.txt")
        with open(full_name,"r") as f:
            for stock in f.readlines():
                li.append(stock.replace("\n",""))
        return li
    else:
        li = stock_info_a_code_name()
        return li

def get_a_shot(_symbols:list) -> list:
    #访问接口
    url = 'http://hq.sinajs.cn/list={}'
    #构造参数
    str_args =""
    args=[]
    for index,code in enumerate(_symbols):
        str_args += str(code)
        str_args += ","
        if((index+1)%250==0):
            str_args = str_args[:-1]
            args.append(str_args)
            str_args = ""
    str_args = str_args[:-1]
    args.append(str_args)

    #事件访问
    tasks = [_asyn_work(url.format(x)) for x in args] 

    loop = asyncio.get_event_loop()
    time_start = time.time()
    futures = loop.run_until_complete(asyncio.wait(tasks))
    all_stocks=[]
    for future in futures[0]:
        str_ret = future.result()
        str_ret = str_ret.replace("\n","").replace('var hq_str_',"").replace('"',"").replace('=',",").replace(" ","")
        if(str_ret==None):continue 
        stocks_str = str_ret.split(";")[:-1]  #去空行
        stocks_li = [x.split(",")[:-1] for x in stocks_str]
        all_stocks.extend(stocks_li)

    time_end = time.time()
    return all_stocks


def stock_zh_a_spot(_method="normal") -> pd.DataFrame:
    big_df = pd.DataFrame()
    page_count = _get_zh_a_page_count()
    zh_sina_stock_payload_copy = zh_sina_a_stock_payload.copy()
    if(_method=="normal"):
        for page in range(1, page_count+1):
            zh_sina_stock_payload_copy.update({"page": page,"num":"80"})
            res = requests.get(
                zh_sina_a_stock_url,
                params=zh_sina_stock_payload_copy)
            try:
                data_json = json.loads(res.text)
            except:
                data_json = demjson.decode(res.text)
            big_df = big_df.append(pd.DataFrame(data_json), ignore_index=True)
        return big_df
    elif(_method=="pool"):
        """线程池"""
        _executor = ThreadPoolExecutor(max_workers=10)
        tasks = []
        for page in range(1, page_count+1):
            zh_sina_stock_payload_copy.update({"page": page})
            task = _executor.submit(_work,zh_sina_a_stock_url,zh_sina_stock_payload_copy.copy())
            func = functools.partial(_done,big_df)
            task.add_done_callback(func)
            tasks.append(task)
        wait(tasks)
        return big_df
    elif(_method=="async"):
        """异步事件"""
        loop = asyncio.get_event_loop()
        futures = loop.run_until_complete(_asyn_run(page_count,zh_sina_stock_payload_copy))
        loop.close()
        for future in futures[0]:
            text = future.result()
            if(text==None):continue
            try:
                data_json = json.loads(text)
            except:
                data_json = demjson.decode(text)
            big_df = big_df.append(pd.DataFrame(data_json), ignore_index=True)
        return big_df
    else:return big_df

async def _asyn_run(_page_count,_zh_sina_stock_payload_copy):
    tasks=[]
    for page in range(1, _page_count+1):
        _zh_sina_stock_payload_copy.update({"page": page})
        task = _asyn_work(zh_sina_a_stock_url,_zh_sina_stock_payload_copy.copy())
        tasks.append(task)
    return await asyncio.wait(tasks)
    


async def _asyn_work(_url,_para=None):
    async with aiohttp.ClientSession() as session:
        async with session.get(_url,params = _para) as res:
            return await res.text()

def _work(_url,_di):
    ret = requests.get(_url,params=_di)
    return  ret

def _done(big_df,future):
    res = future.result()
    if(res == None):return
    data_json = demjson.decode(res.text)
    big_df = big_df.append(pd.DataFrame(data_json), ignore_index=True)


