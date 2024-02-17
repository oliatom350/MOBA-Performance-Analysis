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
        matchesIDs = api.getNormalAndRankedIDs(puuid, 0, time.time(), nGamesThreshold - len(matches))
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
    topNorm = jungleNorm = midNorm = adcNorm = suppNorm = topSolo = jungleSolo = midSolo = adcSolo = suppSolo = topFlex \
        = jungleFlex = midFlex = adcFlex = suppFlex = unknown = totalNorm = totalSolo = totalFlex = unknownQueue = 0
    for match in matches:
        queueType = match['info']['queueId']
        info = getMatchPlayerInfo(puuid, match)
        if info is None:
            continue
        lane = info['individualPosition']
        if queueType == 400:
            totalNorm += 1
            # Tratamiento de Normales
            if lane == 'TOP':
                topNorm += 1
            elif lane == 'JUNGLE':
                jungleNorm += 1
            elif lane == 'MIDDLE':
                midNorm += 1
            elif lane == 'BOTTOM':
                adcNorm += 1
            elif lane == 'UTILITY':
                suppNorm += 1
            else:
                unknown += 1
        elif queueType == 420:
            totalSolo += 1
            # Tratamiento de Solo/Duo
            if lane == 'TOP':
                topSolo += 1
            elif lane == 'JUNGLE':
                jungleSolo += 1
            elif lane == 'MIDDLE':
                midSolo += 1
            elif lane == 'BOTTOM':
                adcSolo += 1
            elif lane == 'UTILITY':
                suppSolo += 1
            else:
                unknown += 1
        elif queueType == 440:
            totalFlex += 1
            # Tratamiento de Flex
            if lane == 'TOP':
                topFlex += 1
            elif lane == 'JUNGLE':
                jungleFlex += 1
            elif lane == 'MIDDLE':
                midFlex += 1
            elif lane == 'BOTTOM':
                adcFlex += 1
            elif lane == 'UTILITY':
                suppFlex += 1
            else:
                unknown += 1
        else:
            unknownQueue += 1
            continue

    perNorm = round((totalNorm * 100 / len(matches)), 2)
    perSolo = round((totalSolo * 100 / len(matches)), 2)
    perFlex = round((totalFlex * 100 / len(matches)), 2)
    perUnknownQueue = round((unknownQueue * 100 / len(matches)), 2)
    print(
        f"El jugador {name} ha jugado en las siguientes colas:\n"
        f"{totalNorm} partidas Draft normales ({perNorm}%)\n"
        f"{totalSolo} partidas Ranked Solo/Duo ({perSolo}%)\n"
        f"{totalFlex} partidas Ranked Flex ({perFlex}%)\n"
        f"{unknownQueue} partidas de otro tipo ({perUnknownQueue}%)\n"
    )
    totalMatchesCount = totalNorm+totalSolo+totalFlex
    perTop = round((topNorm+topSolo+topFlex * 100 / totalMatchesCount), 2)
    perJg = round((jungleNorm+jungleSolo+jungleFlex * 100 / totalMatchesCount), 2)
    perMid = round((midNorm+midSolo+midFlex * 100 / totalMatchesCount), 2)
    perAdc = round((adcNorm+adcSolo+adcFlex * 100 / totalMatchesCount), 2)
    perSupp = round((suppNorm+suppSolo+suppFlex * 100 / totalMatchesCount), 2)
    perUnknownPosition = round((unknown * 100 / totalMatchesCount), 2)
    print(
        f"También ha jugado en las siguientes posiciones: \n"
        f"Top: {topNorm+topSolo+topFlex} veces ({perTop} %)\n"
        f"Jungla: {jungleNorm+jungleSolo+jungleFlex} veces ({perJg} %)\n"
        f"Mid: {midNorm+midSolo+midFlex} veces ({perMid} %)\n"
        f"Tirador: {adcNorm+adcSolo+adcFlex} veces ({perAdc} %)\n"
        f"Support: {suppNorm+suppSolo+suppFlex} veces ({perSupp} %)\n"
        f"Línea desconocida: {unknown} veces ({perUnknownPosition} %)\n"
    )


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
