#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from ib_async import util
from ib_async.objects import BarDataList, BarData
import pandas_ta as ta

from enum import Enum
class Signals(Enum):
    NONE = 0
    BUY = 1
    SELL = 2
    SHORT = 3
    COVER = 4


class MeanReversion():
    _signal = Signals.NONE
    
    def __init__(self, bb_period=22, std=2, ma_period=10):
        self.bb_period = bb_period
        self.std = float(std)
        self.ma_period = ma_period
        self.inTrade = 0
        self.lookback =  2 * max(self.bb_period, self.ma_period)
        
    @property
    def signal(self):
        return self._signal

    def update(self, bars, hasNewBar):
        _df = util.df(bars[-self.lookback:])
        bb = ta.bbands(_df.close, length=self.bb_period, std=self.std)
        ma = ta.ma(_df.close, length=self.ma_period)
        
        if  _df.iloc[-1].low <= bb[f"BBL_{self.bb_period}_{self.std}"].iloc[-1] and _df.close.iloc[-1] > bb[f"BBL_{self.bb_period}_{self.std}"].iloc[-1]:
            self._signal = Signals.BUY
        if self.inTrade > 0 and _df.close.iloc[-1] > ma.iloc[-1]:
            self._signal = Signals.SELL
            
        if  _df.iloc[-1].high >= bb[f"BBU_{self.bb_period}_{self.std}"].iloc[-1] and _df.close.iloc[-1] < bb[f"BBU_{self.bb_period}_{self.std}"].iloc[-1]:
            self._signal = Signals.SHORT
        if self.inTrade < 0 and _df.close.iloc[-1] < ma.iloc[-1]:
            self._signal = Signals.COVER

        else:
            self._signal = Signals.NONE
            
    def __str__(self):
        return "Mean Reversion Strategy"
