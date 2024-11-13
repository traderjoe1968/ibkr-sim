import os
import tomllib
import pandas as pd
import sqlite3
from functools import cache
from dataclasses import dataclass, field
from typing import List, NamedTuple, Optional, Dict

from ib_async import Future, Contract, ContractDetails


@cache
def load_contract(filename: str, symbol: str) -> ContractDetails:
    """Load basic contract information."""
    try:
        with open(filename, "rb") as f:
            _contracts = tomllib.load(f)
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

    contractDetails = ContractDetails()
    contractDetails.contract = contract
    contractDetails.minTick = float(contract_dict["minTick"])
    contractDetails.longName = contract_dict["longName"]
    contractDetails.contractMonth = contract_dict["contractMonth"]
    contractDetails.timeZoneId = contract_dict["timeZoneId"]
    contractDetails.tradingHours = contract_dict["tradingHours"]
    contractDetails.liquidHours = contract_dict["liquidHours"]
    contractDetails.underSymbol = contract_dict['symbol']
    contractDetails.underSecType = contract_dict['secType']
    contractDetails.lastTradeTime = contract_dict["lastTradeTime"]
    contractDetails.minSize = int(contract_dict["minSize"])
    contractDetails.sizeIncrement = contract_dict["sizeIncrement"]
    return contractDetails


def load_csv(csvfilename: str, symbol: str) -> pd.DataFrame:
    """Load historical data from CSV file."""
    
    cols = ["dt", "tm", "open", "high", "low", "close", "volume"]
    df = pd.read_csv(
        csvfilename, 
        header=0, 
        names=cols, 
        usecols=[0, 1, 2, 3, 4, 5, 6], 
        parse_dates=True
    )
    df['date'] = pd.to_datetime(df["dt"] + " " + df["tm"], format="mixed")
    return df.drop(columns=["dt", "tm"])

def load_db(dbfilename: str, symbol: str, startDateStr: str = '', endDateStr: str = '') -> pd.DataFrame:
    """Load historical data from SQLite database with optional date filtering."""
    try:
        query = _build_db_query(symbol, startDateStr, endDateStr)
        
        with sqlite3.connect(dbfilename) as conn:
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
