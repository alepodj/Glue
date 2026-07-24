import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from common import WINDOW_SIZE

import glue

# Serve ui/ (default) and optionally specify which file types to check for glue.expose()
glue.init()

# disable_cache now defaults to True so this isn't strictly necessary. Set it to False to enable caching.
glue.start('disable_cache.html', size=WINDOW_SIZE, disable_cache=True)
