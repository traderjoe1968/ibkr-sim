import logging
from typing import (Any, Dict, List, Optional, Set, TYPE_CHECKING, Tuple,Union, cast)

from ib_async.contract import (
    Contract, ContractDescription, ContractDetails, DeltaNeutralContract,
    ScanData)
from ib_async.objects import (
    AccountValue, BarData, BarDataList, CommissionReport, DOMLevel,
    DepthMktDataDescription, Dividends, Execution, FamilyCode, Fill,
    FundamentalRatios, HistogramData, HistoricalNews, HistoricalSchedule,
    HistoricalSession, HistoricalTick, HistoricalTickBidAsk,
    HistoricalTickLast, MktDepthData, NewsArticle, NewsBulletin, NewsProvider,
    NewsTick, OptionChain, OptionComputation, PnL, PnLSingle, PortfolioItem,
    Position, PriceIncrement, RealTimeBar, RealTimeBarList, SoftDollarTier,
    TickAttribBidAsk, TickAttribLast, TickByTickAllLast, TickByTickBidAsk,
    TickByTickMidPoint, TickData, TradeLogEntry)
from ib_async.order import Order, OrderState, OrderStatus, Trade
from ib_async.ticker import Ticker
from ib_async.util import (
    UNSET_DOUBLE, UNSET_INTEGER, dataclassAsDict, dataclassUpdate,
    getLoop, globalErrorEvent, isNan, parseIBDatetime)

if TYPE_CHECKING:
    from ib_async.ib import IB


OrderKeyType = Union[int, Tuple[int, int]]



_accounts: List[str] = ['DU1215439',] # FIXME: read accounts from config file
_positions: Dict[str, Dict[int, Position]] = {}

def getAccounts():
    return _accounts