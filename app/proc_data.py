from app import api, database

nGamesThreshold = 100


def processPlayer(name):
    puuid = api.getSummonerPUUID(name)
    matches = database.getAllPlayersGames(puuid)
    if len(matches) == 0:
        # TODO Recuperar las primeras 100 partidas normales y las primeras 100 ranked del jugador
        pass
    elif len(matches) <= nGamesThreshold:
        # TODO Recuperar 'nGamesThreshold - len(matches)' partidas
        pass

    # Una vez llegados a este punto, deberían haberse recuperado un número mínimo de 100 partidas totales.
    # En el caso de que no sean suficientes, se mostrará un mensaje de que no hay suficientes datos para analizar al jugador
    print(f'Se han recuperado {len(matches)} partidas de {name}')


# FUNCIONES ESTADÍSTICAS DESCRIPTIVAS


# FUNCIONES GRÁFICAS TEMPORALES


# FUNCIONES ANÁLISIS CAMPEONES


# FUNCIONES ANÁLISIS ITEMIZACIÓN


### OPCIONAL ###
# FUNCIONES PARA MOSTRAR HEATMAPS
# FUNCIONES MACHINE LEARNING
# FUNCIONES DE ANÁLISIS POR SEGMENTACIÓN
