import time

from flask import Flask, jsonify
from flask_cors import CORS
from markupsafe import escape

import api
import database
import proc_data

app = Flask(__name__)
CORS(app)


# @app.route('/<username>')
# def showUserProfile(username):
#     # show the user profile for that user
#     return f'User {escape(username)}'


# @app.route('/', methods=['POST', 'GET'])
# def hello():
#     if request.method == 'GET':
#         return '<p>Hello, World. This is GET request</p>'
#     else:
#         return '<p>Hello, World. This is POST request</p>'


@app.route('/')
def testHello():
    data = {'message': 'Hello from Flask!'}
    return jsonify(data)


@app.route('/<username>')
def testUser(username):
    puuid = api.getSummonerPUUID(username)
    if puuid is None:
        data = {'message': 'No existe el jugador'}
    else:
        if database.checkPlayerDB(puuid):
            data = {'puuid': puuid,
                    'name': username,
                    'searchTime': time.asctime()}
        else:
            data = {'message': 'No existe el jugador dentro de la BBDD'}
    return jsonify(data)


if __name__ == '__main__':
    app.run()
