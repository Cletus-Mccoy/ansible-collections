import sys
import os

_here = os.path.dirname(__file__)
_collection_root = os.path.abspath(os.path.join(_here, "../../../.."))
_module_utils = os.path.join(_collection_root, "plugins", "module_utils")

for _p in (_collection_root, _module_utils):
    if _p not in sys.path:
        sys.path.insert(0, _p)
