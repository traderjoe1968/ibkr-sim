import os
import tomllib
import pandas as pd
import sqlite3
from functools import cache
from dataclasses import dataclass, field
from typing import List, NamedTuple, Optional, Dict

from ib_async import Future, Contract, ContractDetails

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')

# Load contracts configuration once at module level
with open(os.path.join(DATA_DIR, "contracts.toml"), "rb") as f:
    _contracts = tomllib.load(f)

@cache
def get_margin(symbol: str) -> float:
    """Get initial margin requirement for a contract."""
    try:
        return float(_contracts[symbol]["initMargin"])
    except KeyError:
        raise ValueError(f"Contract {symbol} not found in contracts.toml")

@cache
def get_commission(symbol: str) -> float:
    """Get commission for a contract."""
    try:
        return float(_contracts[symbol]["commission"])
    except KeyError:
        raise ValueError(f"Contract {symbol} not found in contracts.toml")

@cache
def load_contract(symbol: str) -> Contract:
    """Load basic contract information."""
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

@cache
def load_contractDetails(symbol: str) -> ContractDetails:
    """Load detailed contract information."""
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
    """Load historical data from CSV file."""
    try:
        filename = os.path.join(DATA_DIR, _contracts[symbol]["filename"])
    except KeyError:
        raise ValueError(f"Contract {symbol} not found in contracts.toml")
    
    cols = ["dt", "tm", "open", "high", "low", "close", "volume"]
    df = pd.read_csv(
        filename, 
        header=0, 
        names=cols, 
        usecols=[0, 1, 2, 3, 4, 5, 6], 
        parse_dates=True
    )
    df['date'] = pd.to_datetime(df["dt"] + " " + df["tm"], format="mixed")
    return df.drop(columns=["dt", "tm"])

def load_db(symbol: str, startDateStr: str = '', endDateStr: str = '') -> pd.DataFrame:
    """Load historical data from SQLite database with optional date filtering."""
    try:
        dbname = os.path.join(DATA_DIR, _contracts[symbol]["dbname"])
        query = _build_db_query(symbol, startDateStr, endDateStr)
        
        with sqlite3.connect(dbname) as conn:
            return pd.read_sql_query(query, conn)
            
    except KeyError:
        raise ValueError(f"Contract {symbol} not found in contracts.toml")

def _build_db_query(symbol: str, startDateStr: str, endDateStr: str) -> str:
    """Build SQL query with date filters."""
    query = f"SELECT datetime as date, open, high, low, close, volume FROM tbl_5min_data where ticker='{symbol}'"
    
    if startDateStr and endDateStr:
        query += f" and datetime between '{startDateStr}' and '{endDateStr}'"
    elif startDateStr:
        query += f" and datetime >= '{startDateStr}'"
    elif endDateStr:
        query += f" and datetime <= '{endDateStr}'"
    
    return query

def load_openorders() -> Dict:
    """Load open orders from database."""
    # TODO: implement load of open orders from DB 
    return {}

def load_positions() -> Dict:
    """Load current positions from database."""
    # TODO: implement load of open positions from DB 
    return {}

def load_executions() -> Dict:
    """Load execution history from database."""
    # TODO: implement load of execution history from DB
    return {}