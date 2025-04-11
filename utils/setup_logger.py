import logging
import os
import sys

def setup_logger(name=None, level=logging.INFO, log_file=None):
    """
    Set up and return a configured logger
    
    Args:
        name: Logger name (defaults to root logger if None)
        level: Logging level (defaults to INFO)
        log_file: Optional file path for log output
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Add console handler if not already configured
    if not logger.handlers:
        # Console handler
        console_handler = logging.StreamHandler(stream=sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # File handler if specified
        if log_file:
            # Ensure directory exists
            log_dir = os.path.dirname(log_file)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir)
                
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
    
    return logger

# Configure root logger by default
root_logger = setup_logger()

# Example usage:
# from utils.setup_logger import setup_logger
# logger = setup_logger(__name__)
