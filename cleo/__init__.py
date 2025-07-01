import sys
import os
from pkgutil import extend_path
from pathlib import Path

# NOTE: 
# This makes it posible to do `from cleo import x` instead of haveing to do the abselute path.
# This is also called a namespace package.
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
__path__ = extend_path(__path__, __name__)

# Usefull paths
templates_dir: Path = Path(Path(__file__).parent, 'templates')
project_root : Path = Path(Path(__file__).parent.parent)
addons: Path = Path(project_root, 'commands')

# DO the import last, so we aviod circular imports 
from . import utils

__version__ = utils.version.get_version()
VERSION: str = __version__
NAME = __name__

from . import config
from . import cli

