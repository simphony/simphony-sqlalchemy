"""Migrate sqlite databases with this module."""

import os
import argparse
import logging
from osp.wrappers.sqlalchemy import SqlAlchemySession
from osp.core.session.db.sql_migrate import SqlMigrate

logger = logging.getLogger(__name__)


class SqlAlchemyMigrate(SqlMigrate):
    """Migrate sqlite tables to the latest db schema."""

    def __init__(self, url):
        """Initialize the migration tool with an SqliteSession."""
        super().__init__(SqlAlchemySession(url))


def install_from_terminal():
    """Migrate sqlite databases from terminal."""
    # Parse the user arguments
    parser = argparse.ArgumentParser(
        description="Migrate your sqlite database."
    )
    parser.add_argument("url", type=str,
                        help="The sqlalchemy url to connect to the database.")

    args = parser.parse_args()

    m = SqlAlchemySession(args.url)
    m.run()


if __name__ == "__main__":
    install_from_terminal()
