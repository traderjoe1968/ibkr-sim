
from ib_async import IB
from ib_async.order import BracketOrder, LimitOrder, Order, OrderState, OrderStatus, StopOrder, Trade

from ibkr_sim.sim_client import SimClient


class IBSim(IB):
    def __init__(self, ContractData, AccountBalance=100_000.00):
        super(IBSim, self).__init__()
        self.client = SimClient(self.wrapper, ContractData, AccountBalance) 

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