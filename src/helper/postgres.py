#
# Title: postgres.py
# Description: postgresql support
# Development Environment: Ubuntu 22.04.5 LTS/python 3.10.12
# Author: G.S. Cole (guycole at gmail dot com)
#
import datetime
import logging
from typing import Any

import sqlalchemy
from sqlalchemy import and_, desc, func, select
from sqlalchemy.exc import SQLAlchemyError

from helper.sql_table import (
    AdsbExchange,
    DailyScore,
    GeoLoc,
    LoadLog,
    Observation,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("hyena")


class PostGres:
    db_engine = None
    Session = None

    def __init__(
        self,
        session: sqlalchemy.orm.session.sessionmaker,
        app_logger: logging.Logger | None = None,
    ):
        self.logger = app_logger or logger
        self.Session = session

    def adsb_exchange_insert(self, args: dict[str, Any]) -> AdsbExchange:
        candidate = AdsbExchange(args)

        try:
            with self.Session() as session:
                session.add(candidate)
                session.commit()
        except SQLAlchemyError:
            self.logger.exception("adsb_exchange_insert failed")

        return candidate

    def adsb_exchange_select_or_insert(self, args: dict[str, Any]) -> AdsbExchange:
        statement = select(AdsbExchange).filter_by(
            adsb_hex=args["adsb_hex"],
            category=args["category"],
            emergency=args["emergency"],
            flight=args["flight"],
            model=args["model"],
            registration=args["registration"],
            ladd_flag=args["ladd_flag"],
            military_flag=args["military_flag"],
            pia_flag=args["pia_flag"],
            wierdo_flag=args["wierdo_flag"],
        )

        with self.Session() as session:
            candidate = session.scalars(statement).first()

        if candidate is None:
            return self.adsb_exchange_insert(args)

        return candidate

    def daily_score_insert_or_update(self, args: dict[str, Any]) -> DailyScore:
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
        except SQLAlchemyError:
            self.logger.exception("daily_score_insert_or_update failed")

        return candidate

    def geo_loc_select_by_site(self, site_name: str) -> list[GeoLoc]:
        statement = (
            select(GeoLoc)
            .filter_by(site_name=site_name)
            .order_by(desc(GeoLoc.fix_time), desc(GeoLoc.id))
        )

        with self.Session() as session:
            return session.scalars(statement).all()

    def load_log_insert(self, args: dict[str, Any]) -> LoadLog:
        candidate = LoadLog(args)

        try:
            with self.Session() as session:
                session.add(candidate)
                session.commit()
        except SQLAlchemyError:
            self.logger.exception("load_log_insert failed")

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

    def observation_insert(self, args: dict[str, Any]) -> Observation:
        candidate = Observation(args)

        try:
            with self.Session() as session:
                session.add(candidate)
                session.commit()
        except SQLAlchemyError:
            self.logger.exception("observation_insert failed")

        return candidate

# ;;; Local Variables: ***
# ;;; mode:python ***
# ;;; End: ***
