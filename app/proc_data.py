import time

from app import api, database

nGamesThreshold = 100


def processPlayer(name):
    puuid = api.getSummonerPUUID(name)
    getPlayerMatches(name, puuid)


def getPlayerMatches(name, puuid):
    matches = database.getAllPlayersGames(puuid)
    if len(matches) == 0:
        # Recuperar las primeras 100 partidas normales y las primeras 100 ranked del jugador
        matchesIDs = api.getNormalAndRankedIDs(puuid, 0, time.time(), 100)
        for matchID in matchesIDs:
            matchInfo = api.getMatchInfo(matchID)
            if matchInfo is None:
                continue
            matches.append(matchInfo)
    elif len(matches) <= nGamesThreshold:
        # Recuperar 'nGamesThreshold - len(matches)' partidas
        matchesIDs = api.getNormalAndRankedIDs(puuid, 0, time.time(), nGamesThreshold-len(matches))
        for matchID in matchesIDs:
            matchInfo = api.getMatchInfo(matchID)
            if matchInfo is None:
                continue
            matches.append(matchInfo)

    # Una vez llegados a este punto, deberían haberse recuperado un número mínimo de 100 partidas totales.
    # En el caso de que no sean suficientes, se mostrará un mensaje de que no hay suficientes datos para analizar al jugador
    print(f'Se han recuperado {len(matches)} partidas de {name}')
    getMatchesPosition(name, puuid, matches)


def getMatchesPosition(name, puuid, matches):
    top = jungle = mid = adc = supp = unknown = 0
    for match in matches:
        info = getMatchPlayerInfo(puuid, match)
        if info is None:
            continue
        lane = info['individualPosition']
        if lane == 'TOP':
            top += 1
        elif lane == 'JUNGLE':
            jungle += 1
        elif lane == 'MIDDLE':
            mid += 1
        elif lane == 'BOTTOM':
            adc += 1
        elif lane == 'UTILITY':
            supp += 1
        else:
            unknown += 1

    perTop = round((top * 100 / len(matches)), 2)
    perJg = round((jungle * 100 / len(matches)), 2)
    perMid = round((mid * 100 / len(matches)), 2)
    perAdc = round((adc * 100 / len(matches)), 2)
    perSupp = round((supp * 100 / len(matches)), 2)
    print(f"El jugador {name} ha jugado en las siguientes posiciones: \nTop: {top} veces ({perTop} %)\nJungla: {jungle} veces ({perJg} %)\nMid: "
          f"{mid} veces ({perMid} %)\nTirador: {adc} veces ({perAdc} %)\nSupport: {supp} veces ({perSupp} %)\n")


def getMatchPlayerInfo(puuid, match):
    # Buscar el índice del puuid en metadata
    index = None
    for indice, jugador in enumerate(match["metadata"]["participants"]):
        if jugador == puuid:
            index = indice
            break

    if index is None:
        return None  # El puuid no está en metadata

    # Obtener la información del jugador utilizando el índice en participants
    info = match.get("info", {})
    participants = info.get("participants", {})
    if 0 <= index < len(participants):
        return participants[index]
    else:
        return None

# FUNCIONES ESTADÍSTICAS DESCRIPTIVAS


# FUNCIONES GRÁFICAS TEMPORALES


# FUNCIONES ANÁLISIS CAMPEONES


# FUNCIONES ANÁLISIS ITEMIZACIÓN


### OPCIONAL ###
# FUNCIONES PARA MOSTRAR HEATMAPS
# FUNCIONES MACHINE LEARNING
# FUNCIONES DE ANÁLISIS POR SEGMENTACIÓN
