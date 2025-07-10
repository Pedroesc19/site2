"""
Bootstrap wrapper for Phase 1 refactor.

• Re-export create_app & db so external code can still do
      from hackerservice import create_app, db

• Provide an import alias so existing code that says
      import app
  continues to work until we clean it up in later phases.
"""
from importlib import import_module
import sys

from .app import create_app, db     # re-export

# Transparent alias:  import app  ->  hackerservice.app
sys.modules.setdefault("app", import_module(__name__ + ".app"))

