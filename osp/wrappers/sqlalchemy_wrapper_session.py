"""For backwards compatibility reason."""

import logging
from osp.wrappers.sqlalchemy import SqlAlchemySession as SqlAlchemyWrapperSession  # noqa: F401,E501

logger = logging.getLogger(__name__)
logger.warning(
    "osp.wrappers.sqlalchemy_wrapper_session.SqlAlchemyWrapperSession is "
    "deprecated. Use osp.wrappers.sqlalchemy.SqlAlchemySession instead."
)
