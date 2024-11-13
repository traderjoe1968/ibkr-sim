import numpy as np
import pandas as pd
from pandas import DataFrame
from datetime import datetime
from dataclasses import dataclass, field
from ib_async import IB, util, Position, Trade, Fill, CommissionReport
from ib_async.order import LimitOrder, Order, OrderStatus, StopOrder, MarketOrder

from ibkr_sim.sim_ib import IBSim
from ibkr_sim import stats
from ibkr_sim.sim_contract_sim import load_contract
from ibkr_sim.sim_contract_sim import load_csv
from ibkr_sim.example.stoch_k import stoch_k, Signals


import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(message)s\n")
handler = logging.StreamHandler()
handler.setFormatter(formatter)
logger.addHandler(handler)


# util.logToConsole(logger.ERROR)


class Trader():

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
                                    'bars': pd.Series(dtype=int),
                                    'profit': pd.Series(dtype=float),
                                })
        # Stats Parameters
        self.risk_free_rate = 5.0  # Set the risk-free rate (optional)
        # self.orderList = [ MarketOrder('BUY', 1),  MarketOrder('SELL', 1), # Close Long
        #                    MarketOrder('SELL', 1), MarketOrder('BUY', 1), # Close Short
        #                    MarketOrder('BUY', 1),  MarketOrder('BUY', 1), MarketOrder('SELL', 2), # Add to position then Close
        #                    MarketOrder('SELL', 2),  MarketOrder('BUY', 1), MarketOrder('BUY', 1), # Reduce Position then close
        #                    MarketOrder('BUY', 3), MarketOrder('SELL', 4), MarketOrder('BUY', 1), # Reverse Long Position to Short
        #                    MarketOrder('SELL', 2), MarketOrder('SELL', 1),MarketOrder('BUY', 4), # Short add then reverse
        #                    MarketOrder('SELL', 1), # Close
        #              ]
        # self.count = 0

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
                'bars': 0,
                'profit': -commission,
            }])
            self.trade_results = pd.concat([ self.trade_results, df], ignore_index=True)
            self.in_trade = qty
            self.trade_bars = 0
        
        def close_position(current_position, price, dt, commission, multiplier):
            self.trade_results.loc[current_position.index, 'exit_dt'] = dt
            self.trade_results.loc[current_position.index, 'exit_price'] = price
            self.trade_results.loc[current_position.index, 'profit'] -= commission
            if self.trade_results.loc[current_position.index, 'qty'].item() < 0:
                self.trade_results.loc[current_position.index, 'profit'] += (self.trade_results.loc[current_position.index, 'entry_price']  - price)*multiplier
            else:
                self.trade_results.loc[current_position.index, 'profit'] += (price - self.trade_results.loc[current_position.index, 'entry_price'])*multiplier
            self.trade_results.loc[current_position.index, 'bars'] = self.trade_bars
                        

        def add_position(current_position, qty, price, commission):
            newAvgEntryPrice = (qty * price + self.trade_results.loc[current_position.index, 'qty']*self.trade_results.loc[current_position.index, 'entry_price']) / (qty + self.trade_results.loc[current_position.index, 'qty'])
            self.trade_results.loc[current_position.index, 'entry_price'] = newAvgEntryPrice
            self.trade_results.loc[current_position.index, 'qty'] += qty
            self.trade_results.loc[current_position.index, 'profit'] -= commission


        side = -1 if fill.execution.side == "SLD" else 1
        current_position = self.trade_results[(self.trade_results['ticker'] == fill.contract.symbol) & (self.trade_results['exit_dt'] == "") & (self.trade_results['exit_price'] == 0)]
        new_position_size = fill.execution.cumQty
        if current_position.empty:
            open_position(fill.contract.symbol, side, fill.execution.cumQty, fill.execution.avgPrice, fill.execution.time, report.commission)
        else:
            if new_position_size == -current_position.iloc[-1]['qty']:
                # New position would close existing trade
                close_position(current_position, fill.execution.avgPrice, fill.execution.time, report.commission, self.contract.multiplier)
                self.in_trade = 0
            # Add to existing position
            elif new_position_size  + current_position.iloc[-1]['qty'] > 0 and new_position_size * current_position.iloc[-1]['qty'] > 0: 
                add_position(current_position, fill.execution.cumQty, fill.execution.avgPrice, report.commission)
            # Reducing to existing position
            elif abs(new_position_size) < abs(current_position.iloc[-1]['qty']) and new_position_size * current_position.iloc[-1]['qty'] < 0:
                comm_per_contract = report.commission / abs(fill.execution.cumQty)
                new_position = current_position.iloc[0].to_dict()
                new_position['qty'] = new_position_size + current_position.iloc[-1]['qty']
                self.trade_results.loc[current_position.index, 'qty'] = fill.execution.cumQty + current_position.iloc[-1]['qty']
                close_position(current_position, fill.execution.avgPrice, fill.execution.time, abs(fill.execution.cumQty + current_position.iloc[-1]['qty']) * comm_per_contract, self.contract.multiplier) 
                open_position(fill.contract.symbol, -side, new_position['qty'], new_position['entry_price'], new_position['entry_dt'], abs(new_position['qty'])*comm_per_contract)
            # Reverse existing position
            elif abs(new_position_size) > abs(current_position.iloc[-1]['qty']) and new_position_size * current_position.iloc[-1]['qty'] < 0:
                comm_per_contract = report.commission / abs(fill.execution.cumQty)
                newQty = fill.execution.cumQty + current_position.iloc[-1]['qty']
                close_position(current_position, fill.execution.avgPrice, fill.execution.time, abs(current_position.iloc[-1]['qty']) * comm_per_contract, self.contract.multiplier) 
                open_position(fill.contract.symbol, side, newQty, fill.execution.avgPrice, fill.execution.time, abs(newQty) * comm_per_contract)
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
        # if self.count % 8 and len(self.orderList):
        #     order = self.orderList.pop(0)
        #     self.trade = self.ib.placeOrder(self.contract, order)
        # self.count +=1



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
                                    endDateTime='2021-12-16', 
                                    durationStr='30 D', 
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
        logger.info(f"Starting Capital=$100000.00\t Ending Capital=${self.ib.client.TotalCashBalance:.2f}\t Profit={self.ib.client.TotalCashBalance-100000}")
        logger.info(f"TotalProfit={stats.TotalProfit(self.trade_results):.2f}\t AvgProfitLoss={stats.AvgProfitLoss(self.trade_results):.2f}")
        logger.info(f"WinRatio={stats.WinRatio(self.trade_results):.2f}\t MaxSystemDrawdown={stats.MaxSystemDrawdown(self.trade_results):.2f}")
        logger.info(f"SharpeRatio={stats.SharpeRatio(self.trade_results,5.0):.2f}")
        logger.info(f"SortinoRatio={stats.SortinoRatio(self.trade_results,5.0):.2f}")
        logger.info(f"UlcerIndex={stats.UlcerIndex(self.trade_results):.2f}")
        logger.info(f"ProfitFactor={stats.ProfitFactor(self.trade_results):.2f}")
        logger.info(f"Expectancy={stats.Expectancy(self.trade_results):.2f}")
        # running = True
        # while running:
        #     # This updates IB-insync:
        #     ib.sleep(0.03)

        #     # This updates PyGame:
        #     for event in pygame.event.get():
        #         if event.type == pygame.QUIT:
        #             running = False
        #             pygame.quit()

broker = Trader()

if __name__ == "__main__":
    try:
        broker.run()
        logger.info("==== Done ====")
        
    finally:
        
        util.getLoop().stop()   
