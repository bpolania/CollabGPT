from flask import Flask, request, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
import jwt
import datetime
import functools
from flask_cors import CORS
import openai_secret_manager
import openai
import re
openai.api_key = openai_secret_manager.get_secret("openai")["api_key"]

app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///collab_gpt.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy()

from database import db

users = {}
channel_members = {}

import functools

def create_app():
    db.init_app(app)
    return app

app = create_app()

default_language = "english"


from models import User, Channel

def auth_decorator(f):
    @functools.wraps(f)
    def wrapped_function(*args, **kwargs):
        token = request.cookies.get('jwt')
        if not token:
            return jsonify({'message': 'Authentication required'}), 401
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            request.user = User.query.filter_by(username=data['username']).first()
        except Exception as e:
            return jsonify({'message': 'Invalid token', 'error': str(e)}), 401
        return f(*args, **kwargs)
    return wrapped_function



@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    username = data['username']
    password = data['password']

    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        return jsonify({'message': 'User already exists'}), 400

    new_user = User(username=username, password=password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'User created'}), 201


@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data['username']
    password = data['password']

    user = User.query.filter_by(username=username).first()
    if not user or user.password != password:
        return jsonify({'message': 'Invalid username or password'}), 401

    token = jwt.encode({'username': username, 'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)}, app.config['SECRET_KEY'])
    response = make_response(jsonify({'message': 'Logged in'}), 200)
    response.set_cookie('jwt', token)
    return response

@app.route('/create', methods=['POST'])
@auth_decorator
def create():
    data = request.get_json()
    channel_name = data['channel_name']

    existing_channel = Channel.query.filter_by(name=channel_name).first()
    if existing_channel:
        return jsonify({'message': 'Channel already exists'}), 400

    # Send initial prompt to OpenAI API
    user_prompt = f"Please set up the conversation for channel {channel_name}. User messages will be identified with [username]."
    group_language = f"The defaut language is {default_language} so if any message is not in {default_language} please translate automatically"
    response_format = f"Please response a one sentence answer only saying Group {channel_name} created with default language {default_language}"

    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": f"{user_prompt}{group_language}{response_format}"}]
    )
    response = completion.choices[0].message.content.strip()
    messages = response.split('\n')
    final_text = messages[-1].replace("[Admin]","").replace("[admin]","")

    conversation_id = completion.id

    new_channel = Channel(name=channel_name, conversation_id=conversation_id)
    db.session.add(new_channel)
    db.session.commit()

    return jsonify({'message': 'Channel created', 'bot_message': final_text}), 201


@app.route('/join', methods=['POST'])
@auth_decorator
def join():
    channel_name = request.json.get('channel_name')
    channel = Channel.query.filter_by(name=channel_name).first()

    if not channel:
        return jsonify({'message': 'Channel not found'}), 404

    if request.user in channel.users:
        return jsonify({'message': 'User already in the channel'}), 400

    channel.users.append(request.user)
    db.session.commit()

    return jsonify({'message': 'Successfully joined the channel'}), 200


@app.route('/leave', methods=['POST'])
@auth_decorator
def leave():
    data = request.get_json()
    channel_name = data['channel_name']

    channel = Channel.query.filter_by(name=channel_name).first()
    if not channel:
        return jsonify({'message': 'Channel does not exist'}), 400

    user = User.query.filter_by(username=request.user).first()
    channels = set(user.channels.split(',')) if user.channels else set()

    if channel_name not in channels:
        return jsonify({'message': 'Not a member of the channel'}), 400

    channels.remove(channel_name)
    user.channels = ','.join(channels)
    db.session.commit()

    return jsonify({'message': 'Left channel'}), 200

if __name__ == '__main__':
    app.run(debug=True)
