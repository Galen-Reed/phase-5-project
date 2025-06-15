from config import db, bcrypt, ma

# Models go here!
class User(db.Model):
    __tablename__= "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    email = db.Column(db.String, unique=True, nullable=True)
    _password_hash = db.Column(db.String(100), nullable=False)

    github_id = db.Column(db.String, unique=True, nullable=True)
    avatar_url = db.Column(db.String, nullable=True)  
    is_oauth_user = db.Column(db.Boolean, default=False, nullable=False)

    #Relationships
    notes = db.relationship("Note", back_populates="user", cascade="all, delete-orphan")
    coffees = db.relationship("Coffee", secondary="notes",  back_populates="users", overlaps="notes")

    @property
    def password_hash(self):
        raise AttributeError("Password hashes may not be viewed")
    
    @password_hash.setter
    def password_hash(self, password):
        if password:
            self._password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    def authenticate(self, password):
        if self.is_oauth_user or not self._password_hash:
            return False
        return bcrypt.check_password_hash(self._password_hash, password)
    
    @classmethod
    def create_oauth_user(cls, github_data):
        """Create a new user from GitHub OAuth data"""
        user = cls(
            username=github_data.get('login'),  # GitHub username
            email=github_data.get('email'),
            github_id=str(github_data.get('id')),
            avatar_url=github_data.get('avatar_url'),
            is_oauth_user=True
        )
        return user
    
    @classmethod
    def find_by_github_id(cls, github_id):
        """Find user by GitHub ID"""
        return cls.query.filter_by(github_id=str(github_id)).first()
    
class Coffee(db.Model):
    __tablename__ = "coffees"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    description = db.Column(db.String, nullable=False)
    cafe_id = db.Column(db.Integer, db.ForeignKey("cafes.id"), nullable=False)

    notes = db.relationship("Note", back_populates="coffee", cascade="all, delete-orphan")
    users = db.relationship("User", secondary="notes", back_populates="coffees", overlaps="notes")
    cafe = db.relationship("Cafe", back_populates="coffees")

class Cafe(db.Model):
    __tablename__ = "cafes"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    location = db.Column(db.String, nullable=False)

    coffees = db.relationship("Coffee", back_populates="cafe")

class Note(db.Model):
    __tablename__ = "notes"

    id = db.Column(db.Integer, primary_key=True)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.String, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    coffee_id = db.Column(db.Integer, db.ForeignKey("coffees.id"), nullable=False)

    #Relationships
    user = db.relationship("User", back_populates="notes", overlaps="coffees,users")
    coffee = db.relationship("Coffee", back_populates="notes", overlaps="coffees,users")

#Marshmallow Schemas

class UserSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = User
        load_instance = True
        exclude = ("_password_hash", "github_id")
        include_relationships = True

    notes = ma.Nested("NoteSchema", many=True, exclude=("user",))
    coffees = ma.Nested("CoffeeSchema", many=True, exclude=("users", "notes"))

class CafeSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Cafe
        load_instance = True
        include_relationships = True

    coffees = ma.Nested("CoffeeSchema", many=True, exclude=("cafe",))

class CoffeeSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Coffee
        load_instance = True
        include_relationships = True

    cafe = ma.Nested(CafeSchema, exclude=("coffees",))
    notes = ma.Nested("NoteSchema", many=True, exclude=("coffee",))
    users = ma.Nested(UserSchema, many=True, exclude=("coffees", "notes"))

class NoteSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Note
        load_instance = True
        include_relationships = True

    user = ma.Nested(UserSchema, exclude=("notes", "coffees"))
    coffee = ma.Nested(CoffeeSchema, exclude=("notes", "users"))
