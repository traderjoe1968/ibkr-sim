import os
from sqlalchemy import Column, Integer, String, Float, DateTime, Enum, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import enum

Base = declarative_base()


class Data5min(Base):
    __tablename__ = 'tbl_5min_data'

    ticker = Column(String, nullable=False, primary_key=True)
    datetime = Column(DateTime, default=datetime.now(datetime.timezone.utc), primary_key=True)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Integer, nullable=False)

    def __repr__(self):
        return (f"<bar(ticker={self.ticker}, datetime={self.datetime}), "
                f"open={self.open}, high={self.high}, low={self.low}, "
                f"close={self.close}, volume={self.volume})>")


class TradeExecution(Base):
    __tablename__ = 'trade_executions'

    id = Column(Integer, primary_key=True)
    datetime = Column(DateTime, default=datetime.now(datetime.timezone.utc))
    ticker = Column(String, nullable=False)  
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    multiplier = Column(Float, nullable=False)
    commission = Column(Float, nullable=False)
    marketvalue = Column(Float, nullable=True)
    

    def __repr__(self):
        return (f"<TradeExecution(ticker={self.ticker}, datetime={self.datetime}), "
                f"quantity={self.quantity}, price={self.price}, commission={self.commission}, "
                f"marketvalue={self.marketvalue}>")
    

# Database setup
# Database setup
DATABASE_URL = 'sqlite:///trades.db'
if not os.path.exists('trades.db'):  # Only creates if file does not exist
    engine = create_engine(DATABASE_URL)  # Using SQLite for simplicity
    Base.metadata.create_all(engine)  # Creates tables only if they don't exist
else:
    engine = create_engine(DATABASE_URL)

Session = sessionmaker(bind=engine)
Session = sessionmaker(bind=engine)

# Example usage
session = Session()