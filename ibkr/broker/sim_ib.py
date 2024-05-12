
from ib_insync import IB
from ibkr.broker.sim_client import SimClient


class IBSim(IB):
    def __init__(self):
        super(IBSim, self).__init__()
        self.client = SimClient(self.wrapper) 
     
    
    

    