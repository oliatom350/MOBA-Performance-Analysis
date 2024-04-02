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
    puuid = api.getSummonerPUUID(username)
    registered = api.registerSummoner(username)
    if registered is None:
        return {'error': {}}
    else:
        api.storePlayerMatches(puuid, registered)
        return {'success': {}}


@app.route('/<username>/matchesPosition')
def getMatchesPosition(username):
    puuid = api.getSummonerPUUID(username)
    matches = database.getAllPlayersGames(puuid)
    dicPos = proc_data.getMatchesPosition(username, puuid, matches)
    return dicPos


@app.route('/<username>/KDA')
def getPlayerKDA(username):
    puuid = api.getSummonerPUUID(username)
    matches = database.getAllPlayersGames(puuid)
    dicKDA = proc_data.getPlayerKDA(username, puuid, matches)
    return dicKDA


@app.route('/<username>/winrate')
def getPlayerWinrate(username):
    puuid = api.getSummonerPUUID(username)
    matches = database.getAllPlayersGames(puuid)
    dicChamps = proc_data.getPlayerWinrate(username, puuid, matches)
    return dicChamps


@app.route('/<username>/championPool')
def getChampionPool(username):
    puuid = api.getSummonerPUUID(username)
    matches = database.getAllPlayersGames(puuid)
    selectedChamps = proc_data.definingChampPool2(username, puuid, matches)
    return selectedChamps


@app.route('/<username>/partnersResults')
def getPartnersResults(username):
    # TODO
    puuid = api.getSummonerPUUID(username)
    matches = database.getAllPlayersGames(puuid)
    partnersResults = proc_data.getResultsWithPartner(puuid, matches)
    return partnersResults


@app.route('/<username>/winrateVsChamps')
def getWinrateAgainstChampions(username):
    # TODO
    puuid = api.getSummonerPUUID(username)
    matches = database.getAllPlayersGames(puuid)
    winrateVsChamps = proc_data.getWinrateAgainstChampions(puuid, matches)
    return winrateVsChamps


@app.route('/<username>/winrateWChamps')
def getWinrateAlongsideChampions(username):
    # TODO
    puuid = api.getSummonerPUUID(username)
    matches = database.getAllPlayersGames(puuid)
    winrateWChamps = proc_data.getWinrateAlongsideChampions(puuid, matches)
    return winrateWChamps


@app.route('/<username>/playerData')
def getQuickPlayerData(username):
    # TODO
    puuid = api.getSummonerPUUID(username)
    matches = database.getAllPlayersGames(puuid)
    playerData = proc_data.getQuickPlayerInfo(username, puuid, matches)
    return playerData


@app.route('/<username>/heatmaps')
def getQuickPlayerData(username):
    # TODO
    puuid = api.getSummonerPUUID(username)
    matches = database.getAllPlayersGames(puuid)
    images = proc_data.drawKillsHeatmaps(puuid, matches)
    return images


if __name__ == '__main__':
    app.run()
