import pandas as pd


import sqlite3
# Connect to SQLite database (or create it if it doesn't exist)
conn = sqlite3.connect('trading_data.sqlite')
cursor = conn.cursor()

# Create table for storing the data
cursor.execute('''
CREATE TABLE IF NOT EXISTS tbl_5min_data (
    ticker TEXT,
    datetime TEXT,
    open REAL,
    high REAL,
    low REAL,
    close REAL,
    volume INTEGER
)
''')

df = pd.read_csv(r'ibkr/broker/data/ES_cc.csv')
# Combine 'date' and 'time' columns into a single 'datetime' column
df['datetime'] = pd.to_datetime(df['date'] + ' ' + df['time'])
# Drop the 'date' and 'time' columns as they are now redundant
df.drop(columns=['date', 'time'], inplace=True)
# Reorder the columns if necessary
df = df[['datetime', 'open', 'high', 'low', 'close', 'volume']]

# Insert the data into the SQLite database
for _, row in df.iterrows():
    cursor.execute('''
        INSERT INTO tbl_5min_data (ticker, datetime, open, high, low, close, volume) 
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', ('ES', row[ 'datetime'].strftime('%Y-%m-%d %H:%M:%S'), row['open'], row['high'], row['low'], row['close'], row['volume']))
# Commit and close the connection
conn.commit()
conn.close()