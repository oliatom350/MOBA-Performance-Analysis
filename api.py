from typing import Mapping, Any
from pymongo.collection import Collection
import requests


def loginAPI(collection: Collection[Mapping[str, Any]], api_key, summoner_name):
    # Endpoint de la API para obtener información del invocador por nombre
    summoner_api_url = f'https://euw1.api.riotgames.com/lol/summoner/v4/summoners/by-name/{summoner_name}'

    # Agrega la clave de la API a la solicitud
    headers = {'X-Riot-Token': api_key}

    # Realiza la solicitud a la API de SummonerV4 de Riot Games
    response = requests.get(summoner_api_url, headers=headers)
    # Verifica si la solicitud fue exitosa (código de respuesta 200)
    if response.status_code == 200:
        data = response.json()
        idSummoner = data["id"]

        champion_mastery_url = f'https://euw1.api.riotgames.com/lol/champion-mastery/v4/champion-masteries/by-summoner/{idSummoner}'
        # Realiza la solicitud a la API de Champion-MasteryV4 de Riot Games
        response2 = requests.get(champion_mastery_url, headers=headers)

        if response2.status_code == 200:
            data2 = response2.json()
            # Eliminamos el campo redundante summonerId
            for champion_mastery in data2:
                champion_mastery.pop("summonerId", None)
            data["championMasteries"] = data2
            result = collection.update_one(
                {"id": idSummoner},
                {"$setOnInsert": data},
                upsert=True
            )
            if result.upserted_id:
                print(f"Se ha insertado un nuevo jugador con ID: {result.upserted_id}")
                print(f'ID del Invocador: {idSummoner}')
                print(f'Nivel del Invocador: {data["summonerLevel"]}')
            else:
                print(f"El jugador con ID {idSummoner} ya existe en la base de datos.")

        else:
            print(f'Error en la solicitud: {response.status_code}')

    else:
        print(f'Error en la solicitud: {response.status_code}')
