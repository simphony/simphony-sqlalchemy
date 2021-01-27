"""Migrate sqlite databases with this module."""

import argparse
import logging
from osp.wrappers.sqlalchemy import SqlAlchemySession
from osp.core.session.db.sql_migrate import SqlMigrate

logger = logging.getLogger(__name__)


def install_from_terminal():
    """Migrate sqlite databases from terminal."""
    # Parse the user arguments
    parser = argparse.ArgumentParser(
        description="Migrate your sqlite database."
    )
    parser.add_argument("url", type=str,
                        help="The sqlalchemy url to connect to the database.")

    args = parser.parse_args()

    with SqlAlchemySession(args.url) as session:
        m = SqlMigrate(session)
        m.run()


if __name__ == "__main__":
    install_from_terminal()
