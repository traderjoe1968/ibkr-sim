
import asyncio
from concurrent.futures import ThreadPoolExecutor
import copy
import pandas as pd
import datetime
import logging
import time
from typing import Awaitable, Dict, Iterator, List, Optional, Union, override

from eventkit import Event

import ib_insync.util as util
from ib_insync import IB
from ib_insync.client import Client
from ib_insync.contract import Contract, ContractDescription, ContractDetails
from ib_insync.objects import (
    AccountValue, BarDataList, BarData, DepthMktDataDescription, Execution,
    ExecutionFilter, Fill, HistogramData, HistoricalNews, HistoricalSchedule,
    NewsArticle, NewsBulletin, NewsProvider, NewsTick, OptionChain,
    OptionComputation, PnL, PnLSingle, PortfolioItem, Position, PriceIncrement,
    RealTimeBarList, ScanDataList, ScannerSubscription, SmartComponent,
    TagValue, TradeLogEntry, WshEventData)
from ib_insync.order import (
    BracketOrder, LimitOrder, Order, OrderState, OrderStatus, StopOrder, Trade)
from ib_insync.ticker import Ticker
from ib_insync.wrapper import Wrapper

from ibkr.broker.sim_client import SimClient
from ibkr.broker.sim_contract_sim import load_csv




class IBSim(IB):
    def __init__(self):
        super(IBSim, self).__init__()
        self.client = SimClient(self.wrapper) 
     

    @override
    async def reqHistoricalDataAsync(
            self, contract: Contract,
            endDateTime: Union[datetime.datetime, datetime.date, str, None],
            durationStr: str, barSizeSetting: str,
            whatToShow: str, useRTH: bool,
            formatDate: int = 1, keepUpToDate: bool = False,
            chartOptions: List[TagValue] = [], timeout: float = 60) \
            -> BarDataList:

        reqId = self.client.getReqId()
        bars = BarDataList()
        bars.reqId = reqId
        bars.contract = contract
        bars.endDateTime = endDateTime
        bars.durationStr = durationStr
        bars.barSizeSetting = barSizeSetting
        bars.whatToShow = whatToShow
        bars.useRTH = useRTH
        bars.formatDate = formatDate
        bars.keepUpToDate = keepUpToDate
        bars.chartOptions = chartOptions or []
        
        future = self.wrapper.startReq(reqId, contract, container=bars)
        _df = self.loadHistoricalData(reqId, contract.symbol, durationStr, barSizeSetting)
        if keepUpToDate:
            loop = util.getLoop()
            loop.create_task(self.historicalDataUpdate(reqId, bars, contract, _df))
        task = asyncio.wait_for(future, timeout) if timeout else future
        try:
            await task
        except asyncio.TimeoutError:
            self.client.cancelHistoricalData(reqId)
            self._logger.warning(f'reqHistoricalData: Timeout for {contract}')
            bars.clear()
        return bars
    
    def loadHistoricalData(self,reqId: int, symbol:str, durationStr: str, barSizeSetting: str,):
        # FIXME: Duration and Bar Size
        d, p = durationStr.split(' ')
        t, s = barSizeSetting.split(' ')
        t = int(t)
        n = int(d) * t * 60 * 24

        _df = load_csv(symbol)

        for index, row in _df[:n].iterrows():
            bar = BarData(
                date=str(row.date),
                open=float(row.open),
                high=float(row.high),
                low=float(row.low),
                close=float(row.close),
                volume=float(row.volume),
                average=float(0),
                barCount=int(index))                  
            self.wrapper.historicalData(int(reqId), bar)
        startDateStr = str(_df.iloc[0].date)
        endDateStr = str(_df.iloc[n-1].date)

        self.wrapper.historicalDataEnd(int(reqId), startDateStr, endDateStr)
        return _df[n:]
    
    async def historicalDataUpdate(self, reqId: int, bars: BarDataList, contract: Contract, df: pd.DataFrame):
        self.wrapper._reqId2Contract[reqId] = contract
        self.wrapper.reqId2Subscriber[reqId] = bars
        for index, row in df.iterrows():
            bar = BarData(
                    date=str(row.date),
                    open=float(row.open),
                    high=float(row.high),
                    low=float(row.low),
                    close=float(row.close),
                    volume=float(row.volume),
                    average=float(0),
                    barCount=int(index)
                )
            self.wrapper.historicalDataUpdate(reqId, bar)
            await asyncio.sleep(1)

    @override
    def placeOrder(self, contract: Contract, order: Order) -> Trade:
        """
        Place a new order or modify an existing order.
        Returns a Trade that is kept live updated with
        status changes, fills, etc.

        Args:
            contract: Contract to use for order.
            order: The order to be placed.
        """
        orderId = order.orderId or self.client.getReqId()
        # self.client.placeOrder(orderId, contract, order)
        now = datetime.datetime.now(datetime.timezone.utc)
        key = self.wrapper.orderKey(
            self.wrapper.clientId, orderId, order.permId)
        trade = self.wrapper.trades.get(key)
        if trade:
            # this is a modification of an existing order
            assert trade.orderStatus.status not in OrderStatus.DoneStates
            logEntry = TradeLogEntry(now, trade.orderStatus.status, 'Modify')
            trade.log.append(logEntry)
            self._logger.info(f'placeOrder: Modify order {trade}')
            trade.modifyEvent.emit(trade)
            self.orderModifyEvent.emit(trade)
        else:
            # this is a new order
            order.clientId = self.wrapper.clientId
            order.orderId = orderId
            orderStatus = OrderStatus(
                orderId=orderId, status=OrderStatus.PendingSubmit)
            logEntry = TradeLogEntry(now, orderStatus.status)
            trade = Trade(
                contract, order, orderStatus, [], [logEntry])
            self.wrapper.trades[key] = trade
            self._logger.info(f'placeOrder: New order {trade}')
            self.newOrderEvent.emit(trade)
        return trade

    @override
    def reqPositionsAsync(self) -> Awaitable[List[Position]]:
        return []
    
    @override
    def reqOpenOrdersAsync(self) -> Awaitable[List[Trade]]:
        return []
    
    @override
    def reqCompletedOrdersAsync(self, apiOnly: bool) -> Awaitable[List[Trade]]:
        return []
    
    @override
    def reqAccountUpdatesAsync(self, account: str) -> Awaitable[None]:
        return []

    @override
    def reqAccountUpdatesMultiAsync(self, account: str, modelCode: str = '') -> Awaitable[None]:
        return []
    
    @override
    async def qualifyContractsAsync(self, *contracts: Contract) -> List[Contract]:
        result = []       
        return result
