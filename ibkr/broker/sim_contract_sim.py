
import os
import tomllib
import pandas as pd
from functools import cache
from dataclasses import dataclass, field
from typing import List, NamedTuple, Optional

from ib_async import Future, Contract, ContractDetails

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),'data')

with open(os.path.join(DATA_DIR,"contracts.toml"), "rb") as f:
    _contracts = tomllib.load(f)

def get_margin(symbol: str) -> float:
    try:
        contract_dict = _contracts[symbol]
    except KeyError:
        raise ValueError(f"Contract {symbol} not found in contracts.toml")
    return float(contract_dict["initMargin"])

def get_commission(symbol: str) -> float:
    try:
        contract_dict = _contracts[symbol]
    except KeyError:
        raise ValueError(f"Contract {symbol} not found in contracts.toml")
    return float(contract_dict["commission"])

def load_contract(symbol: str) -> Contract:
    try:
        contract_dict = _contracts[symbol]
    except KeyError:
        raise ValueError(f"Contract {symbol} not found in contracts.toml")

    contract = Contract()
    contract.conId = int(contract_dict["conId"])
    contract.symbol = contract_dict["symbol"]
    contract.tradingClass = contract_dict["tradingClass"]
    contract.secType = contract_dict["secType"]
    contract.exchange = contract_dict["exchange"]
    contract.currency = contract_dict["currency"]
    contract.multiplier = contract_dict["multiplier"]
    return contract

def load_contractDetails(symbol: str) -> ContractDetails:
    try:
        contract_dict = _contracts[symbol]
    except KeyError:
        raise ValueError(f"Contract {symbol} not found in contracts.toml")

    contract = load_contract(symbol)
    details = ContractDetails()
    details.contract = contract
    details.minTick = float(contract_dict["minTick"])
    details.longName = contract_dict["longName"]
    details.contractMonth = contract_dict["contractMonth"]
    details.timeZoneId = contract_dict["timeZoneId"]
    details.tradingHours = contract_dict["tradingHours"]
    details.liquidHours = contract_dict["liquidHours"]
    details.underSymbol = contract_dict['symbol']
    details.underSecType = contract_dict['secType']
    details.lastTradeTime = contract_dict["lastTradeTime"]
    details.minSize = int(contract_dict["minSize"])
    details.sizeIncrement = contract_dict["sizeIncrement"]
    return details

def load_csv(symbol: str) -> pd.DataFrame:
    try:
        filename = os.path.join(DATA_DIR,_contracts[symbol]["filename"])
    except KeyError:
        raise ValueError(f"Contract {symbol} not found in contracts.toml")
    
    cols = ["dt", "tm", "open", "high", "low", "close", "volume"]
    _df = pd.read_csv(filename, header=0, names=cols, usecols=[0, 1, 2, 3, 4, 5, 6], parse_dates=True)
    _df['date'] = pd.to_datetime(_df["dt"] + " " + _df["tm"], format="mixed")
    del _df["dt"]
    del _df["tm"]
    # df = _df.set_index('date')
    return _df
            
    
def load_openorders():
    # TODO : implement load of open orders from DB 
    return {}

def load_positions() -> Contract:
    # TODO : implement load of open positions from DB 
    return {}

def load_executions():
    # TODO : implement load of execution history from DB
    return {}