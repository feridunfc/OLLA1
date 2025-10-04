Sure, here is your corrected Flask application with two endpoints: `/register` and `/login`. The `/register` endpoint takes a username and password, hashes the password using Werkzeug's `generate_password_hash` function, and stores the hash in the database. 

The `/login` endpoint takes a username and password, checks if the user exists and if the provided password matches the stored one (using `check_password_hash`), then returns a JWT token:

```python
from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import (
    JWTManager, jwt_required, create_access_token, get_jwt_identity
)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'  # Use your own DB
app.config['JWT_SECRET_KEY'] = 'super-secret'  # Change this - make it stronger in production
jwt = JWTManager(app)
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return {"error": "Missing username or password"}, 400
        
    user = User(username=username)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    
    return {"message": f"User {username} created"}

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return {"error": "Missing username or password"}, 400
        
    user = User.query.filter_by(username=username).first()
    
    if not user or not user.check_password(password):
        return {"error": "Invalid username or password"}, 401
        
    access_token = create_access_token(identity=user.id)
    return {"access_token": access<｜begin▁of▁sentence｜>_token}
    
if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)
```
