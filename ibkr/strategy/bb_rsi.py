#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from ib_insync import util
from ib_insync.objects import BarDataList, BarData
import pandas_ta as ta

from enum import Enum
class Signals(Enum):
    NONE = 0
    LONG = 1
    SHORT = 2
    HOLD = 3



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
            self._signal = Signals.LONG
            
        elif _df.iloc[-1].close >= bb[f"BBU_{self.bb_period}_{self.std}"].iloc[-1] and rsi.iloc[-1] >= 70:
            self._signal = Signals.SHORT

        else:
            self._signal = Signals.NONE

             
         
    def __str__(self):
        return "BB-RSI Strategy"