import re
import requests
from app import database
from enum import Enum
from queue import Queue
import time

teamAnalyticAPIKey = 'RGAPI-5b5ad231-cb44-4bd0-9306-d58dc37ca228'


class QueueType(Enum):
    Normal = 1
    Ranked = 2


def registerSummoner(summoner):
    # TODO Buscar la forma de hacer las request mediante la función doRequest()
    # Agrega la clave de la API a la solicitud
    headers = {'X-Riot-Token': teamAnalyticAPIKey}

    # Endpoint de la API para obtener información del invocador por nombre (su longitud máxima es 16)
    # y por puuid (si la longitud es de exactamente 78)
    if len(summoner) == 78:
        summonerPUUID_api_url = f'https://euw1.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/{summoner}'
        response = requests.get(summonerPUUID_api_url, headers=headers)
    else:
        summonerName_api_url = f'https://euw1.api.riotgames.com/lol/summoner/v4/summoners/by-name/{summoner}'
        response = requests.get(summonerName_api_url, headers=headers)

    # Verifica si la solicitud fue exitosa (código de respuesta 200)
    if response.status_code == 200:
        data = response.json()
        puuid = data["puuid"]
        champion_mastery_url = f'https://euw1.api.riotgames.com/lol/champion-mastery/v4/champion-masteries/by-puuid/{puuid}'
        # Realiza la solicitud a la API de Champion-MasteryV4 de Riot Games
        response2 = requests.get(champion_mastery_url, headers=headers)

        if response2.status_code == 200:
            data2 = response2.json()
            # Eliminamos el campo redundante summonerId
            for champion_mastery in data2:
                champion_mastery.pop("summonerId", None)
            data["championMasteries"] = data2
            data["lastGame"] = 0
            database.insertPlayerDB(summoner, data)

        else:
            print(f'Error en la solicitud: {response2.status_code}')

    else:
        print(f'Error en la solicitud: {response.status_code}')


def updateChampions():
    # TODO Buscar la forma de hacer las request mediante la función doRequest()
    # URL de la página web empleada por Riot Games para publicar el json con todos los campeones del juego
    championsURL = 'https://developer.riotgames.com/docs/lol#data-dragon_champions'

    # Realiza la solicitud HTTP a la URL
    response = requests.get(championsURL)

    if response.status_code == 200:
        # Expresión regular actualizada para encontrar el enlace
        patron_enlace = r'(https://ddragon\.leagueoflegends\.com/cdn/\d+(\.\d+)+/data/en_US/champion\.json)'

        # Buscar el enlace usando la expresión regular
        enlace_encontrado = re.search(patron_enlace, response.text).group()

        # Descarga el JSON en el caso de encontrar el enlace
        if enlace_encontrado:
            response2 = requests.get(enlace_encontrado)
            if response2.status_code == 200:
                # Envía el response2.json() al fichero database para que lo parsee e introduzca los campeones en su DB
                database.updateChampionsDB(response2.json())
            else:
                print(f'Error en la solicitud: {response.status_code}')
        else:
            print('No hay enlaces coincidentes')
    else:
        print(f'Error en la solicitud: {response.status_code}')


def getIDMatches(puuid, queue, startTime, endTime, count):
    # Se construye la url basándose en el tipo de cola indicada en el parámetro
    if queue == QueueType.Normal:
        queue_param = 'normal'
    elif queue == QueueType.Ranked:
        queue_param = 'ranked'
    else:
        raise ValueError("Tipo de cola no válido")

    matchesAPIurl = f'https://europe.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?type={queue_param}&startTime={startTime}&endTime={endTime}&count={count}'
    return doRequest(matchesAPIurl)

    # Ahora, puedes usar los IDs de las partidas para obtener detalles de cada partida y almacenarlos en la base de datos.


