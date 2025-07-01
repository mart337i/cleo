import glob
import json
import logging
import logging.config
import os

import rich
from dotenv import load_dotenv

from cleo import NAME
from cleo import addons as addons_dir
from cleo import project_root


class Configuration:
    def __init__(self, addons):
        """
        Initialize configuration by loading environment variables from all env,json files in addons
        and from the OS environment
        
        Args:
            addons: Directory containing command modules and their environment files
        """
        self.env = {}
        self.loaded_config = {}
        self.addons = addons

        self.load_env_from_directory(directory=addons)
        self.load_config_files_from_directory(directory=addons)

        debug = os.getenv('cleo_DEBUG', 0)
        log_level = os.getenv('LOG_LEVEL', 0)
        log_to_file = os.getenv('LOG_TO_FILE', 0)

        self.debug = bool(int(debug))
        self.log_to_file = bool(int(log_to_file))


        self._logger = self.setup_logging(app_name=NAME,log_level=log_level,log_to_file=self.log_to_file)
   
    def load_env_from_directory(self, directory):
        """
        Load all environment files found in the specified directory
        
        Args:
            directory: Directory to scan for environment files
        """
        if not os.path.exists(directory):
            return
            
        env_files = glob.glob(os.path.join(directory, "**/*.env"),include_hidden=True, recursive=True)
        for env_file in env_files:
            load_dotenv(env_file, override=True)
        for key, value in os.environ.items():
            self.env[key] = value

    def load_config_files_from_directory(self, directory):
        """
        Load all configuration files found in the specified directory
        
        Args:
            directory: Directory to scan for environment files
        """
        if not os.path.exists(directory):
            return
        

        configuration_files = glob.glob(os.path.join(directory, "**/*.json"),include_hidden=True, recursive=True)
        for config_file in configuration_files:
            with open(config_file, 'r') as f:
                data = json.load(f)
                self.loaded_config.update(data)
                f.close()


    def setup_logging(
        self,
        app_name='app',
        log_filename='app.log',
        log_level=logging.INFO,
        log_to_file=False,
    ):

        log_dir = os.path.join(project_root, 'logs')
        log_path = os.path.join(log_dir, log_filename)

        if log_to_file:
            os.makedirs(log_dir, exist_ok=True)

        formatter = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

        handlers = {
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'default',
                'level': log_level,
            },
        }

        if log_to_file:
            handlers['file'] = {
                'class': 'logging.FileHandler',
                'filename': log_path,
                'formatter': 'default',
                'level': log_level,
            }

        logging_config = {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'default': {
                    'format': formatter,
                    'datefmt': '%Y-%m-%d %H:%M:%S',
                }
            },
            'handlers': handlers,
            'root': {
                'level': log_level,
                'handlers': list(handlers.keys())
            },
            'loggers': {
                name: {
                    'handlers': list(handlers.keys()),
                    'level': log_level,
                    'propagate': False
                } for name in ['uvicorn', 'uvicorn.access', 'uvicorn.error', app_name]
            }
        }

        logging.config.dictConfig(logging_config)
        return logging.getLogger(app_name)

        
configuration: Configuration = Configuration(addons_dir)
