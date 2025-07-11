from flask import request, session, make_response, redirect, url_for, jsonify
from flask_restful import Resource


from config import app, db, api, github

from models import User, Note, Coffee, Cafe, UserSchema, NoteSchema, CoffeeSchema, CafeSchema

user_schema = UserSchema()
users_schema = UserSchema(many=True)
note_schema = NoteSchema()
notes_schema = NoteSchema(many=True)
coffee_schema = CoffeeSchema()
coffees_schema = CoffeeSchema(many=True)
cafe_schema = CafeSchema()
cafes_schema = CafeSchema(many=True)

class Signup(Resource):
    def post(self):
        data = request.get_json()

        username = data.get("username")
        password = data.get("password")

        if not username or not password:
            return {"error": "Username and password are required"}, 422
        
        if User.query.filter_by(username=username).first():
            return {"error": "Username already exists"}, 422
        
        try:
            new_user = User(username=username, is_oauth_user=False)
            new_user.password_hash = password

            db.session.add(new_user)
            db.session.commit()

            session["user_id"] = new_user.id

            return make_response(user_schema.dump(new_user), 200)
        except Exception as e:
            db.session.rollback()
            print(f"Signup error: {e}")
            return {"error": "Failed to create account"}, 500
    
class CheckSession(Resource):
    def get(self):
        user = User.query.filter(User.id == session.get('user_id')).first()

        if user:

            for coffee in user.coffees:
                coffee.notes = [note for note in coffee.notes if note.user_id == user.id]
            return make_response(user_schema.dump(user), 200)
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
            return make_response(user_schema.dump(user), 200)
        else:
            return {"error": "Invalid username or password"}, 401
            
class Logout(Resource):
    def delete(self):
        session.clear()
        return {'message': '204: No Content'}, 204


class GitHubLogin(Resource):
    def get(self):
        print("🔐 GitHubLogin session before redirect:", dict(session))
        
        for key in list(session.keys()):
            if key.startswith('_state_github_'):
                session.pop(key)
        
        redirect_uri = url_for('github_callback', _external=True)
        resp = github.authorize_redirect(redirect_uri)
        print("🔐 GitHubLogin session AFTER redirect call:", dict(session))
        return resp

@app.route('/auth/github/callback')
def github_callback():
    """Handle GitHub OAuth callback"""
    try:
        token = github.authorize_access_token()
        user_data = github.get('user').json()
        
        username = user_data.get('login')
        email = user_data.get('email')
        
        if not email:
            emails = github.get('user/emails').json()
            email = next((e['email'] for e in emails if e['primary'] and e['verified']), None)
        
        if not email:
            return redirect("http://localhost:3000/login?error=email-not-found")
        
        user = User.query.filter_by(email=email).first()
        
        if not user:
            user = User(
                username=username,
                email=email,
                is_oauth_user=True,
                _password_hash=None
            )

            db.session.add(user)
            db.session.commit()
        
        session['user_id'] = user.id
        
        return redirect("http://localhost:3000")
        
    except Exception as e:
        print(f"OAuth error: {e}")
        return redirect("http://localhost:3000")

class GitHubLink(Resource):
    def post(self):
        """Link GitHub account to existing user (if logged in)"""
        if 'user_id' not in session:
            return {"error": "Must be logged in to link accounts"}, 401
        
        data = request.get_json()
        github_id = data.get('github_id')
        avatar_url = data.get('avatar_url')
        
        if not github_id:
            return {"error": "GitHub ID required"}, 422
        
        existing_oauth_user = User.find_by_github_id(github_id)
        if existing_oauth_user:
            return {"error": "GitHub account already linked to another user"}, 422

        current_user = User.query.get(session['user_id'])
        current_user.github_id = str(github_id)
        current_user.avatar_url = avatar_url
        
        db.session.commit()
        
        return {"message": "GitHub account linked successfully"}, 200

class OAuthStatus(Resource):
    def get(self):
        """Check if current user has OAuth linked"""
        if 'user_id' not in session:
            return {"error": "Not logged in"}, 401
            
        user = User.query.get(session['user_id'])
        if not user:
            return {"error": "User not found"}, 404
            
        return {
            "is_oauth_user": user.is_oauth_user,
            "has_github_linked": bool(user.github_id),
            "avatar_url": user.avatar_url
        }, 200

class Notes(Resource):
    def get(self):
        if 'user_id' not in session:
            return {"error": "Not logged in"}, 401
        
        notes = Note.query.filter_by(user_id=session["user_id"]).all()
        return notes_schema.dump(notes), 200
    
    def post(self):
        if "user_id" not in session:
            return {"error": "Not logged in"}, 401
        
        data = request.get_json()
        new_note = Note(
            rating=data.get("rating"),
            comment=data.get("comment"),
            user_id=session["user_id"],
            coffee_id=data.get("coffee_id")
        )
        
        db.session.add(new_note)
        db.session.commit()

        return note_schema.dump(new_note), 201

