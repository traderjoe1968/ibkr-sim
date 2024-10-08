"""Socket client for communicating with Interactive Brokers."""

import asyncio
from datetime import datetime, timezone
import logging
import time
from collections import deque
from typing import Deque, Awaitable, Dict, Iterator, List, Optional, Union, override

from eventkit import Event

from ib_async.client import Client
from ib_async.wrapper import Wrapper
from ib_async import util
from ib_async.contract import (ComboLeg, Contract, ContractDescription, ContractDetails, DeltaNeutralContract)
from ib_async.order import BracketOrder, LimitOrder, Order, OrderState, OrderStatus, StopOrder, Trade
from ib_async.objects import (
    BarData, CommissionReport, DepthMktDataDescription, Execution, FamilyCode,
    HistogramData, HistoricalSession, HistoricalTick, HistoricalTickBidAsk,
    HistoricalTickLast, NewsProvider, PriceIncrement, SmartComponent,
    SoftDollarTier, TagValue, TickAttribBidAsk, TickAttribLast, ConnectionStats, WshEventData)

from ibkr.broker.sim_portfolio_sim import getAccounts
from ibkr.broker.sim_contract_sim import load_csv, load_contractDetails, load_openorders, load_positions, load_executions, get_commission, get_margin


class SimClient(Client):
    
    def __init__(self, wrapper):
        super(SimClient, self).__init__(wrapper)   
        self.decoder = None
        self.conn = None
        # Override Settings
        self._serverVersion = 150
        self._apiReady = True
        self._permIdSeq = 123456000
        self._execIdSeq = int(0x1_000_000_000)
        self._accounts = getAccounts()
        self.TotalCashBalance = 100_000.0
        self.TotalCashValue = 100_000.0
        self.TotalDailyProfit = 0.0

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
            loop = util.getLoop()
            loop.stop()
            

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
    def placeOrder(self, orderId, contract, order):
        pass

    @override
    def cancelOrder(self, orderId, manualCancelOrderTime=''):
        # try:
        #     self.pending.remove(order)
        # except ValueError:
        #     # If the list didn't have the element we didn't cancel anything
        #     return False

        # order.cancel()
        # self.notify(order)
        # self._ococheck(order)
        # if not bracket:
        #     self._bracketize(order, cancel=True)
        # return True
        raise NotImplementedError()

    @override
    def reqOpenOrders(self):
        oo = load_openorders()  # FIXME:
        if oo:
            c = Contract()
            o = Order()
            os = OrderStatus()
            self.wrapper.openOrder(orderId=0, contract=c, order=o, orderState=os)
        self.wrapper.openOrderEnd()

    @override
    def reqAccountUpdates(self, subscribe, acctCode):
        self.wrapper.accountDownloadEnd(_account='DU1215439')

    @override   
    def reqExecutions(self, reqId, execFilter):
        ex = load_executions() # FIXME:
        if ex:
            c = Contract()
            e = Execution()
            self.wrapper.execDetails(reqId, contract=c, execution=e)
        self.wrapper.execDetailsEnd(reqId)

    # def reqIds(self, numIds):
    #     self.send(8, 1, numIds)

    @override
    def reqContractDetails(self, reqId, contract):
        cd = load_contractDetails(contract.symbol)
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

    @override
    def reqHistoricalData(
            self, reqId, contract, endDateTime, durationStr, barSizeSetting,
            whatToShow, useRTH, formatDate, keepUpToDate, chartOptions):
        
        # FIXME: Duration and Bar Size
        d, p = durationStr.split(' ')
        t, s = barSizeSetting.split(' ')
        t = int(t)
        n = int(d) * t * 60 * 24

        _df = load_csv(contract.symbol)

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

        self._df = _df[n:]

        self.wrapper.lastTime = _df.iloc[n].date
        if keepUpToDate:
            loop = util.getLoop()
            loop.create_task(self.historicalDataUpdateAsync(reqId))

        self.wrapper.historicalDataEnd(int(reqId), startDateStr, endDateStr)

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
        pos = load_positions()  # FIXME:
        if pos: 
            c = Contract()
            self.wrapper.position(account='DU1215439', contract=c, posSize=0, avgCost=0)
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
        self.wrapper.accountUpdateMulti(reqId=reqId, account='DU1215439', tag='AccountCode', val='DU1215439', currency='', modelCode='')
        self.wrapper.accountUpdateMulti(reqId=reqId, account='DU1215439', tag='AccountOrGroup', val='DU1215439', currency='BASE', modelCode='')
        self.wrapper.accountUpdateMulti(reqId=reqId, account='DU1215439', tag='AccountReady', val='true', currency='', modelCode='')
        self.wrapper.accountUpdateMulti(reqId=reqId, account='DU1215439', tag='AccountType', val='INDIVIDUAL', currency='', modelCode='')
        self.wrapper.accountUpdateMulti(reqId=reqId, account='DU1215439', tag='Currency', val='BASE', currency='BASE', modelCode='')
        
        self.wrapper.accountUpdateMulti(reqId=reqId, account='DU1215439', tag='InitMarginReq', val='0', currency='AUD', modelCode='')
        self.wrapper.accountUpdateMulti(reqId=reqId, account='DU1215439', tag='MaintMarginReq', val='0', currency='AUD', modelCode='')

        self.wrapper.accountUpdateMulti(reqId=reqId, account='DU1215439', tag='TotalCashBalance', val=f'{self.TotalCashBalance:.2f}', currency='BASE', modelCode='')
        self.wrapper.accountUpdateMulti(reqId=reqId, account='DU1215439', tag='TotalCashValue', val=f'{self.TotalCashValue:.2f}', currency='AUD', modelCode='')
        self.wrapper.accountUpdateMulti(reqId=reqId, account='DU1215439', tag='UnrealizedPnL', val='0', currency='BASE', modelCode='')
        self.wrapper.accountUpdateMulti(reqId=reqId, account='DU1215439', tag='RealizedPnL', val='0', currency='BASE', modelCode='')

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

    
    async def historicalDataUpdateAsync(self, reqId: int):
        for index, row in self._df.iterrows():
            await asyncio.sleep(0)
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
    
    def updateOrder(self, trade):
        trade.orderStatus.status = 'Submitted'
        

    def modifyOrder(self, trade):
        self._logger.debug('orderModifyEvent: Not Implemented')
        raise NotImplementedError()


            
    def do_execution(self, trade, price, side):
        account = self._accounts[0]
        reqId = self.getReqId()
        execId = self.getexecId()
        c: Contract = trade.contract
        o: Order = trade.order
        os: OrderStatus = trade.orderStatus
        pos = self.wrapper.positions[account]
        
        com = get_commission(c.symbol)
        margin = get_margin(c.symbol)
    
        unrealizedPNL = 0.0  # FixMe: Calculate Unrealized PNL
        realizedPNL = 0.0 # FixMe: Calculate Realized PNL
        closedPos = 0 # FixMe: Calculate Closed Positions
        newPos = o.totalQuantity 

        # Get Current Position if exists
        position = pos.get(c.conId)
        curPos = position.position if position else 0
        # Check if we are closing or we are reversing positions.
        if side == 'BOT':
            if curPos > 0:
                newPos += curPos
            if curPos < 0:  # We have closed or reversed positions.
                closedPos = min(newPos, curPos)
                newPos += curPos
        elif side == 'SLD':
            if curPos < 0:
                newPos -= curPos
            if curPos > 0:  # We have closed or reversed positions.
                closedPos = min(newPos, curPos)
                newPos -= curPos
        else:
            raise ValueError('Side must be BOT or SLD')

        # FixMe: 
        averageCost   = price
        MarketValue   = price * newPos * c.multiplier
        unrealizedPNL = newPos * (price - position.avgCost) * c.multiplier if position else 0
        realizedPNL   = closedPos * (price - position.avgCost) * c.multiplier if position else 0

        ex = Execution(
                        execId=execId, 
                        time=self.wrapper.lastTime,  
                        acctNumber=account, 
                        exchange=c.exchange, 
                        side=side, 
                        shares=o.totalQuantity,
                        price=price, 
                        permId=o.permId, 
                        clientId=self.clientId, 
                        orderId=o.orderId, 
                        liquidation=0, 
                        cumQty=o.totalQuantity, 
                        avgPrice=averageCost, 
                        orderRef='', 
                        evRule='', 
                        evMultiplier=c.multiplier, 
                        modelCode='', 
                        lastLiquidity=1,     
                    )
        self.wrapper.execDetails(reqId, c, ex)
        self.wrapper.execDetailsEnd(reqId=reqId)
        # Update the order status
        self.wrapper.orderStatus(
                        orderId=os.orderId, 
                        status=OrderStatus.Filled, 
                        filled=o.totalQuantity, 
                        remaining=0, 
                        avgFillPrice=price, 
                        permId=o.permId, 
                        parentId=0, 
                        lastFillPrice=price, 
                        clientId=self.wrapper.clientId,
                        whyHeld='', 
                        mktCapPrice=0.0
                    )
        # Update the position
        self.wrapper.position(account, c, newPos, price)
        self.wrapper.positionEnd()
        # Generate a commission report
        cr = CommissionReport(execId=ex.execId,
                              commission=com * o.totalQuantity, 
                              currency=c.currency, 
                              realizedPNL=realizedPNL, 
                              yield_=0.0, 
                              yieldRedemptionDate=0
                            )
        self.wrapper.commissionReport(cr)     
        # Update the Account
        self.TotalCashValue = self.TotalCashValue + realizedPNL + unrealizedPNL - com*closedPos 
        self.TotalCashBalance = self.TotalCashValue - newPos * margin 
        
        self.wrapper.accountUpdateMulti(reqId=reqId, account='DU1215439', tag='TotalCashValue', val=f'{self.TotalCashValue:.2f}', currency='AUD', modelCode='')
        self.wrapper.accountUpdateMulti(reqId=reqId, account='DU1215439', tag='TotalCashBalance', val=f'{self.TotalCashBalance:.2f}', currency='AUD', modelCode='')
        # Update the portfolio
        self.wrapper.updatePortfolio(c, newPos, price, MarketValue,  averageCost, unrealizedPNL, realizedPNL, account)
        # Update PNL
        self.wrapper.pnlSingle(reqId, newPos, self.TotalDailyProfit, unrealizedPNL, realizedPNL, MarketValue )
        


    def update_executions(self, bar: BarData):
        for key, trade in self.wrapper.trades.items():
            if trade.orderStatus.status == OrderStatus.Submitted:
                match trade.order.action:
                    case "BUY":
                        match trade.order.orderType:
                            case "MKT":
                                self.do_execution(trade, bar.close, 'BOT')
                            case "LMT":
                                if trade.order.lmtPrice <= bar.high:
                                    self.do_execution(trade, trade.order.lmtPrice, 'BOT')
                            case "STP LMT":
                                if trade.order.auxLmtPrice <= bar.high:
                                    self.do_execution(trade, trade.order.auxLmtPrice, 'BOT')
                    case "SELL":
                        match trade.order.orderType:
                            case "MKT":
                                self.do_execution(trade, bar.close, 'SLD')
                            case "LMT":
                                if trade.order.lmtPrice >= bar.low:
                                    self.do_execution(trade, trade.order.lmtPrice, 'SLD')
                            case "STP LMT":
                                if trade.order.auxLmtPrice >= bar.low:
                                    self.do_execution(trade, trade.order.auxLmtPrice, 'SLD')
                    