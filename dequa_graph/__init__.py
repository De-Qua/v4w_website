"""DeQua graph library."""
import logging
logging.getLogger(__name__).addHandler(logging.NullHandler())


def set_up_logging(loglevel=logging.DEBUG):
    """
    Set up logging for dequa graph.
    :param loglevel: loglevel for the nky_util loggers
    :return: the logger object
    """
    try:
        from flask import current_app
        if current_app:
            return current_app.logger
    except ModuleNotFoundError:
        pass
    logger = logging.getLogger('dequa_graph')
    logger.handlers.clear()
    logger.setLevel(loglevel)
    ch = logging.StreamHandler()
    formatter = logging.Formatter('[%(asctime)s] [%(name)s:%(filename)s:%(lineno)d] [%(levelname)s] %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    return logger


from . import formatting
from . import geographic
from . import topology
from . import utils
from . import weights
