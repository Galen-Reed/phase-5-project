#!/usr/bin/env python3

# Standard library imports

# Remote library imports
from flask import request, session, make_response
from flask_restful import Resource

# Local imports
from config import app, db, api, github
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
        
class GitHubAuth(Resource):
    def get(self):
        """Initiate GitHub OAuth login"""
        redirect_uri = url_for('githubcallback', _external=True)
        authorization_url = github.authorize_redirect(redirect_uri)
        return make_response(authorization_url)

class GitHubCallback(Resource):
    def get(self):
        """Handle GitHub OAuth callback"""
        try:
            token = github.authorize_access_token()
            
            # Get user info from GitHub
            resp = github.get('user', token=token)
            github_user = resp.json()
            
            # Get user's email (might need separate API call)
            email_resp = github.get('user/emails', token=token)
            emails = email_resp.json()
            primary_email = next((email['email'] for email in emails if email['primary']), None)
            
            # Check if user already exists by GitHub ID
            user = User.find_by_github_id(github_user['id'])
            
            if user:
                # Existing OAuth user - just log them in
                session['user_id'] = user.id
                return {
                    "message": "Login successful",
                    "user": user.to_dict(),
                    "redirect": "/dashboard"
                }, 200
            else:
                # Check if user exists by username (in case they want to link accounts)
                existing_user = User.query.filter_by(username=github_user['login']).first()
                
                if existing_user and not existing_user.is_oauth_user:
                    # Username conflict with non-OAuth user
                    return {"error": "Username already exists with different auth method"}, 409
                
                # Create new OAuth user
                new_user = User.create_oauth_user({
                    'login': github_user['login'],
                    'id': github_user['id'],
                    'email': primary_email,
                    'avatar_url': github_user.get('avatar_url')
                })
                
                db.session.add(new_user)
                db.session.commit()
                
                session['user_id'] = new_user.id
                return {
                    "message": "Account created and logged in",
                    "user": new_user.to_dict(),
                    "redirect": "/dashboard"
                }, 201
                
        except Exception as e:
            print(f"OAuth error: {e}")
            return {"error": "OAuth authentication failed"}, 400

class GitHubLink(Resource):
    def post(self):
        """Link GitHub account to existing user (if logged in)"""
        if 'user_id' not in session:
            return {"error": "Must be logged in to link accounts"}, 401
        
        # This would typically require a separate OAuth flow
        # For now, we'll accept GitHub user data in the request
        data = request.get_json()
        github_id = data.get('github_id')
        avatar_url = data.get('avatar_url')
        
        if not github_id:
            return {"error": "GitHub ID required"}, 422
        
        # Check if GitHub account is already linked to another user
        existing_oauth_user = User.find_by_github_id(github_id)
        if existing_oauth_user:
            return {"error": "GitHub account already linked to another user"}, 422
        
        # Link to current user
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




api.add_resource(Signup, '/signup', endpoint='signup')
api.add_resource(CheckSession, '/check_session', endpoint='check_session')
api.add_resource(Login, '/login', endpoint='login')
api.add_resource(Logout, '/logout', endpoint='logout')
api.add_resource(GitHubAuth, '/auth/github')
api.add_resource(GitHubCallback, '/auth/github/callback')
api.add_resource(GitHubLink, '/auth/github/link')
api.add_resource(OAuthStatus, '/auth/status')

if __name__ == '__main__':
    app.run(port=5555, debug=True)