class NotesById(Resource):
    def get(self, id):
        if "user_id" not in session:
            return {"error": "Not logged in"}, 401
        
        note = Note.query.filter_by(id=id, user_id=session["user_id"]).first()
        if not note:
            return {"error": "Note not found"}, 404
        
        return note_schema.dump(note), 200
    
    def patch(self, id):
        if "user_id" not in session:
            return {"error": "Not logged in"}, 401
        
        note = Note.query.filter_by(id=id, user_id=session["user_id"]).first()
        if not note:
            return {"error": "Note not found"}, 404
        
        data = request.get_json()

        if "rating" in data:
            note.rating = data["rating"]
        if "comment" in data:
            note.comment = data["comment"]

        db.session.commit()

        return note_schema.dump(note), 200
    
    def delete(self, id):
        if 'user_id' not in session:
            return {"error": "Not logged in"}, 401
            
        note = Note.query.filter_by(id=id, user_id=session['user_id']).first()
        if not note:
            return {"error": "Note not found"}, 404
        
        db.session.delete(note)
        db.session.commit()

        return {"message": "Note deleted successfully"}, 200
    
class Coffees(Resource):
    def get(self):
        if "user_id" not in session:
            return {"error": "Not logged in"}, 401

        coffees = Coffee.query.all()
        return coffees_schema.dump(coffees), 200
    
    def post(self):
        if "user_id" not in session:
            return {"error": "Not logged in"}, 401
        
        data = request.get_json()

        if not data.get("name") or not data.get("cafe_id"):
            return {"error": "Name and cafe_id are required"}, 422
        
        cafe = db.session.get(Cafe, data.get("cafe_id"))
        if not cafe:
            return {"error": "Cafe not found"}, 404
        
        new_coffee = Coffee(
            name=data.get("name"),
            description=data.get("description"),
            cafe_id=data.get("cafe_id")
        )
        
        db.session.add(new_coffee)
        db.session.commit()

        return coffee_schema.dump(new_coffee), 201
    
class CoffeesById(Resource):
    def get(self, id):
        if "user_id" not in session:
            return {"error": "Not logged in"}, 401
        
        coffee = Coffee.query.get(id)
        if not coffee:
            return {"error": "Coffee not found"}, 404
        
        return coffee_schema.dump(coffee), 200
    
    def patch(self, id):
        if "user_id" not in session:
            return {"error": "Not logged in"}, 401
        
        coffee = Coffee.query.get(id)
        if not coffee:
            return {"error": "Coffee not found"}, 404
        
        data = request.get_json()

        if "name" in data:
            coffee.name = data["name"]
        if "description" in data:
            coffee.description = data["description"]
        
        db.session.commit()

        return coffee_schema.dump(coffee), 200
    
    def delete(self, id):
        if "user_id" not in session:
            return {"error": "Not logged in"}, 401
        
        coffee = db.session.get(Coffee, id)
        if not coffee:
            return {"error": "Coffee not found"}, 404
        
        db.session.delete(coffee)
        db.session.commit()

        return {"message": "Coffee deleted successfully"}, 200
    
class Cafes(Resource):
    def get(self):
        if "user_id" not in session:
            return {"error": "Not logged in"}, 401
        
        cafes = Cafe.query.all()

        return cafes_schema.dump(cafes), 200
    
    def post(self):
        if "user_id" not in session:
            return {"error": "Not logged in"}, 401
        
        data = request.get_json()

        if not data.get("name") or not data.get("location"):
            return {"error": "Name and location are required"}, 422
        
        new_cafe = Cafe(
            name=data.get("name"),
            location=data.get("location")
        )
        
        db.session.add(new_cafe)
        db.session.commit()

        return cafe_schema.dump(new_cafe), 201
    
class CafesById(Resource):
    def get(self, id):
        if "user_id" not in session:
            return {"error": "Not logged in"}, 401
        
        cafe = Cafe.query.get(id)
        if not cafe:
            return {"error": "Cafe not found"}, 404
        
        return cafe_schema.dump(cafe), 200
    
    def patch(self, id):
        if "user_id" not in session:
            return {"error": "Not logged in"}, 401
        
        cafe = Cafe.query.get(id)
        if not cafe:
            return {"error": "Cafe not found"}, 404
        
        data = request.get_json()

        if "name" in data:
            cafe.name = data["name"]
        if "location" in data:
            cafe.location = data["location"]

        db.session.commit()

        return cafe_schema.dump(cafe), 200
    
    def delete(self, id):
        if "user_id" not in session:
            return {"error": "Not logged in"}, 401
        
        cafe = Cafe.query.get(id)
        if not cafe:
            return {"error": "Cafe not found"}, 404

        db.session.delete(cafe)
        db.session.commit()

        return {"message": "Cafe deleted successfully"}, 200
    

api.add_resource(Signup, '/signup', endpoint='signup')
api.add_resource(CheckSession, '/check_session', endpoint='check_session')
api.add_resource(Login, '/login', endpoint='login')
api.add_resource(Logout, '/logout', endpoint='logout')
api.add_resource(GitHubLogin, '/auth/github', endpoint='github_login')
api.add_resource(GitHubLink, '/auth/github/link')
api.add_resource(OAuthStatus, '/auth/status')
api.add_resource(Notes, '/notes', endpoint="notes")
api.add_resource(NotesById, '/notes/<int:id>', endpoint="notes_by_id")
api.add_resource(Coffees, '/coffees', endpoint='coffees')
api.add_resource(CoffeesById, '/coffees/<int:id>', endpoint="coffees_by_id")
api.add_resource(Cafes, '/cafes', endpoint="cafes")
api.add_resource(CafesById, '/cafes/<int:id>', endpoint="cafes_by_id")


if __name__ == '__main__':
    app.run(port=5555, debug=True)