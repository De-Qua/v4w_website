"""DeQua graph library."""
import logging
import colorlog


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
    logger = colorlog.getLogger('dequa_graph')
    logger.handlers.clear()
    logger.setLevel(loglevel)
    ch = colorlog.StreamHandler()
    formatter = colorlog.ColoredFormatter('[%(asctime)s] [%(name)s:%(filename)s:%(lineno)d] %(log_color)s[%(levelname)s]%(reset)s %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    return logger


from . import formatting
from . import geographic
from . import topology
from . import utils
from . import weights
from . import errors
