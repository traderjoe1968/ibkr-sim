
from ib_async import util
from ib_async.order import LimitOrder, Order, OrderStatus, StopOrder

from ibkr.broker.sim_ib import IBSim
from ibkr.broker.sim_contract_sim import load_contract

from ibkr.broker.sim_contract_sim import load_csv

from ibkr.strategy.bb_rsi import MeanReversion, Signals

import logging
util.logToConsole(logging.INFO)
util.logToFile('ibkr.log', logging.ERROR)


ib = IBSim()
ib.connect('127.0.0.1', 7497, clientId=1)

contract = load_contract('ES')
ib.qualifyContracts(contract)

strategy = MeanReversion()  


def update_stats():
    pass


def check_strategy(bars):
    strategy.update(bars, hasNewBar=False)
    
    match strategy.signal :
        case Signals.BUY:
            qty = 1 
            order = LimitOrder('BUY', qty, bars[-1].close)
            trade = ib.placeOrder(contract, order)
            strategy.inTrade = 1
        case Signals.SELL:
            qty = 1
            order = LimitOrder('SELL', qty, bars[-1].close)
            trade = ib.placeOrder(contract, order)
            strategy.inTrade = 0
        case Signals.SHORT:
            qty = 1
            order = LimitOrder('SELL', qty, bars[-1].close)
            trade = ib.placeOrder(contract, order)
            strategy.inTrade = -1
        case Signals.COVER:
            qty = 1
            order = LimitOrder('BUY', qty, bars[-1].close)
            trade = ib.placeOrder(contract, order)
            strategy.inTrade = 0



def on_bar_update(bars, hasNewBar):
    ib.client.update_executions(bars[-1])   
    update_stats()
    check_strategy(bars)    


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

    print("---------------------------------")
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
        logging.info("==== Done ====")
    finally:
        ib.disconnect()