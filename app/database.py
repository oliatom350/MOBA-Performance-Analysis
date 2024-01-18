from pymongo import MongoClient

# TODO Si migramos la base de datos de local a otro sitio, hay que cambiar el argumento de MongoClient(), ya que
#  así funciona para localhost:27017
cliente = MongoClient()
db = cliente['TFG']
dbChampions = db['Champions']
dbMatches = db['Matches']
dbSummoner = db['Summoners']


def insertPlayerDB(idSummoner, data):
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


def updateChampionsDB(json):
    for champ_name, champ_data in json['data'].items():
        champ = {champ_name: champ_data}

        # Realiza la actualización de los datos del campeón
        result = dbChampions.update_one(
            {"id": champ_data['id']},
            {"$set": champ},
            upsert=True
        )
        # Sólo si el campeón no existía, entonces se inserta como nuevo
        if result.upserted_id:
            print(f"Se ha insertado un nuevo campeón con ID: {result.upserted_id}")
            print(f'ID del Campeón: {champ_data["id"]}')
        else:
            print(f"Se ha actualizado la información del campeón con ID: {champ_data['id']}")


def clearCollection():
    # TODO Muy importante modificar el dato idCollection si se quieren eliminar los datos de una database concreta
    idCollection = 0
    if idCollection == 0:
        # Eliminar todos los documentos de la colección
        result = dbChampions.delete_many({})
        # Imprimir el resultado
        print(f"Se han eliminado {result.deleted_count} documentos de la colección Champions.")
    elif idCollection == 1:
        # Eliminar todos los documentos de la colección
        result = dbMatches.delete_many({})
        # Imprimir el resultado
        print(f"Se han eliminado {result.deleted_count} documentos de la colección Matches.")
    elif idCollection == 2:
        # Eliminar todos los documentos de la colección
        result = dbSummoner.delete_many({})
        # Imprimir el resultado
        print(f"Se han eliminado {result.deleted_count} documentos de la colección Summoner.")


def getLastGame(puuid):
    summoner = dbSummoner.find_one({"puuid": puuid})
    if summoner:
        return summoner["lastGame"]
    else:
        print(f"No existe el jugador con PUUID {puuid} en la base de datos")


def setLastGame(puuid, time):
    dbSummoner.update_one(
        {"puuid": puuid}, {"$set": {"lastGame": time}},
    )
