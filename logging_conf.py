# Logger Configuration module
# Import this for easy logger configuration
# See example in the comment of the set_logfile_path function below

# Author: Sven Siegmund
# Version 3

"""
This is to easily set the logfile name for the root logger's
file handler from the module where logging_conf
is imported. Like this:

    import logging_conf
    logging.config.dictConfig(logging.conf.create_dict_config(pathlib.Path(pathlib.Path.cwd()), "all.log", "errors.log"))

If you only need the root logger which outputs to console and your defined file
get the root logger.

    logging.getLogger()

If you want an additional custom logger, get it like this instead:

    logger = logging.getLogger("custom_logger")

The custom logger is configured to propagate its log records to the root logger
So the only additional thing you get from this custom logger by default is
an additional log file where only records or error level ERROR and higher are
written.
"""


import pathlib


def create_dict_config(directory: pathlib.Path, all_log: str, error_log: str) -> dict:
    """
    Creates a logging configuration with path to logfiles set as
    given by the arguments
    """
    file_formatter_conf = {
        "format": "{asctime},{msecs:03.0f} {levelname:>9s} {module} {funcName}: {message}",
        "style": "{",
        "datefmt": "%Y-%m-%d %H:%M:%S",
    }

    console_formatter_conf = {
        "format": "{asctime},{msecs:03.0f} {levelname:>9s} {module} {funcName}: {message}",
        "style": "{",
        "datefmt": "%a %H:%M:%S",
    }

    formatters_dict = {
        "file_formatter": file_formatter_conf,
        "console_formatter": console_formatter_conf,
    }

    root_console_handler_conf = {
        "class": "logging.StreamHandler",
        "level": "INFO",
        # "level": "DEBUG",
        "formatter": "console_formatter",
        "stream": "ext://sys.stdout",
    }

    root_file_handler_conf = {
        "class": "logging.FileHandler",
        "level": "DEBUG",
        "formatter": "file_formatter",
        "filename": directory / all_log,
        "mode": "w",
        "encoding": "utf-8",
    }

    custom_file_handler_conf = {
        "class": "logging.FileHandler",
        "level": "ERROR",
        "formatter": "file_formatter",
        "filename": directory / error_log,
        "mode": "w",
        "encoding": "utf-8",
    }

    handlers_dict = {
        "root_console_handler": root_console_handler_conf,
        "root_file_handler": root_file_handler_conf,
        "custom_file_handler": custom_file_handler_conf,
    }

    custom_logger_conf = {
        "propagate": True,
        "handlers": ["custom_file_handler"],
        "level": "DEBUG",
    }

    root_logger_conf = {
        "handlers": ["root_file_handler", "root_console_handler"],
        "level": "DEBUG",
    }

    loggers_dict = {
        "custom_logger": custom_logger_conf,
    }

    dict_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": formatters_dict,
        "handlers": handlers_dict,
        "loggers": loggers_dict,
        "root": root_logger_conf,
        "incremental": False,
    }
    return dict_config
