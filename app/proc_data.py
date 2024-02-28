import time
from enum import Enum

from app import api, database

nGamesThreshold = 100


class DamageType(Enum):
    Physical = 1
    Magical = 2
    Hybrid = 3


def processPlayer(name):
    puuid = api.getSummonerPUUID(name)
    matches = getPlayerMatches(name, puuid)
    if matches is not None:
        # getMatchesPosition(name, puuid, matches)
        # getPlayerKDA(name, puuid, matches)
        # getPlayerWinrate(name, puuid, matches)
        # getMeanDuration(name, puuid, matches)
        definingChampPool(name, puuid, matches)
        # getResultsWithPartner(puuid, matches)


def getPlayerMatches(name, puuid):
    matches = database.getAllPlayersGames(puuid)
    if len(matches) == 0:
        # Recuperar las primeras 100 partidas normales y las primeras 100 ranked del jugador
        matchesIDs = api.getNormalAndRankedIDs(puuid, 0, round(time.time()), 100)
        if matchesIDs is None:
            print(f'No se han recuperado partidas del jugador {name}')
            return None
        for matchID in matchesIDs:
            matchInfo = api.getMatchInfo(matchID)
            if matchInfo is None:
                continue
            matches.append(matchInfo)
    elif len(matches) <= nGamesThreshold:
        # Recuperar 'nGamesThreshold - len(matches)' partidas
        while len(matches) != nGamesThreshold:
            matchesIDs = api.getNormalAndRankedIDs(puuid, 0, round(time.time()), nGamesThreshold - len(matches))
            # matchesIDs = api.getNormalAndRankedIDs(puuid, limitTime, endTime, 100)
            if matchesIDs is None or matchesIDs is []:
                break
            for matchID in matchesIDs:
                if not database.checkGameBlacklist(matchID):
                    matchInfo = api.getMatchInfo(matchID)
                    if matchInfo is None:
                        continue
                    elif matchInfo['info']['queueId'] != 400 and matchInfo['info']['queueId'] != 420 and \
                            matchInfo['info']['queueId'] != 440:
                        continue
                    else:
                        matches.append(matchInfo)
    # TODO Verificar los IDs antes de realizar la búsqueda en la API
    else:
        limitDate = database.getLastGame(puuid)
        endTime = round(time.time())
        while True:
            matchesIDs = api.getNormalAndRankedIDs(puuid, limitDate, endTime, 100)
            if matchesIDs is None or matchesIDs is [] or endTime < limitDate:
                break
            for matchID in matchesIDs:
                if database.checkGameDB(matchesIDs):
                    continue
                matchInfo = api.getMatchInfo(matchID)
                if matchInfo['info']['queueId'] != 400 and matchInfo['info']['queueId'] != 420 and \
                        matchInfo['info']['queueId'] != 440 or matchInfo is None:
                    continue
                else:
                    matches.append(matchInfo)
                try:
                    endTime = int(str(matchInfo['info']['gameCreation'])[:-3])
                except ValueError:
                    continue

    # Una vez llegados a este punto, deberían haberse recuperado un número mínimo de 100 partidas totales.
    # En el caso de que no sean suficientes, se mostrará un mensaje de que no hay suficientes datos para analizar al jugador
    print(f'Se han recuperado {len(matches)} partidas de {name}')
    return matches


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
    totalMatchesCount = totalNorm + totalSolo + totalFlex
    perTop = round(((topNorm + topSolo + topFlex) * 100 / totalMatchesCount), 2)
    perJg = round(((jungleNorm + jungleSolo + jungleFlex) * 100 / totalMatchesCount), 2)
    perMid = round(((midNorm + midSolo + midFlex) * 100 / totalMatchesCount), 2)
    perAdc = round(((adcNorm + adcSolo + adcFlex) * 100 / totalMatchesCount), 2)
    perSupp = round(((suppNorm + suppSolo + suppFlex) * 100 / totalMatchesCount), 2)
    perUnknownPosition = round((unknown * 100 / totalMatchesCount), 2)
    print(
        f"También ha jugado en las siguientes posiciones: \n"
        f"Top: {topNorm + topSolo + topFlex} veces ({perTop} %)\n"
        f"Jungla: {jungleNorm + jungleSolo + jungleFlex} veces ({perJg} %)\n"
        f"Mid: {midNorm + midSolo + midFlex} veces ({perMid} %)\n"
        f"Tirador: {adcNorm + adcSolo + adcFlex} veces ({perAdc} %)\n"
        f"Support: {suppNorm + suppSolo + suppFlex} veces ({perSupp} %)\n"
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


def getPlayerKDA(name, puuid, matches):
    # El objetivo de esta función es obtener:
    # - KDA total
    # - KDA en cada partida
    # - KDA total por tipo de cola
    # - KDA por campeón
    totaldeaths = totalkills = totalassists = deathsNormal = deathsSolo = deathsFlex = killsNormal = killsSolo = \
        killsFlex = assistsNormal = assistsSolo = assistsFlex = totalMatchNormal = totalMatchSolo = totalMatchFlex = 0
    # Creamos los diccionarios vacíos que incluirán las stats por campeones y por partidas
    dicChamps = {}
    dicMatches = {}
    totalGames = len(matches)

    for match in matches:
        queueType = match['info']['queueId']
        info = getMatchPlayerInfo(puuid, match)
        if info is None:
            continue
        if queueType != 400 and queueType != 420 and queueType != 440:
            continue
        kills = info['kills']
        deaths = info['deaths']
        assists = info['assists']
        champName = info['championName']
        dicMatches[match['metadata']['matchId']] = [kills, deaths, assists]

        # Este fragmento de suma se podría eliminar en el futuro, ya que solo se usa para evitar recorrer de nuevo
        # dicMatches sumando cada estadística al total. dicMatches se puede usar para enviar o devolver la info por partida
        totalkills += kills
        totaldeaths += deaths
        totalassists += assists

        if champName in dicChamps:
            dicChamps[champName][0] += kills
            dicChamps[champName][1] += deaths
            dicChamps[champName][2] += assists
            dicChamps[champName][3] += 1
        else:
            dicChamps[champName] = [kills, deaths, assists, 1]
        if queueType == 400:
            # Procesamiento cola Normal
            killsNormal += kills
            deathsNormal += deaths
            assistsNormal += assists
            totalMatchNormal += 1
        elif queueType == 420:
            # Procesamiento cola Ranked Solo/Duo
            killsSolo += kills
            deathsSolo += deaths
            assistsSolo += assists
            totalMatchSolo += 1
        elif queueType == 440:
            # Procesamiento cola Ranked Flex
            killsFlex += kills
            deathsFlex += deaths
            assistsFlex += assists
            totalMatchFlex += 1

    if totalGames != 0:
        print(
            f"El jugador {name} ha jugado {len(dicMatches)} partidas entre Normal, Solo/Duo y Flex, obteniendo los siguientes resultados:")

        print(
            f"KDA total: ({round(totalkills / totalGames, 2)} / {round(totaldeaths / totalGames, 2)} / {round(totaldeaths / totalGames, 2)}): "
            f"{calculateKDA(totalkills, totaldeaths, totalassists)}")
        print(f"\n\nKDA por colas:")
        if totalMatchNormal != 0:
            print(
                f"NormalQueue: ({round(killsNormal / totalMatchNormal, 2)} / {round(deathsNormal / totalMatchNormal, 2)} / {round(assistsNormal / totalMatchNormal, 2)}): "
                f"{calculateKDA(killsNormal, deathsNormal, assistsNormal)}")
        else:
            print(f"No se han obtenido resultados sobre partidas normales")
        if totalMatchSolo != 0:
            print(
                f"Solo/Duo: ({round(killsSolo / totalMatchSolo, 2)} / {round(deathsSolo / totalMatchSolo, 2)} / {round(assistsSolo / totalMatchSolo, 2)}): "
                f"{calculateKDA(killsSolo, deathsSolo, assistsSolo)}")
        else:
            print(f"No se han obtenido resultados sobre partidas solo/duo")
        if totalMatchFlex != 0:
            print(
                f"Flex: ({round(killsNormal / totalMatchFlex, 2)} / {round(deathsNormal / totalMatchFlex, 2)} / {round(assistsNormal / totalMatchFlex, 2)}): "
                f"{calculateKDA(killsFlex, deathsFlex, assistsFlex)}")
        else:
            print(f"No se han obtenido resultados sobre partidas flex")
        print(f"\n\nKDA por campeones jugados:")
        for champ in dict(sorted(dicChamps.items(), key=lambda x: x[1][3], reverse=True)):
            print(
                f"{champ}: ({round(dicChamps[champ][0] / dicChamps[champ][3], 2)} / {round(dicChamps[champ][1] / dicChamps[champ][3], 2)} / {round(dicChamps[champ][2] / dicChamps[champ][3], 2)}): "
                f"{calculateKDA(dicChamps[champ][0], dicChamps[champ][1], dicChamps[champ][2])} en {dicChamps[champ][3]} partidas jugadas")
    else:
        print(
            f"El jugador {name} no ha jugado ninguna partida")


def calculateKDA(kills, deaths, assists):
    if deaths == 0:
        return round(kills + assists, 2)
    else:
        return round((kills + assists) / deaths, 2)


def getPlayerWinrate(name, puuid, matches):
    # El objetivo de esta función es obtener el winrate del jugador basándose en los siguientes criterios:
    # - Winrate total
    # - Winrate por cola
    # - Winrate por posición
    # - Winrate por campeón
    # TODO Si se quiere comprobar el winrate de un campeón o de una posición en una cola concreta, modificar en el futuro la función
    totalVictorias = totalDerrotas = winNormal = loseNormal = winSolo = loseSolo = winFlex = loseFlex = winUnknown = \
        loseUnknown = winTop = loseTop = winJg = loseJg = winMid = loseMid = winAdc = loseAdc = winSupp = loseSupp = 0
    # Creamos un diccionario para los campeones
    dicChamps = {}

    for match in matches:
        queueType = match['info']['queueId']
        info = getMatchPlayerInfo(puuid, match)
        if info is None:
            continue
        win = info['win']
        lane = info['individualPosition']
        champName = info['championName']

        if win:
            totalVictorias += 1
        else:
            totalDerrotas += 1

        if queueType != 400 and queueType != 420 and queueType != 440:
            # Tratamiento otras colas
            if win:
                winUnknown += 1
            else:
                loseUnknown += 1
        else:
            # Winrate por colas separado de otras colas debido a que puede haber conflictos con las posiciones y así ahorramos pasos
            if queueType == 400:
                # Tratamiento Normal
                if win:
                    winNormal += 1
                else:
                    loseNormal += 1
            elif queueType == 420:
                # Tratamiento SoloDuo
                if win:
                    winSolo += 1
                else:
                    loseSolo += 1
            elif queueType == 440:
                # Tratamiento Flex
                if win:
                    winFlex += 1
                else:
                    loseFlex += 1

            # Winrate por posición
            if lane == 'TOP':
                if win:
                    winTop += 1
                else:
                    loseTop += 1
            elif lane == 'JUNGLE':
                if win:
                    winJg += 1
                else:
                    loseJg += 1
            elif lane == 'MIDDLE':
                if win:
                    winMid += 1
                else:
                    loseMid += 1
            elif lane == 'BOTTOM':
                if win:
                    winAdc += 1
                else:
                    loseAdc += 1
            elif lane == 'UTILITY':
                if win:
                    winSupp += 1
                else:
                    loseSupp += 1

        # Winrate por campeón
        if champName in dicChamps:
            if win:
                dicChamps[champName][0] += 1
            else:
                dicChamps[champName][1] += 1
        else:
            if win:
                dicChamps[champName] = [1, 0]
            else:
                dicChamps[champName] = [0, 1]

    # Terminado el bucle de matches
    print(
        f"El jugador {name} ha jugado {winUnknown + winNormal + winSolo + winFlex + loseUnknown + loseNormal + loseSolo + loseFlex} "
        f"partidas, obteniendo los siguientes resultados:")
    print(
        f"Winrate total: {round((winUnknown + winNormal + winSolo + winFlex) / (winUnknown + winNormal + winSolo + winFlex + loseUnknown + loseNormal + loseSolo + loseFlex) * 100, 2)}%")
    print(f"\nWinrate por cola:")
    if winNormal + loseNormal != 0:
        print(
            f"--Winrate NormalQueue: {winNormal} victorias de {winNormal + loseNormal} partidas ({round(winNormal / (winNormal + loseNormal) * 100, 2)}%)")
    else:
        print(f"No ha jugado partidas normales")

    if winSolo + loseSolo != 0:
        print(
            f"--Winrate Solo/Duo: {winSolo} victorias de {winSolo + loseSolo} partidas ({round(winSolo / (winSolo + loseSolo) * 100, 2)}%)")
    else:
        print(f"No ha jugado partidas solo/duo")

    if winFlex + loseFlex != 0:
        print(
            f"--Winrate Flex: {winFlex} victorias de {winFlex + loseFlex} partidas ({round(winFlex / (winFlex + loseFlex) * 100, 2)}%)")
    else:
        print(f"No ha jugado partidas flex")

    if winUnknown + loseUnknown != 0:
        print(
            f"--Winrate otras colas: {winUnknown} victorias de {winUnknown + loseUnknown} partidas ({round(winUnknown / (winUnknown + loseUnknown) * 100, 2)}%)")
    else:
        print(f"No hay datos de partidas en otras colas")

    print(f"\nWinrate por posición:")
    if winTop + loseTop != 0:
        print(
            f"--Winrate Top: {winTop} victorias de {winTop + loseTop} partidas ({round(winTop / (winTop + loseTop) * 100, 2)}%)")
    else:
        print(f"No ha jugado en la posición de Top")

    if winJg + loseJg != 0:
        print(
            f"--Winrate Jungle: {winJg} victorias de {winJg + loseJg} partidas ({round(winJg / (winJg + loseJg) * 100, 2)}%)")
    else:
        print(f"No ha jugado en la posición de Jungla")

    if winMid + loseMid != 0:
        print(
            f"--Winrate Mid: {winMid} victorias de {winMid + loseMid} partidas ({round(winMid / (winMid + loseMid) * 100, 2)}%)")
    else:
        print(f"No ha jugado en la posición de Mid")

    if winAdc + loseAdc != 0:
        print(
            f"--Winrate Adc: {winAdc} victorias de {winAdc + loseAdc} partidas ({round(winAdc / (winAdc + loseAdc) * 100, 2)}%)")
    else:
        print(f"No ha jugado en la posición de Tirador")

    if winSupp + loseSupp != 0:
        print(
            f"--Winrate Supp: {winSupp} victorias de {winSupp + loseSupp} partidas ({round(winSupp / (winSupp + loseSupp) * 100, 2)}%)")
    else:
        print(f"No ha jugado en la posición de Support")

    print(f"\nWinrate por campeón:")
    # Se imprimen los campeones con más partidas jugadas
    for champ, stats in sorted(dicChamps.items(), key=lambda x: sum(x[1]), reverse=True):
        print(
            f"{champ}: {stats[0]} victorias de {stats[0] + stats[1]} partidas ({round(stats[0] / (stats[0] + stats[1]) * 100, 2)}%)")

    return dicChamps


def getMeanDuration(name, puuid, matches):
    # El objetivo de esta función es obtener la duración media de las partidas del jugador. Se puede ampliar a duración
    # media por cola, duración media por campeón y duración media por posición.
    rendiciones = remakes = duracionTotal = countMatches = 0
    for match in matches:
        queueType = match['info']['queueId']
        duracion = match['info']['gameDuration']
        info = getMatchPlayerInfo(puuid, match)
        if info is None or queueType != 400 and queueType != 420 and queueType != 440:
            continue
        remake = info['gameEndedInEarlySurrender']
        ff = info['gameEndedInSurrender']
        if remake:
            remakes += 1
            continue
        elif ff:
            # Usamos como threshold 1500 (25 min) para evitar no contabilizar las partidas que acabaron por rendición
            # pero tuvieron muchos minutos de juego, suficientes como para incluirlos en el cálculo de la media
            if duracion < 1500:
                rendiciones += 1
                continue
        countMatches += 1
        duracionTotal += duracion
    minutos = round((duracionTotal / countMatches) // 60)
    segundos = round((duracionTotal / countMatches) % 60, 2)
    print(f"La duración promedio de las partidas de {name} son de {minutos} minutos y {segundos} segundos")
    print(f"Han ocurrido {remakes} remake(s) y {rendiciones} rendicion(es)")


def getGoldDiffs(name, puuid, matchTimeline):
    # El objetivo de la función es obtener la diferencia de oro promedio que suele sacar el jugador a su rival de posición
    # TODO Función dependiente de tener TIMELINE guardada de la partida concreta
    pass


# FUNCIONES ESTADÍSTICAS DESCRIPTIVAS
def definingChampPool(name, puuid, matches):
    # El objetivo es definir una champion pool de 4 los campeones recomendados como máximo que mejor rendimiento dan al
    # jugador basándonos en diferentes criterios:
    # - Historial de resultados de cada campeón individual
    # - Historial de resultados de un tipo de campeón (fighter, tank, etc.)
    # - Maestría del jugador con los campeones
    dicChamps = getPlayerWinrate(name, puuid, matches)
    # Filtramos usando como threshold 4 partidas jugadas
    poorChamps = []
    for champ, stats in dicChamps.items():
        if sum(dicChamps[champ]) < 4:
            poorChamps.append(champ)
    for champ in poorChamps:
        dicChamps.pop(champ)

    # Apartado de resultados por campeón
    winratesPerChampion = [(champ, stats[0] / sum(stats)) for champ, stats in dicChamps.items()]
    winratesPerChampion = sorted(winratesPerChampion, key=lambda x: x[1], reverse=True)
    dicChampsSorted = {database.getChampionNameById(champ): dicChamps[champ] for champ, _ in winratesPerChampion}
    print(dicChampsSorted)

    # Apartado de resultados por tipo de campeón
    champTags = database.getChampionTags()
    winratesPerTag = {}
    for champ, stats in dicChamps.items():
        tags = champTags.get(champ, [])
        for tag in tags:
            if tag not in winratesPerTag:
                winratesPerTag[tag] = [0, 0]
            winratesPerTag[tag][0] += stats[0]
            winratesPerTag[tag][1] += stats[1]
    print(winratesPerTag)

    # Apartado de maestrías
    champMasteries = database.getSummonerMasteries(puuid)
    if champMasteries is None:
        print("Este jugador no se encuentra en la base de datos")
        api.registerSummoner(puuid)
        champMasteries = database.getSummonerMasteries(puuid)
        if champMasteries is None:
            print("No ha sido posible registrar al jugador")
            exit(-1)
    print(champMasteries)

    # Seleccionar los 4 primeros asumiendo que deben ser 1 champion AD, 1 champion AP y 2 comfort picks
    champRating = assignPointsForPool(dicChampsSorted, winratesPerTag, champMasteries)
    # Los que sí o sí deben entrar a la selección son los tres primeros, independientemente de cualquier otro criterio
    selectedChamps = list(champRating.keys())[:3]
    AD = AP = 0
    # Comprobamos el tipo de daño de los tres añadidos, lo que puede dar lugar a tres casos
    for champion in selectedChamps:
        info = champRating[champion]
        if info[0] == DamageType.Physical:
            AD += 1
        elif info[0] == DamageType.Magical:
            AP += 1
        elif info[0] == DamageType.Hybrid:
            AD += 1
            AP += 1
    # CASO 1: Los tres son tipo mágico
    if AD == 0:
        # Se debe buscar el primer AD o Hybrid que no esté en selectedChamps
        # En caso de que no exista ninguno más, dejar AD a 0
        for champ, info in champRating.items():
            if champ in selectedChamps or info[1] == 0 or info[0] == DamageType.Magical:
                continue
            else:
                selectedChamps.append(champ)
                AD += 1
                break
        pass
    # CASO 2: Los tres son de tipo físico
    elif AP == 0:
        # Se debe buscar el primer AP o Hybrid que no esté en selectedChamps
        # En caso de que no exista ninguno más, dejar AP a 0
        for champ, info in champRating.items():
            if champ in selectedChamps or info[1] == 0 or info[0] == DamageType.Physical:
                continue
            else:
                selectedChamps.append(champ)
                AP += 1
                break
    # CASO 3: Hay al menos un mágico y un físico, o hay un híbrido que se puede usar en ambas categorías, entre los tres seleccionados
    else:
        # En caso de que sí haya al menos uno de cada, añadimos el cuarto
        selectedChamps.append(list(champRating.keys())[3])
    # Además, si no hay un AD o un AP seleccionados (un híbrido vale para cualquiera) entonces añadimos el cuarto
    if AD == 0 or AP == 0:
        selectedChamps.append(list(champRating.keys())[3])

    i = 0
    for selected in selectedChamps:
        i += 1
        print(f"Campeón {i}: {selected}")


def assignPointsForPool(dicChamps, dicTags, champMasteries):
    # Esta función asigna unos puntos en función del historial con el campeón, con el tipo del campeón y las maestrías
    # Rangos de intervalos de los criterios
    champWinrateRange = [0, 0.35, 0.45, 0.55, 0.70]
    tagWinrateRange = [0, 0.35, 0.45, 0.55, 0.70]
    masteryRange = [0, 12000, 25000, 40000, 70000]

    # Puntuación otorgada en cada intervalo
    champWinratePoints = [0, 5, 10, 20, 30]
    tagWinratePoints = [0, 3, 6, 9, 12]
    masteryPoints = [0, 2, 4, 6, 7]

    # Se crean dos diccionarios:
    # Uno con la estructura: {champName: [tags]}
    # Otro con la siguiente estructura: {champName: [damageType, points]}
    champTags = database.getChampionTags()
    champRating = {
        'Aatrox': [DamageType.Physical, 0],
        'Ahri': [DamageType.Magical, 0],
        'Akali': [DamageType.Magical, 0],
        'Akshan': [DamageType.Physical, 0],
        'Alistar': [DamageType.Magical, 0],
        'Amumu': [DamageType.Magical, 0],
        'Anivia': [DamageType.Magical, 0],
        'Annie': [DamageType.Magical, 0],
        'Aphelios': [DamageType.Physical, 0],
        'Ashe': [DamageType.Physical, 0],
        'Aurelion Sol': [DamageType.Magical, 0],
        'Azir': [DamageType.Magical, 0],
        'Bard': [DamageType.Magical, 0],
        'Bel\'Veth': [DamageType.Physical, 0],
        'Blitzcrank': [DamageType.Magical, 0],
        'Brand': [DamageType.Magical, 0],
        'Braum': [DamageType.Magical, 0],
        'Briar': [DamageType.Physical, 0],
        'Caitlyn': [DamageType.Physical, 0],
        'Camille': [DamageType.Physical, 0],
        'Cassiopeia': [DamageType.Magical, 0],
        'Cho\'Gath': [DamageType.Magical, 0],
        'Corki': [DamageType.Magical, 0],
        'Darius': [DamageType.Physical, 0],
        'Diana': [DamageType.Magical, 0],
        'Dr. Mundo': [DamageType.Magical, 0],
        'Draven': [DamageType.Physical, 0],
        'Ekko': [DamageType.Magical, 0],
        'Elise': [DamageType.Magical, 0],
        'Evelynn': [DamageType.Magical, 0],
        'Ezreal': [DamageType.Physical, 0],
        'Fiddlesticks': [DamageType.Magical, 0],
        'Fiora': [DamageType.Physical, 0],
        'Fizz': [DamageType.Magical, 0],
        'Galio': [DamageType.Magical, 0],
        'Gangplank': [DamageType.Physical, 0],
        'Garen': [DamageType.Physical, 0],
        'Gnar': [DamageType.Physical, 0],
        'Gragas': [DamageType.Magical, 0],
        'Graves': [DamageType.Physical, 0],
        'Gwen': [DamageType.Magical, 0],
        'Hecarim': [DamageType.Magical, 0],
        'Heimerdinger': [DamageType.Magical, 0],
        'Hwei': [DamageType.Magical, 0],
        'Illaoi': [DamageType.Physical, 0],
        'Irelia': [DamageType.Physical, 0],
        'Ivern': [DamageType.Magical, 0],
        'Janna': [DamageType.Magical, 0],
        'Jarvan IV': [DamageType.Physical, 0],
        'Jax': [DamageType.Physical, 0],
        'Jayce': [DamageType.Physical, 0],
        'Jhin': [DamageType.Physical, 0],
        'Jinx': [DamageType.Physical, 0],
        'K\'Sante': [DamageType.Physical, 0],
        'Kai\'Sa': [DamageType.Hybrid, 0],
        'Kalista': [DamageType.Physical, 0],
        'Karma': [DamageType.Magical, 0],
        'Karthus': [DamageType.Magical, 0],
        'Kassadin': [DamageType.Magical, 0],
        'Katarina': [DamageType.Magical, 0],
        'Kayle': [DamageType.Hybrid, 0],
        'Kayn': [DamageType.Physical, 0],
        'Kennen': [DamageType.Magical, 0],
        'Kha\'Zix': [DamageType.Physical, 0],
        'Kindred': [DamageType.Physical, 0],
        'Kled': [DamageType.Physical, 0],
        'Kog\'Maw': [DamageType.Hybrid, 0],
        'LeBlanc': [DamageType.Magical, 0],
        'Lee Sin': [DamageType.Physical, 0],
        'Leona': [DamageType.Magical, 0],
        'Lillia': [DamageType.Magical, 0],
        'Lissandra': [DamageType.Magical, 0],
        'Lucian': [DamageType.Physical, 0],
        'Lulu': [DamageType.Magical, 0],
        'Lux': [DamageType.Magical, 0],
        'Master Yi': [DamageType.Physical, 0],
        'Malphite': [DamageType.Magical, 0],
        'Malzahar': [DamageType.Magical, 0],
        'Maokai': [DamageType.Magical, 0],
        'Milio': [DamageType.Magical, 0],
        'Miss Fortune': [DamageType.Physical, 0],
        'Mordekaiser': [DamageType.Magical, 0],
        'Morgana': [DamageType.Magical, 0],
        'Naafiri': [DamageType.Physical, 0],
        'Nami': [DamageType.Magical, 0],
        'Nasus': [DamageType.Physical, 0],
        'Nautilus': [DamageType.Magical, 0],
        'Neeko': [DamageType.Magical, 0],
        'Nidalee': [DamageType.Magical, 0],
        'Nilah': [DamageType.Physical, 0],
        'Nocturne': [DamageType.Physical, 0],
        'Nunu & Willump': [DamageType.Magical, 0],
        'Olaf': [DamageType.Physical, 0],
        'Orianna': [DamageType.Magical, 0],
        'Ornn': [DamageType.Hybrid, 0],
        'Pantheon': [DamageType.Physical, 0],
        'Poppy': [DamageType.Physical, 0],
        'Pyke': [DamageType.Physical, 0],
        'Qiyana': [DamageType.Physical, 0],
        'Quinn': [DamageType.Physical, 0],
        'Rakan': [DamageType.Magical, 0],
        'Rammus': [DamageType.Magical, 0],
        'Rek\'Sai': [DamageType.Physical, 0],
        'Rell': [DamageType.Magical, 0],
        'Renata Glasc': [DamageType.Magical, 0],
        'Renekton': [DamageType.Physical, 0],
        'Rengar': [DamageType.Physical, 0],
        'Riven': [DamageType.Physical, 0],
        'Rumble': [DamageType.Magical, 0],
        'Ryze': [DamageType.Magical, 0],
        'Samira': [DamageType.Physical, 0],
        'Sejuani': [DamageType.Hybrid, 0],
        'Senna': [DamageType.Physical, 0],
        'Seraphine': [DamageType.Magical, 0],
        'Sett': [DamageType.Physical, 0],
        'Shaco': [DamageType.Hybrid, 0],
        'Shen': [DamageType.Hybrid, 0],
        'Shyvana': [DamageType.Magical, 0],
        'Singed': [DamageType.Magical, 0],
        'Sion': [DamageType.Physical, 0],
        'Sivir': [DamageType.Physical, 0],
        'Skarner': [DamageType.Physical, 0],
        'Smolder': [DamageType.Hybrid, 0],
        'Sona': [DamageType.Magical, 0],
        'Soraka': [DamageType.Magical, 0],
        'Swain': [DamageType.Magical, 0],
        'Sylas': [DamageType.Magical, 0],
        'Syndra': [DamageType.Magical, 0],
        'Tahm Kench': [DamageType.Magical, 0],
        'Taliyah': [DamageType.Magical, 0],
        'Talon': [DamageType.Physical, 0],
        'Taric': [DamageType.Magical, 0],
        'Teemo': [DamageType.Magical, 0],
        'Thresh': [DamageType.Magical, 0],
        'Tristana': [DamageType.Physical, 0],
        'Trundle': [DamageType.Physical, 0],
        'Tryndamere': [DamageType.Physical, 0],
        'Twisted Fate': [DamageType.Magical, 0],
        'Twitch': [DamageType.Physical, 0],
        'Udyr': [DamageType.Hybrid, 0],
        'Urgot': [DamageType.Physical, 0],
        'Varus': [DamageType.Physical, 0],
        'Vayne': [DamageType.Physical, 0],
        'Veigar': [DamageType.Magical, 0],
        'Vel\'Koz': [DamageType.Magical, 0],
        'Vex': [DamageType.Magical, 0],
        'Vi': [DamageType.Physical, 0],
        'Viego': [DamageType.Physical, 0],
        'Viktor': [DamageType.Magical, 0],
        'Vladimir': [DamageType.Magical, 0],
        'Volibear': [DamageType.Hybrid, 0],
        'Warwick': [DamageType.Hybrid, 0],
        'Wukong': [DamageType.Physical, 0],
        'Xayah': [DamageType.Physical, 0],
        'Xerath': [DamageType.Magical, 0],
        'Xin Zhao': [DamageType.Physical, 0],
        'Yasuo': [DamageType.Physical, 0],
        'Yone': [DamageType.Physical, 0],
        'Yorick': [DamageType.Hybrid, 0],
        'Yuumi': [DamageType.Magical, 0],
        'Zac': [DamageType.Magical, 0],
        'Zed': [DamageType.Physical, 0],
        'Zeri': [DamageType.Hybrid, 0],
        'Ziggs': [DamageType.Magical, 0],
        'Zilean': [DamageType.Magical, 0],
        'Zoe': [DamageType.Magical, 0],
        'Zyra': [DamageType.Magical, 0]
    }

    for champ in champMasteries:
        champName = database.getChampionByKey(champ['championId'])
        champRating[champName][1] += getPointsGivenRange(champ['championPoints'], masteryRange, masteryPoints)

    for champ, stats in dicChamps.items():
        winrate = (stats[0]/(stats[0] + stats[1]))
        champRating[champ][1] += getPointsGivenRange(winrate, champWinrateRange, champWinratePoints)

        tags = champTags.get(champ)
        totalTagPoints = 0
        for tag in tags:
            tagWinrate = (dicTags.get(tag)[0]/(dicTags.get(tag)[0] + dicTags.get(tag)[1]))
            totalTagPoints += getPointsGivenRange(tagWinrate, tagWinrateRange, tagWinratePoints)
        champRating[champ][1] += int(totalTagPoints/len(tags))

        if stats[0]+stats[1] < 10:
            champRating[champ][1] = int(champRating[champ][1] * 0.85)
        elif stats[0]+stats[1] > 35:
            champRating[champ][1] = int(champRating[champ][1] * 1.15)

    # Una vez acabado el bucle, se debería ordenar el diccionario sobre el total de puntos
    champRatingSorted = dict(sorted(champRating.items(), key=lambda x: x[1][1], reverse=True))
    for champ, stats in champRatingSorted.items():
        print(f'{champ}: {stats[1]}')
    return champRatingSorted


def getPointsGivenRange(x, rangeArray, pointsArray):
    # if x > rangeArray[len(rangeArray)-1]:
    #     return pointsArray[len(pointsArray) - 1]
    for i in range(len(rangeArray)-1, -1, -1):
        if rangeArray[i] <= x:
            return pointsArray[i]


def getResultsWithPartner(puuid, matches):
    # Estructura de dicPartners = {puuid: nombre, victorias, derrotas}
    dicPartners = {}
    for match in matches:
        gameInfo = getMatchPlayerInfo(puuid, match)
        teamID = gameInfo['teamId']
        win = gameInfo['win']
        for participant in match['info']['participants']:
            summonerPUUID = participant['puuid']
            if participant['teamId'] != teamID or summonerPUUID == puuid:
                continue
            else:
                if summonerPUUID in dicPartners:
                    if win:
                        dicPartners[summonerPUUID][1] += 1
                    else:
                        dicPartners[summonerPUUID][2] += 1
                else:
                    if win:
                        dicPartners[summonerPUUID] = [participant['summonerName'], 1, 0]
                    else:
                        dicPartners[summonerPUUID] = [participant['summonerName'], 0, 1]

    nonPartners = []
    for puuid, partner in dicPartners.items():
        if partner[1] + partner[2] < 2:
            nonPartners.append(puuid)
    for stranger in nonPartners:
        dicPartners.pop(stranger)
    print(dicPartners)


def getWinrateAgainstChampions():
    pass


def getWinrateAlongChampions():
    pass
# FUNCIONES GRÁFICAS TEMPORALES


# FUNCIONES ANÁLISIS CAMPEONES


# FUNCIONES ANÁLISIS ITEMIZACIÓN


### OPCIONAL ###
# FUNCIONES PARA MOSTRAR HEATMAPS
# FUNCIONES MACHINE LEARNING
# FUNCIONES DE ANÁLISIS POR SEGMENTACIÓN
