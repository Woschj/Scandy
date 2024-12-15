import logging
from logging.handlers import RotatingFileHandler
import os

def setup_logger(name, log_file, level=logging.INFO):
    handler = RotatingFileHandler(
        log_file,
        maxBytes=1024 * 1024,  # 1 MB
        backupCount=5,
        delay=True  # Verzögert das Öffnen der Datei
    )
    handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)
    
    return logger

# Logger initialisieren
loggers = {
    'user_actions': setup_logger('user_actions', 'logs/user_actions.log'),
    'errors': setup_logger('errors', 'logs/errors.log'),
    'database': setup_logger('database', 'logs/database.log')
} 