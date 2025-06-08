# Standard library imports

# Remote library imports
import os
from flask import Flask
from flask_cors import CORS
from flask_migrate import Migrate
from flask_restful import Api
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData
from flask_marshmallow import Marshmallow
from flask_bcrypt import Bcrypt
from authlib.integrations.flask_client import OAuth
from authlib.integrations.flask_oauth2 import AuthorizationServer

# Instantiate app, set attributes
app = Flask(__name__)

app.secret_key = os.environ.get("SECRET_KEY") or "dev-secret-key"
app.json.compact = False

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


app.config['GITHUB_CLIENT_ID'] = os.environ.get("GITHUB_CLIENT_ID")
app.config['GITHUB_CLIENT_SECRET'] = os.environ.get("GITHUB_CLIENT_SECRET")


# Define metadata, instantiate db
metadata = MetaData(naming_convention={
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
})
db = SQLAlchemy(metadata=metadata)
db.init_app(app)

migrate = Migrate(app, db)
bcrypt = Bcrypt(app)
ma = Marshmallow(app)
api = Api(app)

oauth = OAuth(app)
github = oauth.register(
    name='github',
    client_id=app.config['GITHUB_CLIENT_ID'],
    client_secret=app.config['GITHUB_CLIENT_SECRET'],
    server_metadata_url='https://api.github.com/.well-known/openid_connect_configuration',
    client_kwargs={
        'scope': 'user:email'
    }
)

# Instantiate CORS
CORS(app)
