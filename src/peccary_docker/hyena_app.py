#
# Title: hyena_app.py
# Description: driver for peccary hyena application
# Development Environment: Ubuntu 22.04.5 LTS/python 3.10.12
# Author: G.S. Cole (guycole at gmail dot com)
#
import logging
import os
import sys

from helper.postgres import PostGres

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from loader import Loader

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("hyena")


class HyenaApp:

    def __init__(self, stunt_box: str):
        self.stunt_box = stunt_box

        self.db_conn = os.environ.get(
            "DB_CONN",
            "postgresql+psycopg2://hyena_client:batabat@localhost:5432/hyena",
        )

        db_engine = create_engine(self.db_conn, echo=False)
        self.postgres = PostGres(sessionmaker(bind=db_engine, expire_on_commit=False))

    def execute(self) -> None:
        logger.info(f"hyena execute:{self.stunt_box}")

        if self.stunt_box == "loader":
            loader = Loader(self.postgres)
            loader.execute()
        else:
            logger.error(f"invalid stunt_box option:{self.stunt_box}")
            return


if __name__ == "__main__":
    stunt_box = os.environ.get("stuntbox", "loader")

    app = HyenaApp(stunt_box)
    app.execute()

# ;;; Local Variables: ***
# ;;; mode:python ***
# ;;; End: ***
