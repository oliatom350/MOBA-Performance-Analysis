import time

from flask import Flask, jsonify, make_response
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
    data = {'message': 'Por favor, introduce un nombre de usuario.'}
    return jsonify(data)


@app.route('/<username>')
def testUser(username):
    puuid = api.getSummonerPUUID(username)
    if puuid is None:
        data = {'message': 'No existe el jugador'}
        return make_response(jsonify(data), 404)
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
            elo = database.getSummonerElo(puuid)
            if elo is not None:
                data['elo'] = elo
        else:
            data = {'message': 'No existe el jugador dentro de la BBDD'}
            return make_response(jsonify(data), 404)
    return jsonify(data)


@app.route('/<username>/update')
def updateUser(username):
    if api.registerSummoner(username) is None:
        return {'error': {}}
    else:
        return {'success': {}}


if __name__ == '__main__':
    app.run()
