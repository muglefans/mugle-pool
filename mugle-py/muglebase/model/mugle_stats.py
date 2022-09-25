import datetime
import uuid
import json

from sqlalchemy import Column, Integer, String, DateTime, func, BigInteger, Boolean, asc, and_
from sqlalchemy.orm import relationship

from muglebase.dbaccess import database
from muglebase.model import Base

# This is the "pool statistics" table
#   Each entry contains stats for the block at height

class Mugle_stats(Base):
    __tablename__ = 'mugle_stats'
    height = Column(BigInteger, index=True, primary_key=True, autoincrement=False)
    timestamp = Column(DateTime, nullable=False, index=True)
    difficulty = Column(BigInteger)
    gps = relationship("Gps")
    
    def __repr__(self):
        return str(self.to_json())

    def __init__(self, timestamp, height, difficulty):
        self.timestamp = timestamp
        self.height = height
        self.difficulty = difficulty

    def to_json(self, fields=None):
        gps_data =  []
        for rec in self.gps:
            gps_data.append(rec.to_json())
        obj = { 'timestamp': self.timestamp.timestamp(),
                 'height': self.height,
                 'difficulty': self.difficulty,
                 'gps': gps_data,
              }
        # Filter by field(s)
        if fields != None:
            for k in list(obj.keys()):
                if k not in fields:
                    del obj[k]
        return obj

    # Get a list of all records in the table
    # XXX Please never call this except in testing
    @classmethod
    def getAll(cls):
        return list(database.db.getSession().query(Mugle_stats))

    # Get the latest (n) record(s) in the db
    @classmethod
    def get_latest(cls, range=None):
        highest = database.db.getSession().query(func.max(Mugle_stats.height)).scalar()
        if range == None:
            return database.db.getSession().query(Mugle_stats).filter(Mugle_stats.height == highest).first()
        else:
            h_start = highest-(range-1)
            return list(database.db.getSession().query(Mugle_stats).filter(Mugle_stats.height >= h_start).order_by(asc(Mugle_stats.height)))


    # Get record(s) by height and optional historical range
    @classmethod
    def get_by_height(cls, height, range=None):
        if range == None:
            return database.db.getSession().query(Mugle_stats).filter(Mugle_stats.height==height).first()
        else:
            h_start = height-(range-1)
            h_end = height
            return list(database.db.getSession().query(Mugle_stats).filter(and_(Mugle_stats.height >= h_start, Mugle_stats.height <= h_end)).order_by(asc(Mugle_stats.height)))


    # Get stats records falling within requested time range
    @classmethod
    def get_by_time(cls, ts, range=None):
        if range == None:
            # XXX Get a range, sort, and give closest?
            return database.db.getSession().query(Mugle_stats).filter(Mugle_stats.timestamp<=ts).first()
        else:
            ts_start = ts-range
            ts_end = ts
            return list(database.db.getSession().query(Mugle_stats).filter(and_(Mugle_stats.timestamp >= ts_start, Mugle_stats.timestamp <= ts_end)).order_by(asc(Mugle_stats.height)))
