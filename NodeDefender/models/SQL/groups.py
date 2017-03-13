from ... import db
from datetime import datetime

user_list = db.Table('user_list',
                     db.Column('group_id', db.Integer,
                               db.ForeignKey('group.id')),
                     db.Column('user_id', db.Integer,
                               db.ForeignKey('user.id'))
                    )
node_list = db.Table('node_list',
                     db.Column('group_id', db.Integer,
                               db.ForeignKey('group.id')),
                     db.Column('node_id', db.Integer,
                               db.ForeignKey('node.id'))
                    )

class GroupModel(db.Model):
    '''
    Representing one group containing iCPEs and Users
    '''
    __tablename__ = 'group'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    email = db.Column(db.String(120))
    description = db.Column(db.String(250))
    created_on = db.Column(db.DateTime)
    users = db.relationship('UserModel', secondary=user_list,
                            backref=db.backref('groups', lazy='dynamic'))
    messages = db.relationship('GroupMessageModel', backref='groupmessages')
    nodes = db.relationship('NodeModel', secondary=node_list,
                            backref=db.backref('groups', lazy='dynamic'))
    statistics = db.relationship('StatisticsModel', backref='groups', uselist=False)
   
    def __init__(self, name, description):
        self.name = name
        self.description = description
        self.created_on = datetime.now()

class GroupMessageModel(db.Model):
    '''
    Common messages for a group
    '''
    __tablename__ = 'groupmessage'
    id = db.Column(db.Integer, primary_key=True)
    parent_id = db.Column(db.Integer, db.ForeignKey('group.id'))
    created_on = db.Column(db.DateTime)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    author = db.relationship('UserModel', backref='groupmessageauthor')
    subject = db.Column(db.String(50))
    message = db.Column(db.String(300))

    def __init__(self, author, subject, message):
        self.author = author
        self.message = message
