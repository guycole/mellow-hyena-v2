#
# Title: hyena_app.py
# Description: driver for hyena application
# Development Environment: Ubuntu 22.04.5 LTS/python 3.10.12
# Author: G.S. Cole (guycole at gmail dot com)
#
import logging
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from koala import Koala
from validator import HyenaValidator

from helper.postgres import PostGres

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("hyena")


class HyenaApp:

    def __init__(self, stunt_box: str):
        self.stunt_box = stunt_box

        self.db_conn = os.environ.get(
            "DB_CONN", "postgresql+psycopg2://hyena_client:batabat@localhost:5432/hyena"
        )
        connect_timeout = int(os.environ.get("PG_CONNECT_TIMEOUT", "5"))
        statement_timeout_ms = int(os.environ.get("PG_STATEMENT_TIMEOUT_MS", "5000"))

        db_engine = create_engine(
            self.db_conn,
            echo=False,
            pool_pre_ping=True,
            connect_args={
                "connect_timeout": connect_timeout,
                "options": f"-c statement_timeout={statement_timeout_ms}",
            },
        )
        self.postgres = PostGres(sessionmaker(bind=db_engine, expire_on_commit=False))

    def execute(self) -> int:
        logger.info("hyena execute:%s", self.stunt_box)

        if self.stunt_box == "koala":
            koala = Koala()
            koala.execute()
            return 0

        if self.stunt_box == "validator":
            validator = HyenaValidator(logger, self.postgres)
            return validator.execute()

        logger.error("invalid stunt_box option:%s", self.stunt_box)
        return 1

if __name__ == "__main__":
    # stunt_box options: "koala" and "validator"
    stunt_box = os.environ.get("stuntbox", "validator")

    app = HyenaApp(stunt_box)
    raise SystemExit(app.execute())

# ;;; Local Variables: ***
# ;;; mode:python ***
# ;;; End: ***
