from . import app
import os
import json
import pymongo
from flask import jsonify, request, make_response, abort, url_for, Response  # noqa; F401
from pymongo import MongoClient
from bson import json_util
from pymongo.errors import OperationFailure
from pymongo.results import InsertOneResult
from bson.objectid import ObjectId
from bson.json_util import dumps
import sys

SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
json_url = os.path.join(SITE_ROOT, "data", "songs.json")
songs_list: list = json.load(open(json_url))

# client = MongoClient(
#     f"mongodb://{app.config['MONGO_USERNAME']}:{app.config['MONGO_PASSWORD']}@localhost")
mongodb_service = os.environ.get('MONGODB_SERVICE')
mongodb_username = os.environ.get('MONGODB_USERNAME')
mongodb_password = os.environ.get('MONGODB_PASSWORD')
mongodb_port = os.environ.get('MONGODB_PORT')

print(f'The value of MONGODB_SERVICE is: {mongodb_service}')

if mongodb_service == None:
    app.logger.error('Missing MongoDB server in the MONGODB_SERVICE variable')
    # abort(500, 'Missing MongoDB server in the MONGODB_SERVICE variable')
    sys.exit(1)

if mongodb_username and mongodb_password:
    url = f"mongodb://{mongodb_username}:{mongodb_password}@{mongodb_service}"
else:
    url = f"mongodb://{mongodb_service}"


print(f"connecting to url: {url}")

try:
    client = MongoClient(url)
except OperationFailure as e:
    app.logger.error(f"Authentication error: {str(e)}")

db = client.songs
db.songs.drop()
db.songs.insert_many(songs_list)

def parse_json(data):
    return json.loads(json_util.dumps(data))

######################################################################
# INSERT CODE HERE
######################################################################
@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "OK"}), 200

@app.route("/count", methods=["GET"])
def count_songs():
    try:
        count = db.songs.count_documents({})
        return jsonify({"count": count}), 200
    except Exception as e:
        app.logger.error(f"Error accessing database: {str(e)}")
        return jsonify({"error": "Error accessing database", "message": str(e)}), 500


@app.route("/song", methods=["GET"])
def songs():
    try:
        songs_cursor = db.songs.find({})
        songs_list = list(songs_cursor)  
        return jsonify({"songs": json.loads(dumps(songs_list))}), 200
    except Exception as e:
        app.logger.error(f"Database access error: {str(e)}")
        return jsonify({"error": "Unable to access database", "message": str(e)}), 500


@app.route("/song/<int:id>", methods=["GET"])
def get_song_by_id(id):
    try:
        song = db.songs.find_one({"id": id})
        if not song:
            return jsonify({"message": "Song with id not found"}), 404
        return Response(dumps(song), mimetype='application/json'), 200
    except Exception as e:
        app.logger.error("Error accessing database: %s", e)
        return jsonify({"error": "Database access error", "message": str(e)}), 500

@app.route("/song", methods=["POST"])
def create_song():
    song_data = request.get_json()
    if not song_data:
        return jsonify({"message": "No data provided"}), 400

    # Assuming there's a global list called `songs_list` to store song data
    existing_song = next((item for item in songs_list if item['id'] == song_data['id']), None)
    
    if existing_song:
        return jsonify({"Message": f"Song with id {song_data['id']} already present"}), 302

    songs_list.append(song_data)
    return jsonify(song_data), 201


@app.route("/song/<int:id>", methods=["PUT"])
def update_song(id):
    song_data = request.get_json()
    if not song_data:
        return jsonify({"message": "No data provided"}), 400

    # Check if the song exists
    song = db.songs.find_one({"id": id})
    if song:
        # Update the song if it exists
        update_result = db.songs.update_one({"id": id}, {"$set": song_data})
        if update_result.modified_count == 0:
            # No fields were updated
            return jsonify({"message": "Song found, but nothing updated"}), 200
        else:
            # Fields were updated
            return jsonify({"message": "Song updated"}), 201
    else:
        # Song does not exist
        return jsonify({"message": "Song not found"}), 404

@app.route("/song/<int:id>", methods=["DELETE"])
def delete_song(id):
    result = db.songs.delete_one({"id": id})
    if result.deleted_count == 0:
        # No song was deleted because it wasn't found
        return jsonify({"message": "Song not found"}), 404
    else:
        # Song was successfully deleted
        return '', 204  # No content to return






