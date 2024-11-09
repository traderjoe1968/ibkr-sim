import numpy as np
import pandas as pd
from pandas import DataFrame

def calculate_returns(trade_results: DataFrame, risk_free_rate=3.0):
    """Common calculations used across multiple metrics"""
    trade_results['returns'] = trade_results['profit'] / trade_results['entry_price']
    daily_risk_free_rate = (1 + risk_free_rate)**(1/252) - 1
    trade_results['excess_return'] = trade_results['returns'] - daily_risk_free_rate
    return trade_results

def calculate_drawdown(trade_results: DataFrame):
    """Common drawdown calculations"""
    trade_results['cumprofit'] = trade_results['profit'].cumsum()
    trade_results['running_max'] = trade_results['cumprofit'].cummax()
    trade_results['drawdown'] = trade_results['running_max'] - trade_results['cumprofit']
    return trade_results

def separate_trades(trade_results: DataFrame):
    """Split trades into winning and losing"""
    winning_trades = trade_results[trade_results['profit'] > 0]
    losing_trades = trade_results[trade_results['profit'] < 0]
    return winning_trades, losing_trades

def TotalProfit(trade_results:DataFrame):
    total_profit = trade_results['profit'].cumsum() if not trade_results.empty else 0
    return total_profit

def AvgProfitLoss(trade_results:DataFrame):
    avg_profit_loss = trade_results['profit'].mean()
    return avg_profit_loss
        
def AvgProfitLossPercent(trade_results:DataFrame):
    # Calculate profit percentage for each trade
    trade_results['profit_percent'] = (trade_results['profit'] / trade_results['entry_price']) * 100
    # Calculate the average profit/loss percentage
    avg_profit_loss_percent = trade_results['profit_percent'].mean()
    return avg_profit_loss_percent

def AvgBarsHeld(trade_results:DataFrame):
    avg_bars_held = trade_results['bars'].mean()
    return avg_bars_held

def WinRatio(trade_results:DataFrame):
    # Total number of trades
    total_trades = len(trade_results)
    # Number of winning trades (profit > 0)
    winning_trades = (trade_results['profit'] > 0).sum()
    # Calculate the percentage of winners
    percent_winners = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
    return percent_winners

# Main metric functions can now use these helper functions
def SharpeRatio(trade_results: DataFrame, risk_free_rate):
    trade_results = calculate_returns(trade_results, risk_free_rate)
    mean_excess_return = trade_results['excess_return'].mean()
    std_dev_returns = trade_results['excess_return'].std()
    return mean_excess_return / std_dev_returns if std_dev_returns != 0 else np.nan

def SortinoRatio(trade_results: DataFrame, risk_free_rate):
    trade_results = calculate_returns(trade_results, risk_free_rate)
    downside_returns = trade_results['excess_return'][trade_results['excess_return'] < 0]
    downside_deviation = np.sqrt(np.mean(np.square(downside_returns))) if not downside_returns.empty else np.nan
    mean_excess_return = trade_results['excess_return'].mean()
    return mean_excess_return / downside_deviation if downside_deviation != 0 else np.nan

def MaxSystemDrawdown(trade_results: DataFrame):
    trade_results = calculate_drawdown(trade_results)
    return trade_results['drawdown'].max()

def UlcerIndex(trade_results: DataFrame):
    trade_results = calculate_drawdown(trade_results)
    trade_results['drawdown_squared'] = trade_results['drawdown']**2
    return np.sqrt(trade_results['drawdown_squared'].mean())

def ProfitFactor(trade_results: DataFrame):
    winning_trades, losing_trades = separate_trades(trade_results)
    total_profit = winning_trades['profit'].sum()
    total_loss = losing_trades['profit'].sum()
    return total_profit / abs(total_loss) if total_loss != 0 else np.nan

def RiskRewardRatio(trade_results: DataFrame):
    winning_trades, losing_trades = separate_trades(trade_results)
    average_profit = winning_trades['profit'].mean() if len(winning_trades) > 0 else 0
    average_loss = losing_trades['profit'].mean() if len(losing_trades) > 0 else 0
    return average_profit / abs(average_loss) if average_loss != 0 else np.nan