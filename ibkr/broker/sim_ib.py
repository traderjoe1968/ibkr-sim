
from ib_async import IB
from ib_async.order import BracketOrder, LimitOrder, Order, OrderState, OrderStatus, StopOrder, Trade

from ibkr.broker.sim_client import SimClient


class IBSim(IB):
    def __init__(self):
        super(IBSim, self).__init__()
        self.client = SimClient(self.wrapper) 

        self.newOrderEvent += self.onNewOrderEvent
        self.orderModifyEvent += self.onOrderModifyEvent
     
    
    def onNewOrderEvent(self, trade: Trade):
        self.client.updateOrder(trade)

    def onOrderModifyEvent(self, trade: Trade):
        self.client.modifyOrder(trade)
    