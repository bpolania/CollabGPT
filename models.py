from database import db

user_channel = db.Table('user_channel',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('channel_id', db.Integer, db.ForeignKey('channel.id'), primary_key=True)
)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    channels = db.Column(db.String, nullable=True)

class Channel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    conversation_id = db.Column(db.String(64), unique=True, nullable=False)
    users = db.relationship('User', secondary=user_channel, backref=db.backref('joined_channels', lazy='dynamic'))

