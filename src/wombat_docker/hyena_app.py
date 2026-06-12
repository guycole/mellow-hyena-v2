#
# Title: heeler_app.py
# Description: driver for heeler application
# Development Environment: Ubuntu 22.04.5 LTS/python 3.10.12
# Author: G.S. Cole (guycole at gmail dot com)
#
import logging
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from koala import Koala
from scorer import Scorer
from validator import Validator
from postgres import PostGres

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("heeler")

class HeelerApp:

    def __init__(self, score_limit, stunt_box: str):
        self.score_limit = score_limit
        self.stunt_box = stunt_box

        # wombat docker
        self.db_conn = "postgresql+psycopg2://heeler_client:batabat@172.17.0.1:5432/heeler"

        # mac development
        # self.db_conn = "postgresql+psycopg2://heeler_client:batabat@localhost:5432/heeler"

        db_engine = create_engine(self.db_conn, echo=False)
        self.postgres = PostGres(sessionmaker(bind=db_engine, expire_on_commit=False))

    def execute(self) -> None:
        logger.info(f"heeler execute:{self.stunt_box}")

        if self.stunt_box == "scorer":
            scorer = Scorer(self.postgres)
            scorer.scorer(self.score_limit)
        elif self.stunt_box == "validator":
            validator = Validator(self.postgres)
            validator.execute()
            koala = Koala()
            koala.execute()
        else:
            logger.error(f"invalid stunt_box option:{self.stunt_box}")
            return

if __name__ == "__main__":
    # stunt_box options: "koala", "scorer" and "validator"
    score_limit = os.environ.get("limit", -1)
    stunt_box = os.environ.get("stuntbox", "validator")

    app = HeelerApp(int(score_limit), stunt_box)
    app.execute()

# ;;; Local Variables: ***
# ;;; mode:python ***
# ;;; End: ***
