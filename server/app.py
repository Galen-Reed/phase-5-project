#!/usr/bin/env python3

# Standard library imports

# Remote library imports
from flask import request, session, make_response
from flask_restful import Resource

# Local imports
from config import app, db, api
# Add your model imports
from models import User, Note, Coffee, Cafe


# Views go here!

class Signup(Resource):
    def post(self):
        data = request.get_json()

        username = data.get("username")
        password = data.get("password")

        if not username or not password:
            return {"error": "Username and password are required"}, 422
        
        if User.query.filter_by(username=username).first():
            return {"error": "Username already exists"}, 422
        
        new_user = User(username=username)
        new_user.password_hash = password

        db.session.add(new_user)
        db.session.commit()

        session["user_id"] = new_user.id

        return make_response(new_user.to_dict(), 200)
    
class CheckSession(Resource):
    def get(self):
        user = User.query.filter(User.id == session.get('user_id')).first()

        if user:
            return make_response(user.to_dict(), 200)
        else:
            return {"error": "User not signed in"}, 401
            
class Login(Resource):
    def post(self):
        data = request.get_json()
        username = data.get("username")
        password = data.get("password")

        user = User.query.filter_by(username=username).first()

        if user and user.authenticate(password):
            session["user_id"] = user.id
            return make_response(user.to_dict(), 200)
        else:
            return {"error": "Invalid username or password"}, 401
            
class Logout(Resource):
    def delete(self):
        user = User.query.filter(User.id == session.get('user_id')).first()

        if user:
            session['user_id'] = None
            return {'message': '204: No Content'}, 204
        else:
            return {'message': '401: Not authorized'}, 401