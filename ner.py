import spacy
from flask import Flask, request, jsonify, render_template
from flask_socketio import SocketIO, emit
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy_serializer import SerializerMixin

import os

from dotenv import load_dotenv
load_dotenv()


app = Flask(__name__)

socketio = SocketIO(app, cors_allowed_origins="*")
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URI")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Suppress a warning message

db = SQLAlchemy(app)

class Conversation(db.Model, SerializerMixin):
    serialize_only = ('id', 'content')
    
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(500))

nlp = spacy.load("en_core_web_sm")

def extract_topics(text):
    doc = nlp(text)
    return [ent.text for ent in doc.ents]

def search_related_conversations(new_conversation):
    with app.app_context():

        topics = extract_topics(new_conversation)
        
        related_conversations = []

        for topic in topics:
            results = Conversation.query.filter(Conversation.content.contains(topic)).all()
            related_conversations.extend(results)
        
        return related_conversations

convos = search_related_conversations("Mountain Dew is almost like a Doritos")
for convo in convos:
    print(convo.content)
