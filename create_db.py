from app import app, db
from models import User, Channel

with app.app_context():
    db.create_all()
