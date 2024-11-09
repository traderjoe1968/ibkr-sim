
from ib_async import IB
from ib_async.order import BracketOrder, LimitOrder, Order, OrderState, OrderStatus, StopOrder, Trade

from ibkr.broker.sim_client import SimClient


class IBSim(IB):
    def __init__(self, AccountBalance):
        super(IBSim, self).__init__()
        self.client = SimClient(self.wrapper, AccountBalance=100_000.0) 

        self.newOrderEvent += self.do_updateOrder
        self.orderModifyEvent += self.do_modifyOrder
        self.cancelOrderEvent += self.do_cancelOrder
     
    def do_cancelOrder(self, trade:Trade):
        trade.orderStatus.status = OrderStatus.Cancelled

    def do_updateOrder(self, trade:Trade):
        trade.orderStatus.status = OrderStatus.Submitted      

    def do_modifyOrder(self, trade:Trade):
        self._logger.error('orderModifyEvent: Not Implemented')
        raise NotImplementedError()