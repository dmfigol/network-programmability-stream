import sys
import logging.config

logging_dict = {
    "version": 1,
    "disable_existing_loggers": True,
    "formatters": {
        "standard": {
            "format": "[%(asctime)s] %(levelname)-8s {%(name)s:%(lineno)d} %(message)s"
        }
    },
    "handlers": {
        "default": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "lab-system.log",
            "maxBytes": 1024 * 1024 * 5,
            "backupCount": 5,
            "formatter": "standard",
        },
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "stream": sys.stdout,
            "formatter": "standard",
        },
    },
    "loggers": {
        "lab_system": {
            "handlers": ["console", "default"],
            "level": "INFO",
            "propagate": False
        }
    },
    "root": {"handlers": ["console", "default"], "level": "INFO"},
}

logging.config.dictConfig(logging_dict)
# logging.basicConfig(
#     format="[%(asctime)s] %(levelname)-8s {%(filename)s:%(lineno)d} %(message)s",
#     level=logging.INFO,
#     handlers=[
#         logging.FileHandler("lab-system.log"),
#         logging.StreamHandler(),
#     ],
# )
