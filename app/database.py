from pymongo import MongoClient

# TODO Si migramos la base de datos de local a otro sitio, hay que cambiar el argumento de MongoClient(), ya que
#  así funciona para localhost:27017
cliente = MongoClient()
db = cliente['TFG']
dbChampions = db['Champions']
dbMatches = db['Matches']
dbSummoner = db['Summoners']


def insertarJugador(idSummoner, data):
    result = dbSummoner.update_one(
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
