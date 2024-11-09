import numpy as np
import pandas as pd
from datetime import datetime
from dataclasses import dataclass, field
from ib_async import IB, util, Position, Trade, Fill, CommissionReport
from ib_async.order import LimitOrder, Order, OrderStatus, StopOrder, MarketOrder

from ibkr.broker.sim_ib import IBSim
from ibkr.broker.sim_contract_sim import load_contract

from ibkr.broker.sim_contract_sim import load_csv

from ibkr.strategy.stoch_k import stoch_k, Signals

import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(message)s\n")
handler = logging.StreamHandler()
handler.setFormatter(formatter)
logger.addHandler(handler)


# util.logToConsole(logger.ERROR)


class Brokers():

    def __init__(self, AccountBalance=100_000.0):
        self.ib = IBSim(AccountBalance)
        self.ib._logger.setLevel(logging.ERROR)
        self.ib.wrapper._logger.setLevel(logging.ERROR)
        self.ib.connect('127.0.0.1', 7497, clientId=1)

        self.contract = load_contract('ES')
        self.ib.qualifyContracts(self.contract)
        self.ib.commissionReportEvent += self.on_execution

        self.strategy = stoch_k()  
        self.in_trade = 0
        self.trade_bars = 0
        self.trade_results = pd.DataFrame({
                                    'ticker': pd.Series(dtype=str),
                                    'direction': pd.Series(dtype=str),
                                    'qty': pd.Series(dtype=int),
                                    'entry_dt': pd.Series(dtype=str),
                                    'entry_price': pd.Series(dtype=float),
                                    'exit_dt': pd.Series(dtype=str),
                                    'exit_price': pd.Series(dtype=float),
                                    'profit': pd.Series(dtype=float),
                                    'cumprofit': pd.Series(dtype=float),
                                    'bars': pd.Series(dtype=int)
                                })

    def on_execution(self, trade: Trade, fill: Fill, report: CommissionReport):
        def open_position(ticker, side, qty, price, dt, commission):
            direction = 'Long' if side == 1 else 'Short'
            df = pd.DataFrame([{
                'ticker': ticker,
                'direction': direction,
                'qty': qty,
                'entry_dt': dt,
                'entry_price': price,
                'exit_dt': "",
                'exit_price': 0,
                'profit': -commission,
                'cumprofit':0,
                'bars': 0
            }])
            self.trade_results = pd.concat([ self.trade_results, df], ignore_index=True)
            self.in_trade = qty
            self.trade_bars = 0
        
        def close_position(current_position, price, dt, commission, multiplier):
            self.trade_results.loc[current_position.index, 'exit_dt'] = dt
            self.trade_results.loc[current_position.index, 'exit_price'] = price
            self.trade_results.loc[current_position.index, 'profit'] += current_position['qty'] * (price - current_position['entry_price'])*multiplier - commission * current_position['qty']
            self.trade_results.loc[current_position.index, 'bars'] = self.trade_bars
            self.trade_results['cumprofit'] = self.trade_results['profit'].cumsum()
            self.in_trade = 0

        side = -1 if fill.execution.side == "SLD" else 1
        current_position = self.trade_results[(self.trade_results['ticker'] == fill.contract.symbol) & (self.trade_results['exit_dt'] == "") & (self.trade_results['exit_price'] == 0)]
        new_position_size = side * fill.execution.cumQty
        if current_position.empty:
            open_position(fill.contract.symbol, side, fill.execution.cumQty, fill.execution.avgPrice, fill.execution.time, report.commission)
        else:
            if new_position_size * side == -current_position.iloc[-1]['qty']:
                # New position would close existing trade
                close_position(current_position, fill.execution.avgPrice, fill.execution.time, report.commission, self.contract.multiplier)
            elif abs(new_position_size) > abs(current_position.iloc[-1]['qty']) and side != np.sign(current_position.iloc[-1]['qty']):
                # Reverse existing position
                close_position(current_position.iloc, fill.execution.avgPrice, fill.execution.time, report.commission, fill.contract.multiplier)
                raise NotImplementedError()
            elif abs(new_position_size) > abs(current_position.iloc[-1]['qty']) and side == np.sign(current_position.iloc[-1]['qty']):
                # Add to existing position
                raise NotImplementedError()                              
        pass
    

    def check_strategy(self, bars):
        qty = 1
        openOrders = self.ib.openOrders()
        # for position in self.ib.positions():
        #     self.in_trade = position.position
        self.strategy.update(self.in_trade, bars, hasNewBar=False)
        if self.in_trade == 0:
            if self.strategy.signal == Signals.BUY:
                order = MarketOrder('BUY', qty, goodAfterTime=bars[-1].date)
                self.trade = self.ib.placeOrder(self.contract, order)
            elif self.strategy.signal == Signals.SHORT:
                order = MarketOrder('SELL', qty, goodAfterTime=bars[-1].date)
                self.trade = self.ib.placeOrder(self.contract, order)
        else:
            if self.strategy.signal == Signals.SELL:
                order = MarketOrder('SELL', qty, goodAfterTime=bars[-1].date)
                self.trade = self.ib.placeOrder(self.contract, order)
            elif self.strategy.signal == Signals.COVER:
                order = MarketOrder('BUY', qty, goodAfterTime=bars[-1].date)
                self.trade = self.ib.placeOrder(self.contract, order)



    def update_stats(self, bars):
        if abs(self.in_trade) > 0:
            self.trade_bars += 1
            
        pass

    def on_bar_update(self, bars, hasNewBar):
        self.update_stats(bars)
        self.check_strategy(bars)    

    def run(self):
        # session_type = SessionType.LIVE
        bars = self.ib.reqHistoricalData(self.contract, 
                                    endDateTime='', 
                                    durationStr='30000 S', 
                                    barSizeSetting='5 mins', 
                                    whatToShow='TRADES', 
                                    useRTH=False, 
                                    formatDate=1, 
                                    keepUpToDate=True, 
                                    chartOptions=[]
                                )
        bars.updateEvent += self.on_bar_update

        # util.allowCtrlC()
        self.ib.run()
        pd.set_option('display.max_columns', None)  # Show all columns
        pd.set_option('display.max_rows', None)     # Show all rows
        pd.set_option('display.width', 1000)        # Set width of display to avoid line wrapping
        pd.set_option('display.colheader_justify', 'center')  # Center column headers
        logger.info(self.trade_results)
        logger.info("==== Done ====")
        # running = True
        # while running:
        #     # This updates IB-insync:
        #     ib.sleep(0.03)

        #     # This updates PyGame:
        #     for event in pygame.event.get():
        #         if event.type == pygame.QUIT:
        #             running = False
        #             pygame.quit()

broker = Brokers()

if __name__ == "__main__":
    try:
        broker.run()
        logger.info("==== Done ====")
        
    finally:
        
        util.getLoop().stop()   
