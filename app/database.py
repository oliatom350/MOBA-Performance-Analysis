from pymongo import MongoClient

# TODO Si migramos la base de datos de local a otro sitio, hay que cambiar el argumento de MongoClient(), ya que
#  así funciona para localhost:27017
cliente = MongoClient()
db = cliente['TFG']
dbChampions = db['Champions']
dbMatches = db['Matches']
dbSummoner = db['Summoners']


def insertPlayerDB(name, puuid, data):
    existing_player = dbSummoner.find_one({"puuid": puuid})

    if existing_player is None:
        # No existe, realizamos la inserción
        result = dbSummoner.insert_one(data)
        print(f"Se ha insertado un nuevo jugador con ID: {result.inserted_id}")
        print(f'PUUID del Invocador: {puuid}')
        print(f'Nivel del Invocador: {data["summonerLevel"]}')
        return True
    else:
        # Ya existe, actualizamos la información
        dbSummoner.update_one({"puuid": puuid}, {"$set": data})
        print(f"El jugador con nombre {name} ya existe en la base de datos y se ha actualizado su información.")
        return False


def updateChampionsDB(json):
    for champ_name, champ_data in json['data'].items():
        champ = {champ_name: champ_data}

        existing_champion = dbChampions.find_one({f"{champ_name}.id": champ_data['id']})

        if existing_champion is None:
            # No existe, realizamos la inserción
            result = dbChampions.insert_one(champ)
            print(f"Se ha insertado un nuevo campeón con ID: {result.inserted_id}")
            print(f'ID del Campeón: {champ_data["id"]}')
        else:
            # Ya existe, actualizamos la información
            dbChampions.update_one({"id": champ_data['id']}, {"$set": champ})
            print(f"Se ha actualizado la información del campeón con ID: {champ_data['id']}")


def clearCollection(idCollection):
    # TODO Muy importante modificar el dato idCollection si se quieren eliminar los datos de una database concreta
    # idCollection = 0
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
    else:
        print(f"No se ha eliminado ninguna colección. Introduce un valor de colección correcto:"
              f"Champions -- 0      Matches -- 1        Summoner -- 2")


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


def checkGameDB(matchID):
    match = dbMatches.find_one({"metadata.matchId": matchID})
    if match:
        return True
    else:
        return False


def storeGameDB(matchInfo):
    matchID = matchInfo["metadata"]["matchId"]
    existing_match = dbMatches.find_one({"metadata.matchId": matchID})

    if existing_match is None:
        # No existe, realizamos la inserción
        dbMatches.insert_one(matchInfo)
        print(f"Se ha insertado una nueva partida con matchId: {matchID}")
        return matchInfo["metadata"]["participants"]
    else:
        # Ya existe, esta vez NO actualizamos la información
        print(f"Ya existe una partida con matchId: {matchID}.")
        return []


def checkPlayerDB(player):
    existing_player = dbSummoner.find_one({"puuid": player})
    if existing_player:
        # Devuelve False si no existe el jugador en la BBDD, True en caso contrario
        return False
    return True
