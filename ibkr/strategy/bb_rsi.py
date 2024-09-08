#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from ib_insync import util
from ib_insync.objects import BarDataList, BarData
import pandas_ta as ta

from enum import Enum
class Signals(Enum):
    NONE = 0
    BUY = 1
    SELL = 2
    SHORT = 3
    COVER = 4


class MeanReversion():
    sma_p = 200
    rsi_p = 10
    _signal = Signals.NONE
    
    
    def __init__(self):
        self.lookback =  self.sma_p
        self.inTrade = 0

    @property
    def signal(self):
        return self._signal
    
    def update(self, bars, hasNewBar):
        if len(bars) < self.lookback:
            return
        _df = util.df(bars[-self.lookback:])
        rsi = ta.rsi(_df.close, length=self.rsi_p)
        sma = ta.sma(_df.close, length=self.sma_p)
        
        self._signal = Signals.NONE

        if self.inTrade == 0 and rsi.iloc[-1] < 30 and _df.close.iloc[-1] > _df.close.iloc[-2] and _df.close.iloc[-1] > sma.iloc[-1]: # above 200 ma
            self._signal = Signals.BUY
        if self.inTrade > 0 and rsi.iloc[-1] > 70 and _df.close.iloc[-1] < _df.close.iloc[-2]:
            self._signal = Signals.SELL

        if self.inTrade == 0 and self.inTrade < 0 and rsi.iloc[-1] > 70 and _df.close.iloc[-1] < _df.close.iloc[-2] and _df.close.iloc[-1] < sma.iloc[-1]: # below 200 ma
            self._signal = Signals.SHORT
        if self.inTrade < 0 and rsi.iloc[-1] < 30 and _df.close.iloc[-1] > _df.close.iloc[-2]: 
            self._signal = Signals.COVER
            
    def __str__(self):
        return "Mean Reversion Strategy"



class BBRSI():
    
    def __init__(self, bb_period, std, rsi_period):
        self._signal = Signals.NONE
        self.bb_period = bb_period
        self.std = float(std)
        self.rsi_period = rsi_period
        self.intrade = False
        self.lookback =  2 * max(self.bb_period, self.rsi_period)
        
    @property
    def signal(self):
        return self._signal

    def update(self, bars, hasNewBar):
        _df = util.df(bars[-self.lookback:])
        bb = ta.bbands(_df.close, length=self.bb_period, std=self.std)
        rsi = ta.rsi(_df.close, length=self.rsi_period)
        
        if _df.iloc[-1].close <= bb[f"BBL_{self.bb_period}_{self.std}"].iloc[-1] and rsi.iloc[-1] <= 30:
            if rsi.iloc[-1] > rsi.iloc[-2] and rsi.iloc[-2] > rsi.iloc[-3]: 
                self._signal = Signals.BUY
            
        elif _df.iloc[-1].close >= bb[f"BBU_{self.bb_period}_{self.std}"].iloc[-1] and rsi.iloc[-1] >= 70:
            if rsi.iloc[-1] < rsi.iloc[-2] and rsi.iloc[-2] < rsi.iloc[-3]:
                self._signal = Signals.SHORT

        else:
            self._signal = Signals.NONE

             
         
    def __str__(self):
        return "BB-RSI Strategy"