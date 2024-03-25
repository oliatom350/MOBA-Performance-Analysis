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
def userEmpty():
    data = {'empty': 'No hay nombre de jugador'}
    return jsonify(data)


@app.route('/<username>')
def testUser(username):
    puuid = api.getSummonerPUUID(username)
    if puuid is None:
        data = {'message': 'No existe el jugador'}
    else:
        if database.checkPlayerDB(puuid):
            champMasteries = database.getSummonerMasteries(puuid)
            data = {'puuid': puuid,
                    'name': username,
                    'searchTime': time.asctime(),
                    'masteries': {}}
            if champMasteries is None:
                data['masteries'] = 'No se han recuperado correctamente las maestrías'
            for mastery in champMasteries:
                champName = database.getChampionByKey(mastery['championId'])
                champId = database.getChampionIdByKey(mastery['championId'])
                if champName is None and champId is None:
                    data['masteries'][mastery['championId']] = mastery['championPoints']
                elif champName is None:
                    data['masteries'][champId] = {'championPoints': mastery['championPoints'],
                                                  'championLevel': mastery['championLevel']}
                else:
                    data['masteries'][champName] = {'championPoints': mastery['championPoints'],
                                                    'championLevel': mastery['championLevel'],
                                                    'champId': champId}

            iconAndLevelDict = database.getSummonerIconAndLevel(puuid)
            if iconAndLevelDict is not None:
                data['profileIconId'] = iconAndLevelDict['profileIconId']
                data['summonerLevel'] = iconAndLevelDict['summonerLevel']
        else:
            data = {'message': 'No existe el jugador dentro de la BBDD'}
    return jsonify(data)


if __name__ == '__main__':
    app.run()