def getMatches(puuid):
    # Se crea una cola de jugadores a procesar
    puuidQueue = Queue()
    puuidQueue.put(puuid)

    while puuidQueue.not_empty:
        # TODO Una vez la funcionalidad esté completa, añadir el result para QueueType.Ranked
        # Primero, almacenamos el jugador en la base de datos si este no estaba ya
        puuidActual = puuidQueue.get()
        nameActual = getSummonerName(puuidActual)
        registerSummoner(nameActual)
        # Segundo, obtenemos 100 IDs de las partidas en las que ha participado el jugador puuid_actual (ya que count
        # puede ser 100 como máximo) utilizando la primera de las APIs. Hay que utilizar como startTime el atributo de
        # la última partida guardada en el jugador (inicialmente 0). Si el resultado es vacío, pasar
        # al siguiente jugador directamente
        lastGameActual = database.getLastGame(puuidActual)
        endTime = round(time.time())
        result = getIDMatches(puuidActual, QueueType.Normal, lastGameActual, endTime, 100)
        if not result:
            continue
        else:
            # Tercero, comprobamos la fecha de la primera partida (la última que ha jugado) y la almacenamos como
            # información dentro del fichero del jugador
            setSummonerLastGame(puuidActual, result[0])
            while result:
                matchList = createIDList(result)
                # Cuarto, de forma iterativa, comprobamos si la partida ya existe en la BBDD y, solo si no es la última,
                # eliminarla del buffer de resultados en ese caso
                for matchID in matchList:
                    if database.checkGameDB(matchID):
                        continue
                    else:
                        matchInfo = getMatchInfo(matchID)
                        database.storeGameDB(matchInfo)
                        # TODO Añadir los IDs de los jugadores nuevos a la puuidQueue
                    if len(matchList) == 1:
                        endTime = matchInfo['info']['gameCreation']
                # Quinto, comprobamos la fecha de la última partida y, tras procesar esas 100 partidas, volvemos a buscar
                # otros 100 IDs utilizando como endTime esta fecha
                result = getIDMatches(puuidActual, QueueType.Normal, lastGameActual, endTime, 100)
            continue

        # En líneas generales, deberían procesarse todas las partidas disputadas por el jugador hasta el 16 de junio de
        # 2021, fecha en la que se almacenan las primeras partidas localizables con parámetros temporales

    print('Ya no hay más jugadores nuevos que procesar')


def createIDList(idsJSON):
    matchList = []
    for matchID in idsJSON:
        matchList.append(matchID)
    return matchList


def getSummonerName(puuidActual):
    summonerPUUIDAPI = f'https://euw1.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/{puuidActual}'
    data = doRequest(summonerPUUIDAPI)
    return data["name"]


def getSummonerPUUID(summonerName):
    summonerNameAPI = f'https://euw1.api.riotgames.com/lol/summoner/v4/summoners/by-name/{summonerName}'
    data = doRequest(summonerNameAPI)
    return data["puuid"]


def setSummonerLastGame(puuid, matchID):
    matchesInfoAPI = f'https://europe.api.riotgames.com/lol/match/v5/matches/{matchID}'
    data = doRequest(matchesInfoAPI)
    matchDate = data['info']['gameCreation']
    database.setLastGame(puuid, matchDate)


def getMatchInfo(matchID):
    matchesInfoAPI = f'https://europe.api.riotgames.com/lol/match/v5/matches/{matchID}'
    return doRequest(matchesInfoAPI)


def doRequest(APIurl):
    headers = {'X-Riot-Token': teamAnalyticAPIKey}
    response = requests.get(APIurl, headers=headers)
    if response.status_code == 200:
        return response.json()
    elif response.status_code == 429:
        # TODO Recuperar valor de los segundos de la cabecera de response 'retry-after'[1] y esperar esos segundos
        waitTime = response.headers["retry-after"]
        time.sleep(int(waitTime)+1)
        response = requests.get(APIurl, headers=headers)
        return response.json()
    else:
        print(f"Error: {response.status_code}")
        exit(1)
