#
# Title: sql_table.py
# Description: database table definitions
# Development Environment: Ubuntu 22.04.5 LTS/python 3.10.12
# Author: G.S. Cole (guycole at gmail dot com)
#
from datetime import datetime

from sqlalchemy import Column
from sqlalchemy import BigInteger, Boolean, Date, DateTime, Float, Integer, String

from sqlalchemy.orm import registry
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.declarative import declared_attr

mapper_registry = registry()

class Base(DeclarativeBase):
    pass

class DailyScore(Base):
    __tablename__ = "heeler_daily_score"

    id = Column(Integer, primary_key=True)
    crate_name = Column(String)
    file_quantity = Column(Integer)
    host_name = Column(String)
    quantity_adsb = Column(Integer)
    quantity_uat = Column(Integer)
    score_date = Column(Date)

    def __init__(self, args: dict[str, any]):
        self.crate_name = args["crate_name"]
        self.file_quantity = args["file_quantity"]
        self.host_name = args["host_name"]
        self.quantity_adsb = args["quantity_adsb"]
        self.quantity_uat = args["quantity_uat"]
        self.score_date = args["score_date"]

    def __repr__(self):
        return f"daily_score({self.score_date} {self.host_name})"

class GeoLoc(Base):
    __tablename__ = "heeler_geo_loc"

    id = Column(Integer, primary_key=True)
    altitude = Column(Float)
    course = Column(Float)
    fix_time = Column(DateTime)
    host_name = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    site_name = Column(String)
    speed = Column(Float)
   
    def __init__(self, args: dict[str, any]):
        self.altitude = args["altitude"]
        self.course = args["course"]
        self.fix_time = args["fix_time"]
        self.host_name = args["host_name"]
        self.latitude = args["latitude"]
        self.longitude = args["longitude"]
        self.site_name = args["site_name"]
        self.speed = args["speed"]

    def __repr__(self):
        return f"geo_loc({self.site_name} {self.host_name})"

class LoadLog(Base):
    """load_log table definition"""

    __tablename__ = "hyena_load_log"

    id = Column(Integer, primary_key=True)
    crate_name = Column(String)
    epoch_seconds = Column(BigInteger)
    file_name = Column(String)
    geo_loc_id = Column(BigInteger)
    host_name = Column(String)
    load_time = Column(DateTime)
    mode = Column(String)
    obs_quantity = Column(Integer)
    obs_time = Column(DateTime)
    site_name = Column(String)
    task = Column(String)

    def __init__(self, args: dict[str, any]):
        self.crate_name = args["crate_name"]
        self.epoch_seconds = args["epoch_seconds"]
        self.file_name = args["file_name"]
        self.geo_loc_id = args["geo_loc_id"]
        self.host_name = args["host_name"]
        self.load_time = args.get("load_time", datetime.now())
        self.mode = args["mode"]
        self.obs_quantity = args["obs_quantity"]
        self.obs_time = args["obs_time"]
        self.site_name = args["site_name"]
        self.task = args["task"]

    def __repr__(self):
        return f"load_log({self.file_name} {self.obs_time} {self.task} {self.host_name})"

# ;;; Local Variables: ***
# ;;; mode:python ***
# ;;; End: ***
