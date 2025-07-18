from flask_sqlalchemy import SQLAlchemy
from flask_migrate    import Migrate
from flask_login     import LoginManager

# Core Flask extensions
db      = SQLAlchemy()
migrate = Migrate()
login   = LoginManager()
login.login_view = "auth.login"
