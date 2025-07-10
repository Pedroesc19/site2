#!/usr/bin/env python3
import logging
from flask.cli import FlaskGroup
from hackerservice.app import create_app, db

# Configure logging for the application
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
)

# This sets up the FlaskGroup so `flask db ...` commands work
cli = FlaskGroup(create_app=create_app)

if __name__ == '__main__':
    cli()
