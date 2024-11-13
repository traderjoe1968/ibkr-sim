"""Socket client for communicating with Interactive Brokers."""

import asyncio
from datetime import datetime, timezone, timedelta
import dateutil
import logging
import time
from collections import deque
from typing import Deque, Awaitable, Dict, Iterator, List, Optional, Union, override

import dateutil.parser
from eventkit import Event

from ib_async.client import Client
from ib_async.wrapper import Wrapper
from ib_async import util
from ib_async.contract import (ComboLeg, Contract, ContractDescription, ContractDetails, DeltaNeutralContract)
from ib_async.order import BracketOrder, LimitOrder, Order, OrderState, OrderStatus, StopOrder, Trade
from ib_async.objects import (
    BarDataList, BarData, CommissionReport, DepthMktDataDescription, Execution, FamilyCode,
    HistogramData, HistoricalSession, HistoricalTick, HistoricalTickBidAsk,
    HistoricalTickLast, NewsProvider, PriceIncrement, Position, SmartComponent,
    SoftDollarTier, TagValue, TickAttribBidAsk, TickAttribLast, ConnectionStats, WshEventData)


class SimClient(Client):
    
    def __init__(self, wrapper, ContractData, AccountBalance) :
        super(SimClient, self).__init__(wrapper)  
        self.decoder = None
        self.conn = None
        # Override Settings
        self._serverVersion = 150
        self._apiReady = True
        self._permIdSeq = 1
        self._execIdSeq = 1
        self._accounts = ["SimAccount",]
        self.TotalCashBalance = AccountBalance
        self._contractData = ContractData
        self._position = 0
        # FIXME: Need to cater for differnet Contract Classes 
        # should not be hard-coded
        self.commission = 3.5
        

    @override
    def connectionStats(self) -> ConnectionStats:
        """Get statistics about the connection."""
        if not self.isReady():
            raise ConnectionError('Not connected')
        return ConnectionStats(
            self._startTime,
            time.time() - self._startTime,
            self._numBytesRecv, 1,
            self._numMsgRecv, 1)

    @override
    async def connectAsync(self, host, port, clientId, timeout=2.0):
        try:
            self._logger.info(
                f'Connecting to {host}:{port} with clientId {clientId}...')
            self.host = host
            self.port = int(port)
            self.clientId = int(clientId)
            self.connState = Client.CONNECTING
            timeout = timeout or None
            await asyncio.sleep(0.01)
            self.connState = Client.CONNECTED
            self._logger.info('Connected')
            msg = b'API\0' + self._prefix(b'v%d..%d%s' % (
                self.MinClientVersion, self.MaxClientVersion,
                b' ' + self.connectOptions if self.connectOptions else b''))

        except BaseException as e:
            self.disconnect()
            msg = f'API connection failed: {e!r}'
            self._logger.error(msg)
            self.apiError.emit(msg)
            if isinstance(e, ConnectionRefusedError):
                self._logger.error('Make sure API port on TWS/IBG is open')
            raise

    @override
    def disconnect(self):
        """Disconnect from IB connection."""
        self._logger.info('Disconnecting')
        self.connState = Client.DISCONNECTED
        self.reset()

    @override
    def sendMsg(self, msg: str):
        try:
            raise NotImplementedError()
        except Exception as e: 
            logging.exception("\n\tSimulated Environment\n\tRequested function not implemented\n\tImplement function!!!\nterminating",stack_info=True,stacklevel=2)
        finally:
            util.getLoop().stop()
            

    # def reqMktData(
    #         self, reqId, contract, genericTickList, snapshot,
    #         regulatorySnapshot, mktDataOptions):
    #     fields = [1, 11, reqId, contract]

    #     if contract.secType == 'BAG':
    #         legs = contract.comboLegs or []
    #         fields += [len(legs)]
    #         for leg in legs:
    #             fields += [leg.conId, leg.ratio, leg.action, leg.exchange]

    #     dnc = contract.deltaNeutralContract
    #     if dnc:
    #         fields += [True, dnc.conId, dnc.delta, dnc.price]
    #     else:
    #         fields += [False]

    #     fields += [
    #         genericTickList, snapshot, regulatorySnapshot, mktDataOptions]
    #     self.send(*fields)

    # def cancelMktData(self, reqId):
    #     self.send(2, 2, reqId)

    @override
    def placeOrder(self, orderId, contract:Contract, order: Order):
        pass

    @override
    def cancelOrder(self, orderId, manualCancelOrderTime=""):
        pass

    @override
    def reqOpenOrders(self):
        self.wrapper.openOrderEnd()

    @override
    def reqAccountUpdates(self, subscribe, acctCode):
        self.wrapper.accountDownloadEnd(_account=self._accounts[0])

    @override   
    def reqExecutions(self, reqId, execFilter):
        self.wrapper.execDetailsEnd(reqId)

    # def reqIds(self, numIds):
    #     self.send(8, 1, numIds)

    @override
    def reqContractDetails(self, reqId, contract):
        cd = self._contractData [contract.symbol]['ContractDetails']
        self.wrapper.contractDetails(int(reqId), contractDetails=cd)
        self.wrapper.contractDetailsEnd(reqId)

    # def reqMktDepth(
    #         self, reqId, contract, numRows, isSmartDepth, mktDepthOptions):
    #     self.send(
    #         10, 5, reqId,
    #         contract.conId,
    #         contract.symbol,
    #         contract.secType,
    #         contract.lastTradeDateOrContractMonth,
    #         contract.strike,
    #         contract.right,
    #         contract.multiplier,
    #         contract.exchange,
    #         contract.primaryExchange,
    #         contract.currency,
    #         contract.localSymbol,
    #         contract.tradingClass,
    #         numRows,
    #         isSmartDepth,
    #         mktDepthOptions)

    # def cancelMktDepth(self, reqId, isSmartDepth):
    #     self.send(11, 1, reqId, isSmartDepth)

    # def reqNewsBulletins(self, allMsgs):
    #     self.send(12, 1, allMsgs)

    # def cancelNewsBulletins(self):
    #     self.send(13, 1)

    # def setServerLogLevel(self, logLevel):
    #     self.send(14, 1, logLevel)

    # def reqAutoOpenOrders(self, bAutoBind):
    #     self.send(15, 1, bAutoBind)

    # def reqAllOpenOrders(self):
    #     self.send(16, 1)

    # def reqManagedAccts(self):
    #     self.send(17, 1)

    # def requestFA(self, faData):
    #     self.send(18, 1, faData)

    # def replaceFA(self, reqId, faData, cxml):
    #     self.send(19, 1, faData, cxml, reqId)
    async def historicalDataUpdateAsync(self, reqId: int):
        for index, row in self._df.iterrows():
            await asyncio.sleep(0.00001)
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
            self.wrapper.lastTime = row.date
            self.wrapper.historicalDataUpdate(reqId, bar)
        util.getLoop().stop()

    @override
    def reqHistoricalData(
            self, reqId, contract, endDateTime, durationStr, barSizeSetting,
            whatToShow, useRTH, formatDate, keepUpToDate, chartOptions):
        _df = self._contractData[contract.symbol]['df']
        # FIXME: Should not be hard coded but based on max strategy bars needed
        n=100
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
            self.wrapper.lastTime = bar.date

        
        self._df = _df[n:]
        self.wrapper.ib.barUpdateEvent += self.update_executions
        if keepUpToDate:
            loop = util.getLoop()
            loop.create_task(self.historicalDataUpdateAsync(reqId))

        self.wrapper.historicalDataEnd(int(reqId), None, None)


    # def exerciseOptions(
    #         self, reqId, contract, exerciseAction,
    #         exerciseQuantity, account, override):
    #     self.send(
    #         21, 2, reqId,
    #         contract.conId,
    #         contract.symbol,
    #         contract.secType,
    #         contract.lastTradeDateOrContractMonth,
    #         contract.strike,
    #         contract.right,
    #         contract.multiplier,
    #         contract.exchange,
    #         contract.currency,
    #         contract.localSymbol,
    #         contract.tradingClass,
    #         exerciseAction, exerciseQuantity, account, override)

    # def reqScannerSubscription(
    #         self, reqId, subscription, scannerSubscriptionOptions,
    #         scannerSubscriptionFilterOptions):
    #     sub = subscription
    #     self.send(
    #         22, reqId,
    #         sub.numberOfRows,
    #         sub.instrument,
    #         sub.locationCode,
    #         sub.scanCode,
    #         sub.abovePrice,
    #         sub.belowPrice,
    #         sub.aboveVolume,
    #         sub.marketCapAbove,
    #         sub.marketCapBelow,
    #         sub.moodyRatingAbove,
    #         sub.moodyRatingBelow,
    #         sub.spRatingAbove,
    #         sub.spRatingBelow,
    #         sub.maturityDateAbove,
    #         sub.maturityDateBelow,
    #         sub.couponRateAbove,
    #         sub.couponRateBelow,
    #         sub.excludeConvertible,
    #         sub.averageOptionVolumeAbove,
    #         sub.scannerSettingPairs,
    #         sub.stockTypeFilter,
    #         scannerSubscriptionFilterOptions,
    #         scannerSubscriptionOptions)

    # def cancelScannerSubscription(self, reqId):
    #     self.send(23, 1, reqId)

    # def reqScannerParameters(self):
    #     self.send(24, 1)

    # def cancelHistoricalData(self, reqId):
    #     self.send(25, 1, reqId)

    # def reqCurrentTime(self):
    #     self.send(49, 1)

    # def reqRealTimeBars(
    #         self, reqId, contract, barSize, whatToShow,
    #         useRTH, realTimeBarsOptions):
    #     self.send(
    #         50, 3, reqId, contract, barSize, whatToShow,
    #         useRTH, realTimeBarsOptions)

    # def cancelRealTimeBars(self, reqId):
    #     self.send(51, 1, reqId)

    # def reqFundamentalData(
    #         self, reqId, contract, reportType, fundamentalDataOptions):
    #     options = fundamentalDataOptions or []
    #     self.send(
    #         52, 2, reqId,
    #         contract.conId,
    #         contract.symbol,
    #         contract.secType,
    #         contract.exchange,
    #         contract.primaryExchange,
    #         contract.currency,
    #         contract.localSymbol,
    #         reportType, len(options), options)

    # def cancelFundamentalData(self, reqId):
    #     self.send(53, 1, reqId)

    # def calculateImpliedVolatility(
    #         self, reqId, contract, optionPrice, underPrice, implVolOptions):
    #     self.send(
    #         54, 3, reqId, contract, optionPrice, underPrice,
    #         len(implVolOptions), implVolOptions)

    # def calculateOptionPrice(
    #         self, reqId, contract, volatility, underPrice, optPrcOptions):
    #     self.send(
    #         55, 3, reqId, contract, volatility, underPrice,
    #         len(optPrcOptions), optPrcOptions)

    # def cancelCalculateImpliedVolatility(self, reqId):
    #     self.send(56, 1, reqId)

    # def cancelCalculateOptionPrice(self, reqId):
    #     self.send(57, 1, reqId)

    # def reqGlobalCancel(self):
    #     self.send(58, 1)

    # def reqMarketDataType(self, marketDataType):
    #     self.send(59, 1, marketDataType)

    @override
    def reqPositions(self):
        self.wrapper.positionEnd()

    # def reqAccountSummary(self, reqId, groupName, tags):
    #     self.send(62, 1, reqId, groupName, tags)

    # def cancelAccountSummary(self, reqId):
    #     self.send(63, 1, reqId)

    # def cancelPositions(self):
    #     self.send(64, 1)

    # def verifyRequest(self, apiName, apiVersion):
    #     self.send(65, 1, apiName, apiVersion)

    # def verifyMessage(self, apiData):
    #     self.send(66, 1, apiData)

    # def queryDisplayGroups(self, reqId):
    #     self.send(67, 1, reqId)

    # def subscribeToGroupEvents(self, reqId, groupId):
    #     self.send(68, 1, reqId, groupId)

    # def updateDisplayGroup(self, reqId, contractInfo):
    #     self.send(69, 1, reqId, contractInfo)

    # def unsubscribeFromGroupEvents(self, reqId):
    #     self.send(70, 1, reqId)

    # def startApi(self):
    #     self.send(71, 2, self.clientId, self.optCapab)

    # def verifyAndAuthRequest(self, apiName, apiVersion, opaqueIsvKey):
    #     self.send(72, 1, apiName, apiVersion, opaqueIsvKey)

    # def verifyAndAuthMessage(self, apiData, xyzResponse):
    #     self.send(73, 1, apiData, xyzResponse)

    # def reqPositionsMulti(self, reqId, account, modelCode):
    #     self.send(74, 1, reqId, account, modelCode)

    # def cancelPositionsMulti(self, reqId):
    #     self.send(75, 1, reqId)

    @override
    def reqAccountUpdatesMulti(self, reqId, account, modelCode, ledgerAndNLV):
        self.wrapper.accountUpdateMulti(reqId=reqId, account=self._accounts[0], tag='AccountCode', val=self._accounts[0], currency='', modelCode='')
        self.wrapper.accountUpdateMulti(reqId=reqId, account=self._accounts[0], tag='AccountOrGroup', val=self._accounts[0], currency='BASE', modelCode='')
        self.wrapper.accountUpdateMulti(reqId=reqId, account=self._accounts[0], tag='AccountReady', val='true', currency='', modelCode='')
        self.wrapper.accountUpdateMulti(reqId=reqId, account=self._accounts[0], tag='AccountType', val='INDIVIDUAL', currency='', modelCode='')
        self.wrapper.accountUpdateMulti(reqId=reqId, account=self._accounts[0], tag='Currency', val='BASE', currency='BASE', modelCode='')
        
        self.wrapper.accountUpdateMulti(reqId=reqId, account=self._accounts[0], tag='InitMarginReq', val='0', currency='AUD', modelCode='')
        self.wrapper.accountUpdateMulti(reqId=reqId, account=self._accounts[0], tag='MaintMarginReq', val='0', currency='AUD', modelCode='')

        self.wrapper.accountUpdateMulti(reqId=reqId, account=self._accounts[0], tag='TotalCashBalance', val=f'{self.TotalCashBalance:.2f}', currency='BASE', modelCode='')
        self.wrapper.accountUpdateMulti(reqId=reqId, account=self._accounts[0], tag='UnrealizedPnL', val='0', currency='BASE', modelCode='')
        self.wrapper.accountUpdateMulti(reqId=reqId, account=self._accounts[0], tag='RealizedPnL', val='0', currency='BASE', modelCode='')

        self.wrapper.accountUpdateMultiEnd(reqId) 

    # def cancelAccountUpdatesMulti(self, reqId):
    #     self.send(77, 1, reqId)

    # def reqSecDefOptParams(
    #         self, reqId, underlyingSymbol, futFopExchange,
    #         underlyingSecType, underlyingConId):
    #     self.send(
    #         78, reqId, underlyingSymbol, futFopExchange,
    #         underlyingSecType, underlyingConId)

    # def reqSoftDollarTiers(self, reqId):
    #     self.send(79, reqId)

    # def reqFamilyCodes(self):
    #     self.send(80)

    # def reqMatchingSymbols(self, reqId, pattern):
    #     self.send(81, reqId, pattern)

    # def reqMktDepthExchanges(self):
    #     self.send(82)

    # def reqSmartComponents(self, reqId, bboExchange):
    #     self.send(83, reqId, bboExchange)

    # def reqNewsArticle(
    #         self, reqId, providerCode, articleId, newsArticleOptions):
    #     self.send(84, reqId, providerCode, articleId, newsArticleOptions)

    # def reqNewsProviders(self):
    #     self.send(85)

    # def reqHistoricalNews(
    #         self, reqId, conId, providerCodes, startDateTime, endDateTime,
    #         totalResults, historicalNewsOptions):
    #     self.send(
    #         86, reqId, conId, providerCodes, startDateTime, endDateTime,
    #         totalResults, historicalNewsOptions)

    # def reqHeadTimeStamp(
    #         self, reqId, contract, whatToShow, useRTH, formatDate):
    #     self.send(
    #         87, reqId, contract, contract.includeExpired,
    #         useRTH, whatToShow, formatDate)

    # def reqHistogramData(self, tickerId, contract, useRTH, timePeriod):
    #     self.send(
    #         88, tickerId, contract, contract.includeExpired,
    #         useRTH, timePeriod)

    # def cancelHistogramData(self, tickerId):
    #     self.send(89, tickerId)

    # def cancelHeadTimeStamp(self, reqId):
    #     self.send(90, reqId)

    # def reqMarketRule(self, marketRuleId):
    #     self.send(91, marketRuleId)

    # def reqPnL(self, reqId, account, modelCode):
    #     self.send(92, reqId, account, modelCode)

    # def cancelPnL(self, reqId):
    #     self.send(93, reqId)

    # def reqPnLSingle(self, reqId, account, modelCode, conid):
    #     self.send(94, reqId, account, modelCode, conid)

    # def cancelPnLSingle(self, reqId):
    #     self.send(95, reqId)

    # def reqHistoricalTicks(
    #         self, reqId, contract, startDateTime, endDateTime,
    #         numberOfTicks, whatToShow, useRth, ignoreSize, miscOptions):
    #     self.send(
    #         96, reqId, contract, contract.includeExpired,
    #         startDateTime, endDateTime, numberOfTicks, whatToShow,
    #         useRth, ignoreSize, miscOptions)

    # def reqTickByTickData(
    #         self, reqId, contract, tickType, numberOfTicks, ignoreSize):
    #     self.send(97, reqId, contract, tickType, numberOfTicks, ignoreSize)

    # def cancelTickByTickData(self, reqId):
    #     self.send(98, reqId)

    @override
    def reqCompletedOrders(self, apiOnly):
        if 0: #FIXME: Go through all trades and compile list of completed trades.
            c = Contract()
            o = Order()
            os = OrderStatus()
            self.wrapper.completedOrder(contract=c, order=o, orderState=os)
        self.wrapper.completedOrdersEnd()

    # def reqWshMetaData(self, reqId):
    #     self.send(100, reqId)

    # def cancelWshMetaData(self, reqId):
    #     self.send(101, reqId)

    # def reqWshEventData(self, reqId, data: WshEventData):
    #     fields = [102, reqId, data.conId]
    #     if self.serverVersion() >= 171:
    #         fields += [
    #             data.filter,
    #             data.fillWatchlist,
    #             data.fillPortfolio,
    #             data.fillCompetitors]
    #     if self.serverVersion() >= 173:
    #         fields += [
    #             data.startDate,
    #             data.endDate,
    #             data.totalLimit]
    #     self.send(*fields, makeEmpty=False)

    # def cancelWshEventData(self, reqId):
    #     self.send(103, reqId)

    # def reqUserInfo(self, reqId):
    #     self.send(104, reqId)
            
    def getpermId(self) -> int:
        """Get new Perm ID."""
        if not self.isReady():
            raise ConnectionError('Not connected')
        newId = self._permIdSeq
        self._permIdSeq += 1
        return newId
    
    def getexecId(self) -> int:
        """Get new Perm ID."""
        if not self.isReady():
            raise ConnectionError('Not connected')
        newId = self._execIdSeq
        self._execIdSeq += 1
        return newId

    def do_updateportfolio(self, price: float):
        dailyPnL = 0.0
        realizedPNL = 0.0
        unrealizedPNL = 0.0
        marketValue = 0.0
        # Get Current Position if exists
        positions = self.wrapper.positions[self._accounts[0]]
        for key in positions:
            curPos = positions[key]
            if curPos:
                unrealizedPNL += abs(curPos.position) * (price - curPos.avgCost) * curPos.contract.multiplier
                realizedPNL += 0.0
                marketValue += abs(curPos.position * price * curPos.contract.multiplier)
                self.wrapper.updatePortfolio(curPos.contract, abs(curPos.position), 
                        price , marketValue, curPos.avgCost,
                        unrealizedPNL, realizedPNL, self._accounts[0])
        
        reqId = self.getReqId()
        self.wrapper.accountUpdateMulti(reqId=reqId, account=self._accounts[0], tag='TotalCashBalance', val=f'{self.TotalCashBalance:.2f}', currency='BASE', modelCode='')
        self.wrapper.accountUpdateMulti(reqId=reqId, account=self._accounts[0], tag='UnrealizedPnL', val=f'{unrealizedPNL}', currency='BASE', modelCode='')
        self.wrapper.accountUpdateMulti(reqId=reqId, account=self._accounts[0], tag='RealizedPnL', val=f'{realizedPNL}', currency='BASE', modelCode='')
        self.wrapper.accountUpdateMultiEnd(reqId) 
        

    def do_execution(self, trade, price):        
        realizedPNL = 0.0
        newAvgPrice = 0.0

        side = -1 if trade.order.action == "SELL" else 1

        positions = self.wrapper.positions[self._accounts[0]]
        current_position = positions.get(trade.contract.conId) or Position(self._accounts[0], trade.contract, 0, 0.0)
        new_position_size = side * trade.order.totalQuantity 
        newAvgPrice = price

        if current_position.position == 0:
           pass      
        else:
            # Close existing trade
            if new_position_size == -current_position.position: 
                if trade.order.action == "SELL":
                    realizedPNL = trade.order.totalQuantity * (price - current_position.avgCost) * trade.contract.multiplier 
                else:
                    realizedPNL = trade.order.totalQuantity * (current_position.avgCost - price) * trade.contract.multiplier 
                new_position_size = 0 
            # Add to existing position
            elif new_position_size + current_position.position > 0 and new_position_size * current_position.position > 0: 
                newAvgPrice = (trade.orderStatus.filled * trade.orderStatus.avgFillPrice + current_position.avgCost * current_position.position) / (trade.orderStatus.filled  + current_position.position)
                new_position_size = new_position_size + current_position.position
            # Reducing to existing position
            elif abs(new_position_size) < abs(current_position.position) and new_position_size * current_position.position < 0:
                if trade.order.action == "SELL":
                    realizedPNL = trade.order.totalQuantity * (price - current_position.avgCost) * trade.contract.multiplier 
                else:
                    realizedPNL = trade.order.totalQuantity * (current_position.avgCost - price) * trade.contract.multiplier 
                newAvgPrice = current_position.avgCost
                new_position_size = new_position_size + current_position.position         
            # Reverse existing position
            elif abs(new_position_size) > abs(current_position.position) and new_position_size * current_position.position < 0:
                if trade.order.action == "SELL":
                    realizedPNL = abs(current_position.position) * (price - current_position.avgCost) * trade.contract.multiplier 
                else:
                    realizedPNL = abs(current_position.position) * (current_position.avgCost - price) * trade.contract.multiplier 
                newAvgPrice = price
                new_position_size = new_position_size + current_position.position
                 

        self.wrapper.orderStatus(
                        orderId=trade.order.orderId, 
                        status=OrderStatus.Filled, 
                        filled=side * trade.order.totalQuantity, 
                        remaining=0, 
                        avgFillPrice=price, 
                        permId=trade.order.permId, 
                        parentId=0, 
                        lastFillPrice=price, 
                        clientId=self.wrapper.clientId,
                        whyHeld='', 
                        mktCapPrice=0.0
                    )
        reqId = self.getReqId()
        execId = self.getexecId()
        ex = Execution(
                        execId=execId, 
                        time=self.wrapper.lastTime,
                        acctNumber=self._accounts[0], 
                        exchange=trade.contract.exchange, 
                        side="SLD" if trade.order.action == "SELL" else "BOT", 
                        shares=trade.orderStatus.filled,
                        price=price, 
                        permId=trade.order.permId, 
                        clientId=self.clientId, 
                        orderId=trade.order.orderId, 
                        liquidation=0, 
                        cumQty=trade.orderStatus.filled, 
                        avgPrice=price, 
                        orderRef='', 
                        evRule='', 
                        evMultiplier=trade.contract.multiplier, 
                        modelCode='', 
                        lastLiquidity=1,     
                    )
        self.wrapper.execDetails(reqId, trade.contract, ex)
        self.wrapper.execDetailsEnd(reqId=reqId) 
        comm = CommissionReport(execId=execId,
                              commission= self.commission * abs(trade.orderStatus.filled), 
                              currency=trade.contract.currency, 
                              realizedPNL=realizedPNL, 
                              yield_=0.0, 
                              yieldRedemptionDate=0
                            )
        
        # self.wrapper.completedOrder(contract=trade.contract, order=trade.order, orderState=OrderState(status=OrderStatus.Filled))
        # self.wrapper.completedOrdersEnd()
        self.wrapper.commissionReport(comm)
        fill = self.wrapper.fills.get(comm.execId)
        report = util.dataclassUpdate(fill.commissionReport, comm)
        
        self.wrapper.position(self._accounts[0], trade.contract, new_position_size, newAvgPrice)
        self.wrapper.positionEnd()
        

        self.TotalCashBalance += realizedPNL - comm.commission
        self.wrapper.accountUpdateMulti(reqId=reqId, account=self._accounts[0], tag='TotalCashBalance', val=f'{self.TotalCashBalance:.2f}', currency='BASE', modelCode='')
        self.wrapper.accountUpdateMultiEnd(reqId) 
        self.wrapper.ib.commissionReportEvent.emit(trade, fill, report)

        # self._logger.info(f"executed: {self.wrapper.lastTime} \t{"SLD" if trade.order.action == "SELL" else "BOT"} {trade.order.totalQuantity}@{trade.orderStatus.avgFillPrice:.2f}  Position={newPos}")



    def update_executions(self, bars: BarDataList, hasNewBar:bool):
        trades = [v for v in self.wrapper.trades.values() if v.orderStatus.status == OrderStatus.Submitted and v.orderStatus.status not in OrderStatus.DoneStates]
        for trade in trades:
            match trade.order.action:
                case "BUY":
                    match trade.order.orderType:
                        case "MKT":
                            self.do_execution(trade, bars[-1].open)
                        case "LMT":
                            if trade.order.lmtPrice <= bars[-1].high:
                                self.do_execution(trade, trade.order.lmtPrice)
                        case "STP LMT":
                            if trade.order.auxLmtPrice <= bars[-1].high:
                                self.do_execution(trade, trade.order.auxLmtPrice)
                case "SELL":
                    match trade.order.orderType:
                        case "MKT":
                            self.do_execution(trade, bars[-1].open)
                        case "LMT":
                            if trade.order.lmtPrice >= bars[-1].low:
                                self.do_execution(trade, trade.order.lmtPrice)
                        case "STP LMT":
                            if trade.order.auxLmtPrice >= bars[-1].low:
                                self.do_execution(trade, trade.order.auxLmtPrice)

        self.do_updateportfolio(bars[-1].close)
