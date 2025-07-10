from flask_sqlalchemy import SQLAlchemy
from flask_migrate    import Migrate

# Core Flask extensions
db      = SQLAlchemy()
migrate = Migrate()
