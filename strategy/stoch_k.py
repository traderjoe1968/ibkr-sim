#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from ib_async import util
from ib_async.objects import BarDataList, BarData
import pandas_ta as ta

import logging

from enum import Enum
class Signals(Enum):
    NONE = 0
    BUY = 1
    SELL = 2
    SHORT = 3
    COVER = 4


class stoch_k():
    """
        sm = Optimize("smooth",1,1,5,1); 
        stoch_k1 = StochK(16,sm); 
        stoch_k2 = StochK(40,sm); 

        nbars = Optimize("NBars",4,1,10,1); 
        LTrail = LLV(Ref(Low,-1),nbars);
        STrail = HHV(Ref(High,-1),nbars);
        //###########  Buy Setup  ###########  
        BuySetup = stoch_k2 <=20 AND stoch_k1 <=20; 
        Buy = Ref(BuySetup,-1) AND stoch_k1 > 20; 
        BuyPrice = Open; 
        
        Sell = Close < LTrail; 
        SellPrice = ValueWhen(Ref(Sell,-1),Open, 1); ; 
        
        
        //########### Short Setup  ###########  
        ShortSetup = stoch_k2 >=80 AND stoch_k1 >=80; 
        Short = Ref(ShortSetup,-1) AND stoch_k1 < 80; 
        ShortPrice = Open; 
        
        Cover = Close > STrail; 
        CoverPrice = ValueWhen(Ref(Cover,-1),Open, 1); 
    """
        
    _signal = Signals.NONE
    
    def __init__(self):
        self.short = 7
        self.medium = 40
        self.smooth_k = 2
        self.trail = 0
        self.trail_lookback = 4
        self.lookback = -100 * self.medium 
        self.count = 0
        self._signal = Signals.NONE


    @property
    def signal(self):
        return self._signal
    


    def update(self, inTrade, bars, hasNewBar):
        df = util.df(bars[self.lookback:])
        s1 = ta.stoch(df.high, df.low, df.close, k=self.short,   smooth_k=self.smooth_k)
        s2 = ta.stoch(df.high, df.low, df.close, k=self.medium, smooth_k=self.smooth_k)
        # Calc Trailing Stop
        new_close_high = df['close'] > df['close'].shift(1).rolling(window=self.trail_lookback).max()
        new_close_low  = df['close'] < df['close'].shift(1).rolling(window=self.trail_lookback).min()
        if inTrade > 0 and new_close_high.iloc[-1]: # long
            self.trail = max(self.trail, df['low'].shift(1).rolling(window=self.trail_lookback).min().iloc[-1])

        elif inTrade < 0 and new_close_low.iloc[-1]: # short
            self.trail = min(self.trail, df['high'].shift(1).rolling(window=self.trail_lookback).min().iloc[-1])


        self._signal = Signals.NONE

        if  inTrade == 0 and \
            float(s2[f'STOCHk_{self.medium}_3_{self.smooth_k}'].iloc[-2]) <= 20 and \
            float(s1[f'STOCHk_{self.short}_3_{self.smooth_k}'].iloc[-2]) <= 20 and \
            float(s1[f'STOCHk_{self.short}_3_{self.smooth_k}'].iloc[-1]) > 20:
                self._signal = Signals.BUY
                self.trail = df['low'].rolling(window=self.trail_lookback).min().iloc[-1]-1
                pass

        elif  inTrade == 0 and \
            float(s2[f'STOCHk_{self.medium}_3_{self.smooth_k}'].iloc[-2]) >= 80 and \
            float(s1[f'STOCHk_{self.short}_3_{self.smooth_k}'].iloc[-2]) >= 80 and \
            float(s1[f'STOCHk_{self.short}_3_{self.smooth_k}'].iloc[-1]) < 80:
                self._signal = Signals.SHORT  
                self.trail = df['high'].rolling(window=self.trail_lookback).max().iloc[-1]+1
                pass
        
        elif inTrade > 0 and  df['low'].iloc[-1] <= self.trail:
            self._signal = Signals.SELL

        elif inTrade < 0 and df['high'].iloc[-1] >= self.trail:
            self._signal = Signals.COVER


        # if self.count % 100 == 0:
        #     logging.info(f"{float(s1[f'STOCHk_{self.short}_3_1'].iloc[-2])},{float(s2[f'STOCHk_{self.medium}_3_1'].iloc[-2])},{float(s3[f'STOCHk_{self.long}_3_1'].iloc[-2])}")
        #     logging.info(float(s1[f'STOCHk_{self.short}_3_1'].iloc[-1]))
        # self.count += 1
            
