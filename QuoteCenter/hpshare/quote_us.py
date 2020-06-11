#coding:utf -8


import json
import os
import execjs
import pandas as pd
import requests
from  ._base import get_quotes


us_sina_stock_list_url = "http://stock.finance.sina.com.cn/usstock/api/jsonp.php/IO.XSRV2.CallbackList[{}]/US_CategoryService.getList"

us_sina_stock_dict_payload = {
    "page": "2",
    "num": "20",
    "sort": "",
    "asc": "0",
    "market": "",
    "id": ""
}

js_hash_text = """
    function d(s){
		var a, i, j, c, c0, c1, c2, r;
		var _s = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_$';
		var _r64 = function(s, b)
		{
			return ((s | (s << 6)) >>> (b % 6)) & 63;
		};
		a = [];
		c = [];
		for (i = 0; i < s.length; i++)
		{
			c0 = s.charCodeAt(i);
			if (c0 & ~255)
			{
				c0 = (c0 >> 8) ^ c0;
			}
			c.push(c0);
			if (c.length == 3 || i == s.length - 1)
			{
				while(c.length < 3)
				{
					c.push(0);
				}
				a.push((c[0] >> 2) & 63);
				a.push(((c[1] >> 4) | (c[0] << 6)) & 63);
				a.push(((c[1] << 4) | (c[2] >> 2)) & 63);
				a.push(c[2] & 63);
				c = [];
			}
		}
		while (a.length < 16)
		{
			a.push(0);
		}
		r = 0;
		for (i = 0; i < a.length; i++)
		{
			r ^= (_r64(a[i] ^ (r | i), i) ^ _r64(i, r)) & 63;
		}
		for (i = 0; i < a.length; i++)
		{
			a[i] = (_r64((r | i & a[i]), r) ^ a[i]) & 63;
			r += a[i];
		}
		for (i = 16; i < a.length; i++)
		{
			a[i % 16] ^= (a[i] + (i >>> 4)) & 63;
		}
		for (i = 0; i < 16; i++)
		{
			a[i] = _s.substr(a[i], 1);
		}
		a = a.slice(0, 16).join('');
		return a;
	}
"""

def _get_us_page_count() -> int:
    page = "1"
    us_js_decode = f"US_CategoryService.getList?page={page}&num=20&sort=&asc=0&market=&id="
    js_code = execjs.compile(js_hash_text)
    dict_list = js_code.call("d", us_js_decode)  # 执行js解密代码
    us_sina_stock_dict_payload.update({"page": "{}".format(page)})
    res = requests.get(
        us_sina_stock_list_url.format(dict_list), params=us_sina_stock_dict_payload
    )
    data_json = json.loads(res.text[res.text.find("({") + 1: res.text.rfind(");")])
    if not isinstance(int(data_json["count"]) / 20, int):
        page_count = int(int(data_json["count"]) / 20) + 1
    else:
        page_count = int(int(data_json["count"]) / 20)
    return page_count


def _get_us_stock_name() -> pd.DataFrame:
    big_df = pd.DataFrame()
    page_count = _get_us_page_count()
    for page in range(1, page_count + 1):
        # page = "1"
        print("当前第{}页".format(page))
        us_js_decode = "US_CategoryService.getList?page={}&num=20&sort=&asc=0&market=&id=".format(
            page
        )
        js_code = execjs.compile(js_hash_text)
        dict_list = js_code.call("d", us_js_decode)  # 执行js解密代码
        us_sina_stock_dict_payload.update({"page": "{}".format(page)})
        res = requests.get(
            us_sina_stock_list_url.format(dict_list), params=us_sina_stock_dict_payload
        )
        data_json = json.loads(res.text[res.text.find("({") + 1: res.text.rfind(");")])
        big_df = big_df.append(pd.DataFrame(data_json["data"]), ignore_index=True)
    return big_df[["name", "cname", "symbol"]]




def get_us_code(local = False):
    """获取美股股票代码"""
    name = os.path.join(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),"config"),"us_stocks.txt")
    ret = []
    if(local):
        with open(name,"r") as f:
            for line in f.readlines():
                ret.append("gb_"+str.lower(line.replace("\n","")))
    else:
        df = _get_us_stock_name() 
        with open(name,"w") as f:
            for index,row in df.iterrows():
                ret.append("gb_"+str.lower(row["symbol"]))
                f.write(row["symbol"])
                f.write("\n")
    return ret




def get_us_shot(_symbols:list):
    """返回美股实时行情"""
    return get_quotes(_symbols,_handle_ret_str)


def _handle_ret_str(_quote_str):
    temp_list = _quote_str.split(";")
    #_quote_str = _quote_str.replace("\n","").replace('var hq_str_gb_',"").replace('var hq_str_',"").replace('"',"").replace('=',",").replace(" ","")
    _quote_str =_quote_str.replace("\n","").replace('"',"").replace('=',",").replace(';',",")
    if(_quote_str==""):return None
    stocks_str = _quote_str.split("var hq_str_gb_")  #分割
    stocks_li = [x.split(",")[:-1] for x in stocks_str]
    for i in range(len(stocks_li)-1, -1, -1):
        if(len(stocks_li[i])<3):del stocks_li[i]
    return stocks_li



def filter_us_code(_li):
    """美股接口中许多过票都不能用，过滤股票"""
    shot = get_us_shot(_li)
    name = os.path.join(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),"config"),"us_stocks.txt")
    ret = []
    with open(name,"w") as f:
        for quote in shot:
            ret.append("gb_"+quote[0])
            f.write(str.upper(quote[0]))
            f.write("\n")
    return ret