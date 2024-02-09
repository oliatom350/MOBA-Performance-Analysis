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
    # Agrega la clave de la API a la solicitud
    headers = {'X-Riot-Token': teamAnalyticAPIKey}

    # Endpoint de la API para obtener información del invocador por nombre (su longitud máxima es 16)
    # y por puuid (si la longitud es de exactamente 78)
    if len(summoner) == 78:
        summonerPUUID_api_url = f'https://euw1.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/{summoner}'
        response = doRequest(summonerPUUID_api_url)
    else:
        summonerName_api_url = f'https://euw1.api.riotgames.com/lol/summoner/v4/summoners/by-name/{summoner}'
        response = doRequest(summonerName_api_url)

    puuid = response["puuid"]
    champion_mastery_url = f'https://euw1.api.riotgames.com/lol/champion-mastery/v4/champion-masteries/by-puuid/{puuid}'

    # Realiza la solicitud a la API de Champion-MasteryV4 de Riot Games
    response2 = doRequest(champion_mastery_url)
    # Eliminamos el campo redundante summonerId
    for champion_mastery in response2:
        champion_mastery.pop("summonerId", None)
    response["championMasteries"] = response2
    response["lastGame"] = 0
    return database.insertPlayerDB(summoner, puuid, response)


def updateChampions():
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
                print(f"Time1: {time.strftime('%H:%M:%S', time.localtime())}")
        else:
            print('No hay enlaces coincidentes')
    else:
        print(f'Error en la solicitud: {response.status_code}')
        print(f"Time2: {time.strftime('%H:%M:%S', time.localtime())}")


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
    while not len(puuidQueue.queue) == 0:
        puuidActual = puuidQueue.get()
        nameActual = getSummonerName(puuidActual)
        newSummoner = registerSummoner(nameActual)
        newPlayers = []
        if newSummoner:
            newPlayers = getPlayerMatches(puuidActual, False)
        else:
            newPlayers = getPlayerMatches(puuidActual, True)
        for player in newPlayers:
            puuidQueue.put(player)

    print('Ya no hay más jugadores nuevos que procesar')


def getPlayerMatches(puuid, existing: bool):
    # Primero, obtenemos 100 IDs de las partidas en las que ha participado el jugador puuid_actual (ya que count
    # puede ser 100 como máximo) utilizando la primera de las APIs. Si el resultado es vacío, pasar
    # al siguiente jugador directamente.
    # Si el jugador existe en la base de datos, hay que utilizar como startTime el atributo de
    # la última partida guardada en el jugador. Si NO existe, se utiliza como startTime la fecha límite de la API
    # para almacenar partidas
    newPlayers = list()
    if existing:
        limitAPIDate = database.getLastGame(puuid)
    else:
        limitAPIDate = 1623801600
    endTime = round(time.time())
    result = getNormalAndRankedIDs(puuid, limitAPIDate, endTime)
    if not result:
        pass
    else:
        # Segundo, comprobamos la fecha de la primera partida (la última que ha jugado) y la almacenamos como
        # información dentro del fichero del jugador
        setSummonerLastGame(puuid, result[0])
        while result:
            # Tercero, de forma iterativa, comprobamos si la partida ya existe en la BBDD y, solo si no es la última,
            # simplemente guardarla en la BBDD. En el caso de ser la última, recupera también su fecha de creación para
            # realizar la siguiente búsqueda
            for matchID in result:
                if database.checkGameDB(matchID) or database.checkGameBlacklist(matchID):
                    continue
                else:
                    matchInfo = getMatchInfo(matchID)
                    # Al haber comprobado que a veces la API devuelve IDs consecutivos de partidas no almacenadas, se
                    # continúa el procesamiento ignorando los IDs sin información
                    if matchInfo is None:
                        continue
                    participants = database.storeGameDB(matchInfo)
                    for player in participants:
                        if database.checkPlayerDB(player):
                            newPlayers.append(player)
                # TODO: Hacer un try-catch y no almacenar endTime nuevo en caso de que sea vacío
                endTime = int(str(matchInfo['info']['gameCreation'])[:-3])
            # Cuarto, tras comprobar la fecha de la última partida y habiendo procesado esas 100 partidas, volvemos a buscar
            # otros 100 IDs utilizando como endTime esta fecha
            result2 = getNormalAndRankedIDs(puuid, limitAPIDate, endTime)
            # Para salir del bucle, se comprueba si la longitud del nuevo resultado de búsquedas es 0, es decir, no hay
            # más partidas que procesar. Además, para evitar loops infinitos, se comprueba que el resultado de la
            # búsqueda no sea exactamente el mismo que en la anterior iteración
            if len(result2) == 0 or result == result2:
                break
            else:
                result = result2
    return newPlayers
    # En líneas generales, deberían procesarse todas las partidas disputadas por el jugador hasta el 16 de junio de
    # 2021, fecha en la que se almacenan las primeras partidas localizables con parámetros temporales.
    # Se devuelve una lista con todos los nuevos jugadores detectados para ser procesados


def getNormalAndRankedIDs(puuid, limitDate, endTime):
    result = getIDMatches(puuid, QueueType.Normal, limitDate, endTime, 100)
    resultRanked = getIDMatches(puuid, QueueType.Ranked, limitDate, endTime, 100)
    result = result + resultRanked
    return result


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
    matchInfo = doRequest(matchesInfoAPI)
    if matchInfo is None:
        print(f'No se ha recuperado la partida con id {matchID}')
        database.storeEmptyGameIDDB(matchID)
    return matchInfo


# def getNewPlayers(matchInfo):
#     # TODO Debe comprobar cuáles de todos los jugadores de la partida no están en la base de datos y devolverlos
#     pass


def doRequest(APIurl):
    headers = {'X-Riot-Token': teamAnalyticAPIKey}
    response = requests.get(APIurl, headers=headers)

    # Tratamiento de errores de respuesta
    if response.status_code == 200:
        return response.json()
    elif response.status_code == 429:
        waitTime = int(response.headers["retry-after"])
        print(f"Esperando {waitTime} segundos para continuar con la petición de partidas...")
        time.sleep(int(waitTime / 2))
        print(f"Esperando {int(waitTime - waitTime / 2 + 1)} segundos para continuar con la petición de partidas...")
        time.sleep(int(waitTime - waitTime / 2 + 1))
        response = doRequest(APIurl)
        return response
    elif response.status_code == 403 or response.status_code == 404:
        if APIurl.startswith('https://europe.api.riotgames.com/lol/match/v5/matches/'):
            return None
        else:
            print(f"Error: {response.status_code}")
            print(f"Time3: {time.strftime('%H:%M:%S', time.localtime())}")
            exit(1)
    elif response.status_code == 500 or response.status_code == 503:
        return retryRequest(APIurl, headers)
    else:
        print(f"Error: {response.status_code}")
        print(f"Time4: {time.strftime('%H:%M:%S', time.localtime())}")
        exit(1)


def retryRequest(APIurl, headers):
    x = 0.5
    while True:
        print(f"Time: {time.time()}")
        print(f"Esperando {x} segundos")
        time.sleep(x)
        response = requests.get(APIurl, headers=headers)
        if response.status_code == 500 or response.status_code == 503:
            x = float(2 ^ int(x))
        else:
            break
    return response.json()
