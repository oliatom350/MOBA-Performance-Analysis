from pymongo.collection import Collection
from typing import Mapping, Any

cliente = MongoClient()
db = cliente['TFG']
dbChampions = db['Champions']
dbMatches = db['Matches']
dbSummoner = db['Summoners']

def insertarJugador(collection: Collection[Mapping[str, Any]], idSummoner, data):
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
