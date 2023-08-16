import json
from flask import Flask, request, jsonify
from flask_mongoengine import MongoEngine

app = Flask(__name__)
app.config['MONGODB_SETTINGS'] = {
  'host':'mongodb://localhost:27017/progress_tracker'}
db = MongoEngine()
db.init_app(app)

class User(db.Document):
    first_name = db.StringField()
    last_name = db.StringField()
    username = db.StringField()
    password = db.StringField()
    profile_image = db.StringField()
    email = db.StringField()
    role = db.StringField()
    shows_watched = db.StringField()

    def to_json(self):
        return {"firstname": self.first_name, 
                "lastname": self.last_name,
                "username": self.username,
                "password": self.password, 
                "profile_image": self.profile_image,
                "email": self.email, 
                "role": self.role,
                "shows_watched": self.shows_watched}

@app.route('/users', methods=['GET'])
def query_records():
    first_name= request.args.get("firstname")
    #user = User.objects()
    user = User.objects(first_name= first_name).first()
    if not user:
        return jsonify({'error': 'data not found'})
    else:
        return jsonify(user)

@app.route('/', methods=['PUT'])
def create_record():
    record = json.loads(request.data)
    user = User(name=record['name'],
                email=record['email'])
    user.save()
    return jsonify(user.to_json())

@app.route('/', methods=['POST'])
def update_record():
    record = json.loads(request.data)
    user = User.objects(first_name=record['name']).first()
    if not user:
        return jsonify({'error': 'data not found'})
    else:
        user.update(email=record['email'])
    return jsonify(user.to_json())

@app.route('/', methods=['DELETE'])
def delete_record():
    record = json.loads(request.data)
    user = User.objects(first_name=record['name']).first()
    if not user:
        return jsonify({'error': 'data not found'})
    else:
        user.delete()
    return jsonify(user.to_json())

if __name__ == "__main__":
    app.run(debug=True)