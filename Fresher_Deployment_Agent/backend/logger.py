import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# Setup logging directory
LOG_DIR = Path(__file__).resolve().parent.parent.parent / "logs"
os.makedirs(LOG_DIR, exist_ok=True)

def setup_logger(name="fda_logger"):
    logger = logging.getLogger(name)
    
    # If logger already has handlers, assume it's already configured
    if logger.handlers:
        return logger
        
    logger.setLevel(logging.INFO)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File Handler
    log_file = LOG_DIR / f"fda_execution_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger

logger = setup_logger()
