from main import db
from sqlalchemy_serializer import SerializerMixin

class Conversation(db.Model, SerializerMixin):
    serialize_only = ('id', 'content')
    
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(500))