import re
import requests
from app import database
from enum import Enum
from queue import Queue
import time

teamAnalyticAPIKey = 'RGAPI-5b5ad231-cb44-4bd0-9306-d58dc37ca228'


class QueueType(Enum):
    Normal = 1
    Ranked_Solo = 2
    Ranked_Flex = 3


def registerSummoner(summoner_name):
    # Endpoint de la API para obtener información del invocador por nombre
    summoner_api_url = f'https://euw1.api.riotgames.com/lol/summoner/v4/summoners/by-name/{summoner_name}'

    # Agrega la clave de la API a la solicitud
    headers = {'X-Riot-Token': teamAnalyticAPIKey}

    # Realiza la solicitud a la API de SummonerV4 de Riot Games
    response = requests.get(summoner_api_url, headers=headers)
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
            database.insertPlayerDB(summoner_name, data)

        else:
            print(f'Error en la solicitud: {response2.status_code}')

    else:
        print(f'Error en la solicitud: {response.status_code}')


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
        else:
            print('No hay enlaces coincidentes')
    else:
        print(f'Error en la solicitud: {response.status_code}')


def getIDMatches(puuid, queue, startTime, endTime, count):
    # Se construye la url basándose en el tipo de cola indicada en el parámetro
    if queue == QueueType.Normal:
        queue_param = 'normal'
    elif queue == QueueType.Ranked_Solo or QueueType.Ranked_Flex:
        queue_param = 'ranked'
    else:
        raise ValueError("Tipo de cola no válido")

    matchesAPIurl = f'https://europe.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?type={queue_param}&startTime={startTime}&endTime={endTime}&count={count}'
    # Agrega la clave de la API a la solicitud
    headers = {'X-Riot-Token': teamAnalyticAPIKey}

    response = requests.get(matchesAPIurl, headers=headers)

    if response.status_code == 200:
        match_ids = response.json()
        return match_ids
    else:
        print(f"Error: {response.status_code}")
        exit(1)

    # Ahora, puedes usar los IDs de las partidas para obtener detalles de cada partida y almacenarlos en la base de datos.


def getMatches():
    # TODO Se establece un puuid de un player inicial
    puuid = 1
    # Se crea una cola de jugadores a procesar
    puuidQueue = Queue()
    puuidQueue.put(puuid)

    while puuidQueue.not_empty:
        # Primero, obtenemos 100 IDs de las partidas en las que ha participado el jugador puuid_actual (ya que count
        # puede ser 100 como máximo) utilizando la primera de las APIs. Hay que utilizar como startTime el atributo de
        # la última partida guardada en el jugador, pero si no existe, entonces usar 0. Si el resultado es vacío, pasar
        # al siguiente jugador directamente

        # Segundo, de forma iterativa, comprobamos si la partida ya existe en la BBDD y eliminarla del buffer de
        # resultados en ese caso

        # Tercero, comprobamos la fecha de la primera partida (la última que ha jugado) y la almacenamos como
        # información dentro del fichero del jugador

        # Cuarto, comprobamos la fecha de la última partida y, tras procesar esas 100 partidas, volvemos al primer paso
        # utilizando como endTime esta fecha

        # En líneas generales, deberían procesarse todas las partidas disputadas por el jugador hasta el 16 de junio de
        # 2021, fecha en la que se almacenan las primeras partidas localizables con parámetros temporales
        break

    print('Ya no hay más jugadores nuevos que procesar')
