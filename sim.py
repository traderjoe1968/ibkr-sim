
import asyncio

from ib_insync import util
from ib_insync.order import LimitOrder, Order, OrderStatus, StopOrder

from ibkr.broker.sim_ib import IBSim
from ibkr.broker.sim_contract_sim import load_contract

from ibkr.broker.sim_contract_sim import load_csv

from ibkr.strategy.bb_rsi import BBRSI, Signals

import logging
util.logToConsole(logging.DEBUG)


ib = IBSim()
ib.connect('127.0.0.1', 7497, clientId=1)

contract = load_contract('AUD')
ib.qualifyContracts(contract)

strategy = BBRSI(20, 2, 10)  


def update_stats():
    pass

def check_executions(bars):
    pass

def check_strategy(bars):
    strategy.update(bars, hasNewBar=False)
    inTrade = len(ib.positions()) > 0
    if strategy.signal == Signals.LONG and not inTrade:                 # FIXME: Add check for in trade already
        # TODO: Move to Order Function that checks balance, claculates Stop Loss and buy Price etc ..
        order = LimitOrder('BUY', 50000, bars[-1].close)
        trade = ib.placeOrder(contract, order)
    if strategy.signal == Signals.SHORT and not inTrade:                # FIXME: Add check for in trade already
        order = LimitOrder('SELL', 50000, bars[-1].close)
        trade = ib.placeOrder(contract, order)

def on_bar_update(bars, hasNewBar):
    check_executions(bars)    
    check_strategy(bars)
    update_stats()


def main():
    # session_type = SessionType.LIVE
    bars = ib.reqHistoricalData(contract, 
                                endDateTime='', 
                                durationStr='50 D', 
                                barSizeSetting='1 min', 
                                whatToShow='TRADES', 
                                useRTH=False, 
                                formatDate=1, 
                                keepUpToDate=True, 
                                chartOptions=[]
                            )
    bars.updateEvent += on_bar_update

    ib.run()

    # print("---------------------------------")
    # print('Ending cash: ' + str(self.portfolio.cash))
    # print('Ending market value: ' + str(self.portfolio.market_value))
    # print('Ending asset value: ' + str(self.portfolio.get_asset_val()))
    # results = self.statistics.get_results()
    # print("---------------------------------")
    # print("Strategy:", self.strategy)
    # print("Return: %0.2f%%" % results["return"])
    # print("Sharpe Ratio: %0.2f" % results["sharpe_ratio"])
    # print(
    #     "Max Drawdown: %0.2f%%" % (
    #         results["max_drawdown"] * 100.0
    #     )
    # )
    # return_over_mdd = results["return"] / (results["max_drawdown"] * 100 * -1)
    # print("Return Over Maximum Drawdown: %0.2f" % return_over_mdd)
    # print("Backtest complete.")




if __name__ == "__main__":
    try:
        main()
    finally:
        ib.disconnect()