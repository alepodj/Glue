import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import glue

# Serve ui/ (default) and optionally specify which file types to check for glue.expose()
glue.init()

# disable_cache defaults to True. Pass False to allow the browser to cache UI assets.
glue.start('disable_cache.html', disable_cache=True)
