import os
import aiohttp
import asyncio

def get_quotes(_symbols:list,_func = None) -> list:
    """获取行情,代码列表，处理函数"""
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
    futures = loop.run_until_complete(asyncio.wait(tasks))
    all_stocks=[]
    for future in futures[0]:
        str_ret = future.result()
        if(str_ret==None):continue 
        if(_func == None):
            all_stocks.append(str_ret)
        else:
            li = _func(str_ret)
            if(li == None):continue
            all_stocks.extend(li)

    return all_stocks



async def _asyn_work(_url,_para=None,_headers = None):
    """异步访问网络接口"""
    async with aiohttp.ClientSession() as session:
        async with session.get(_url,params = _para,headers = _headers) as res:
            return await res.text()