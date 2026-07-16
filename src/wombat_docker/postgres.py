#
# Title: postgres.py
# Description: postgresql support
# Development Environment: Ubuntu 22.04.5 LTS/python 3.10.12
# Author: G.S. Cole (guycole at gmail dot com)
#
# import sqlalchemy
# from sqlalchemy import and_
# from sqlalchemy import select

import datetime
import logging
import time

from typing import List, Dict

import sqlalchemy
from sqlalchemy import and_
from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy import desc

from sql_table import (
    DailyScore,
    GeoLoc,
    LoadLog,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("hyena")

class PostGres:
    db_engine = None
    Session = None

    def __init__(self, session: sqlalchemy.orm.session.sessionmaker):
        self.Session = session

    def daily_score_insert_or_update(self, args: dict[str, any]) -> DailyScore:
        candidate = DailyScore(args)

        try:
            with self.Session() as session:
                existing = session.scalars(
                    select(DailyScore).filter(
                        and_(
                            DailyScore.score_date == candidate.score_date,
                            DailyScore.host_name == candidate.host_name,
                        )
                    )
                ).first()

                if existing is None:
                    session.add(candidate)
                else:
                    existing.file_quantity += candidate.file_quantity
                    existing.quantity_adsb += candidate.quantity_adsb
                    existing.quantity_uat += candidate.quantity_uat

                session.commit()
        except Exception as error:
            logger.exception("daily_score_insert_or_update failed: %s", error)

        return candidate

    def geo_loc_select_by_site(self, site_name: str) -> List[GeoLoc]:
        statement = select(GeoLoc).filter_by(site_name=site_name).order_by(GeoLoc.fix_time)

        with self.Session() as session:
            return session.scalars(statement).all()

    def load_log_insert(self, args: dict[str, any]) -> LoadLog:
        candidate = LoadLog(args)

        try:
            with self.Session() as session:
                session.add(candidate)
                session.commit()
        except Exception as error:
            logger.exception("load_log_insert failed: %s", error)

        return candidate

    def load_log_select_all(self) -> list[LoadLog]:
        with self.Session() as session:
            return session.scalars(
                select(LoadLog).order_by(desc(LoadLog.load_time), desc(LoadLog.id))
            ).all()

    def load_log_select_all_by_date(self, target: datetime.date) -> list[LoadLog]:
        with self.Session() as session:
            return session.scalars(
                select(LoadLog)
                .filter(func.date(LoadLog.load_time) == target)
                .order_by(desc(LoadLog.load_time), desc(LoadLog.id))
            ).all()

    def load_log_select_by_file_name(self, file_name: str) -> LoadLog:
        with self.Session() as session:
            return session.scalars(
                select(LoadLog).filter_by(file_name=file_name)
            ).first()

# ;;; Local Variables: ***
# ;;; mode:python ***
# ;;; End: ***
