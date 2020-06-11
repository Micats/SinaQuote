#coding:utf8

'''
    akshare的A股历史数据

    A 股数据是从新浪财经获取的数据, 历史数据按日频率更新

    限量: 单次返回具体某个 A 上市公司的所有历史行情数据
'''

import akshare as ak
import pandas as pd
import time
import os
import pickle
import requests
from akshare.stock.cons import (zh_sina_a_stock_hfq_url,
                                zh_sina_a_stock_qfq_url)

if __name__=="__main__":
    import sys
    sys.path.append(".")   #不使用编辑器的时候 运行此文件

from utils import ylog,Util


log=ylog.add_file_1(__file__)



class History:
    """取A股历史数据"""
    def __init__(self):
        
        self.symbols = []  #需要查询股票列表

        #股票列表类型
        self.market_sh_type = ["主板A股","主板B股","创业板"]
        self.market_sz_type = ["A股列表", "B股列表", "AB股列表", "上市公司列表", "主板", "中小企业板", "创业板"]

        self.dir_cur = os.path.dirname(__file__)
        self.dir_p = os.path.dirname(os.path.dirname(__file__))
        self.dir_config = os.path.join(self.dir_p,"config")
        self.dir_data =os.path.join(self.dir_p,"data")

        self.adjust = ["","qfq","hfq","hfq-factor","hfq-factor"]
        self.adjust_type =""  #当前的复权类型

    def update_codes(self):
        """获取股票代码到本地"""   
        #文件中
        _path = Util.path_add_file(self.dir_config,"stocks.txt")

        try:
            time_start = time.time()
            #上证
            sh_df = ak.stock_info_sh_name_code(indicator="主板A股")
            raw_codes = sh_df["SECURITY_CODE_A"].values
            raw_formater = map(lambda x:"sh"+x,raw_codes)
            self.symbols.extend(raw_formater)
            #深证
            sz_df = ak.stock_info_sz_name_code(indicator="A股列表")
            raw_codes = sz_df["公司代码"].values
            raw_formater = map(lambda x:"sz"+x,raw_codes)
            self.symbols.extend(raw_formater)
            #写
            with open(_path,"w",encoding="utf8") as fw:
                for symbol in self.symbols:
                    fw.write(symbol)
                    fw.write("\n")
            time_end = time.time()
            log.info("A股代码列表跟新完毕\n     路径:{}\n     时间(s):{} ".format(_path,time_end-time_start))
        except Exception as e:
            log.error("A股代码列表跟新错误:{}".format(e))

       


    def get_symbols(self):
        """获取需要查询的股票列表"""
        _path = Util.path_add_file(self.dir_config,"stocks.txt")
        #从文件中
        try:
            if(len(self.symbols)==0):
                with open(_path,"r",encoding="utf-8") as f:
                    for line in f.readlines():
                        symbol = line.replace("\n","")
                        self.symbols.append(symbol)
            log.info("获取股票列表完毕，数量:{0}".format(len(self.symbols)))
            return self.symbols
        except Exception as e:
            log.error(e)
            return []
        



    def create_df(self):
        """创建df模板"""
        if(len(self.symbols)==0):
            log.error("股票列表为空，无法创建dataframe")
            return
        try:
            time_start =time.time()
            data = ak.stock_zh_a_daily(symbol = self.symbols[0],adjust="hfq")
            time_end =time.time()
            log.debug("查询一次数据时间(只测了一次，仅做参考):{0}s".format(time_end-time_start))
        except Exception as e:
            log.error("取不到此股票的历史数据,symbol:{0}".format(self.symbols[0]))
            log.error(e)
            return
        log.debug("行索引个数:{0}".format(len(data.index)))
        self.open_df = pd.DataFrame(index = data.index)
        self.high_df = pd.DataFrame(index = data.index)
        self.low_df = pd.DataFrame(index = data.index)
        self.close_df = pd.DataFrame(index = data.index)
        self.turnover_df = pd.DataFrame(index = data.index)
        self.outstanding_df = pd.DataFrame(index = data.index)
        log.debug("创建dataframe成功")

    def parse_data(self,_df,_symbol):
        """解析df"""
        try:
            df_open = pd.DataFrame({_symbol:_df["open"].values},index=_df.index)
            df_high = pd.DataFrame({_symbol:_df["high"].values},index=_df.index)
            df_low = pd.DataFrame({_symbol:_df["low"].values},index=_df.index)
            df_close = pd.DataFrame({_symbol:_df["close"].values},index=_df.index)
            df_turnover = pd.DataFrame({_symbol:_df["turnover"].values},index=_df.index)
            df_outstanding = pd.DataFrame({_symbol:_df["outstanding_share"].values},index=_df.index)

            self.open_df = self.open_df.join(df_open,how="outer")
            self.high_df = self.high_df.join(df_high,how="outer")
            self.low_df = self.low_df.join(df_low,how="outer")
            self.close_df = self.close_df.join(df_close,how="outer")
            self.turnover_df = self.turnover_df.join(df_turnover,how="outer")
            self.outstanding_df = self.outstanding_df.join(df_outstanding,how="outer")
        except Exception as e:
            log.error("解析数据出错,symbol:{0},error:{1}".format(_symbol,e))
    
    def save_csv(self,_path=None):
        _path = self.dir_data if _path==None else _path
        if(not os.path.exists(_path)):os.makedirs(_path)
        suffix = self.adjust_type if self.adjust_type=="" else "_"+self.adjust_type+".csv"
        self.open_df.to_csv(Util.path_add_file(_path,"open"+suffix))
        self.high_df.to_csv(Util.path_add_file(_path,"high"+suffix))
        self.low_df.to_csv(Util.path_add_file(_path,"low"+suffix))
        self.close_df.to_csv(Util.path_add_file(_path,"close"+suffix))
        self.turnover_df.to_csv(Util.path_add_file(_path,"turnover"+suffix))
        self.outstanding_df.to_csv(Util.path_add_file(_path,"outstanding"+suffix))
        log.info("历史行情csv保存完毕，路径:{}".format(_path))

    def save_pickle(self,_path=None):
        _path = self.dir_data if _path==None else _path
        if(not os.path.exists(_path)):os.makedirs(_path)
        suffix = self.adjust_type if self.adjust_type=="" else "_"+self.adjust_type
        with open(Util.path_add_file(_path,"open"+suffix),"wb+") as f:
            pickle.dump(self.open_df,f)
        with open(Util.path_add_file(_path,"high"+suffix),"wb+") as f:
            pickle.dump(self.high_df,f)
        with open(Util.path_add_file(_path,"low"+suffix),"wb+") as f:
            pickle.dump(self.low_df,f)
        with open(Util.path_add_file(_path,"close"+suffix),"wb+") as f:
            pickle.dump(self.close_df,f)
        with open(Util.path_add_file(_path,"turnover"+suffix),"wb+") as f:
            pickle.dump(self.turnover_df,f)
        with open(Util.path_add_file(_path,"outstanding"+suffix),"wb+") as f:
            pickle.dump(self.outstanding_df,f)
        log.info("历史行情pickle保存完毕，路径:{}".format(_path))


    def get_all_type_history_data(self):
        """存储所有类型"""
        #第一种
        # for _type in self.adjust:
        #     self.get_history_data(_type)

        #第二种
        self.get_symbols()
        for symbol in self.symbols:
            self.stock_zh_a_daily_all(symbol)

    def get_history_data(self,adjust=""):
        """获取一种类型的历史数据"""
        self.adjust_type = adjust
        self.get_symbols()
        self.create_df()
        total = len(self.symbols)
        for index,symbol in enumerate(self.symbols):
            try:
                data = ak.stock_zh_a_daily(symbol = symbol,adjust=self.adjust_type) #adjust="hfq"
                count = index+1
                if(count%1==0):log.debug("当前获取进度{:.2%}:共{},第{}".format(count/total,total,count))
                self.parse_data(data,symbol)
                if(count==10):break
            except Exception as e:
                if(e.args[0] =="No value to decode"):
                    log.debug("已经退市:{0}".format(symbol))
                else:
                    log.error("得到历史数据出错:{0}, {1}".format(symbol,e))
        self.save_csv()
        self.save_pickle()


    
    def load_pickle(self,_adjust=""):
        """加载pickle的历史行情文件"""
        suffix = _adjust if _adjust == "" else "_"+_adjust
        with open(Util.path_add_file(self.dir_data,"open"+suffix),"rb") as f:
            self.open_df = pickle.load(f)
        with open(Util.path_add_file(self.dir_data,"high"+suffix),"rb") as f:
            self.high_df = pickle.load(f)
        with open(Util.path_add_file(self.dir_data,"low"+suffix),"rb") as f:
            self.low_df = pickle.load(f)
        with open(Util.path_add_file(self.dir_data,"close"+suffix),"rb") as f:
            self.close_df = pickle.load(f)
        with open(Util.path_add_file(self.dir_data,"turnover"+suffix),"rb") as f:
            self.turnover_df = pickle.load(f)
        with open(Util.path_add_file(self.dir_data,"outstanding"+suffix),"rb") as f:
            self.outstanding_df = pickle.load(f)
        return self.open_df,self.high_df,self.low_df,self.close_df,self.turnover_df,self.outstanding_df
            

    def stock_zh_a_daily_all(self,symbol):
        ret={}

        temp_df = ak.stock_zh_a_daily(symbol = symbol,adjust="")
        ret["defaut"] = temp_df

        # "hfq":
        temp_df_hfq = temp_df.copy()
        res = requests.get(zh_sina_a_stock_hfq_url.format(symbol))
        hfq_factor_df = pd.DataFrame(
            eval(res.text.split("=")[1].split("\n")[0])['data'])
        hfq_factor_df.columns = ["date", "hfq_factor"]
        hfq_factor_df.index = pd.to_datetime(hfq_factor_df.date)
        del hfq_factor_df["date"]

        temp_df_hfq = pd.merge(
            temp_df_hfq, hfq_factor_df, left_index=True, right_index=True, how="left"
        )
        temp_df_hfq.fillna(method="ffill", inplace=True)
        temp_df_hfq = temp_df_hfq.astype(float)
        temp_df_hfq["open"] = temp_df_hfq["open"] * temp_df_hfq["hfq_factor"]
        temp_df_hfq["high"] = temp_df_hfq["high"] * temp_df_hfq["hfq_factor"]
        temp_df_hfq["close"] = temp_df_hfq["close"] * temp_df_hfq["hfq_factor"]
        temp_df_hfq["low"] = temp_df_hfq["low"] * temp_df_hfq["hfq_factor"]
        ret["hfq"]=temp_df_hfq.iloc[:, :-1]

        # "qfq":
        temp_df_qfq = temp_df.copy()
        res = requests.get(zh_sina_a_stock_qfq_url.format(symbol))
        qfq_factor_df = pd.DataFrame(
            eval(res.text.split("=")[1].split("\n")[0])['data'])
        qfq_factor_df.columns = ["date", "qfq_factor"]
        qfq_factor_df.index = pd.to_datetime(qfq_factor_df.date)
        del qfq_factor_df["date"]

        temp_df_qfq = pd.merge(
            temp_df_qfq, qfq_factor_df, left_index=True, right_index=True, how="left"
        )
        temp_df_qfq.fillna(method="ffill", inplace=True)
        temp_df_qfq = temp_df_qfq.astype(float)
        temp_df_qfq["open"] = temp_df_qfq["open"] / temp_df_qfq["qfq_factor"]
        temp_df_qfq["high"] = temp_df_qfq["high"] / temp_df_qfq["qfq_factor"]
        temp_df_qfq["close"] = temp_df_qfq["close"] / temp_df_qfq["qfq_factor"]
        temp_df_qfq["low"] = temp_df_qfq["low"] / temp_df_qfq["qfq_factor"]
        ret["qfq"] = temp_df_qfq.iloc[:, :-1]

        #"hfq-factor"
        res = requests.get(zh_sina_a_stock_hfq_url.format(symbol))
        hfq_factor_df = pd.DataFrame(
            eval(res.text.split("=")[1].split("\n")[0])['data'])
        hfq_factor_df.columns = ["date", "hfq_factor"]
        hfq_factor_df.index = pd.to_datetime(hfq_factor_df.date)
        del hfq_factor_df["date"]
        ret["hfq-factor"] = hfq_factor_df

        #"qfq-factor":
        res = requests.get(zh_sina_a_stock_qfq_url.format(symbol))
        qfq_factor_df = pd.DataFrame(
            eval(res.text.split("=")[1].split("\n")[0])['data'])
        qfq_factor_df.columns = ["date", "qfq_factor"]
        qfq_factor_df.index = pd.to_datetime(qfq_factor_df.date)
        del qfq_factor_df["date"]
        ret["qfq-factor"] = qfq_factor_df

        return ret


if __name__=="__main__":
    #stocks = ak.stock_zh_a_daily(symbol = "sh600582",adjust="hfq")
    #print(stocks)
    obj = History()
    #obj.update_codes()
    #obj.get_history_data()
    #ret = obj.load_pickle()
    #obj.get_all_type_history_data()
    ret = obj.stock_zh_a_daily_all(symbol="sh600000")
    print("结束")