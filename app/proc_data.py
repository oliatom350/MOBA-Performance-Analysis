import re
import time
from enum import Enum
from io import BytesIO

import pandas as pd
import seaborn as sns
from matplotlib import image as mpimg

import api
import database

import matplotlib
import matplotlib.pyplot as plt
# Para el correcto funcionamiento de matplotlib en un servicio web, se utiliza el backend "Agg", que es un backend no
# interactivo diseñado para generar imágenes sin necesidad de una interfaz gráfica de usuario
matplotlib.use('Agg')


class DamageType(Enum):
    Physical = 1
    Magical = 2
    Hybrid = 3


def processPlayer(name, riotId):
    puuid = api.getSummonerPUUID(name, riotId)
    # matches = getAllPlayerMatches(name, puuid)
    matches = database.getNPlayersGames(puuid, 7)
    if matches:
        # getMatchesPosition(name, puuid, matches)

        # getPlayerKDA(name, puuid, matches)

        # getPlayerWinrate(name, puuid, matches)

        # definingChampPool(name, puuid, matches)
        # definingChampPool2(name, puuid, matches)

        # getResultsWithPartner(puuid, matches)

        # getWinrateAgainstChampions(puuid, matches)

        # getWinrateAlongsideChampions(puuid, matches)

        getQuickPlayerInfo(name, puuid, matches)

        # drawKillsHeatmaps(puuid, matches)


def getReferenceData(position):
    challengers = database.getChallengerPlayers()
    print(challengers)
    dicData = getGivenProPlayersHistoryByPosition(challengers, position)
    if dicData is None:
        dicData = getUnknownProPlayersHistoryByPosition(position)
    return dicData


def updatePlayerGames(name, puuid, count):
    if database.checkPlayerDB(puuid):
        limitDate = database.getLastGame(puuid)
    else:
        api.registerSummonerByPUUID(puuid)
        limitDate = 0
    endTime = round(time.time())
    matches = {}
    while True:
        matchesIDs = api.getNormalAndRankedIDs(puuid, limitDate, endTime, count)
        if len(matchesIDs) == 0 or endTime < limitDate:
            break
        matchesRepeated = []
        for matchID in matchesIDs:
            if database.checkGameDB(matchID) or database.checkGameBlacklist(matchID):
                matchesRepeated.append(matchID)
                continue
            matchInfo = api.getMatchInfo(matchID)
            if matchInfo is None:
                matchesRepeated.append(matchID)
                continue
            else:
                database.storeGameDB(matchInfo)
                matches[matchID] = matchInfo
            try:
                endTime = int(str(matchInfo['info']['gameCreation'])[:-3])
            except ValueError as e:
                print(e)
                continue
        if len(matchesRepeated) == len(matchesIDs):
            break
    print(f'Se han actualizado {len(matches)} partidas de {name}')
    return matches


def getAllPlayerMatches(name, puuid):
    matches = database.getAllPlayersGames(puuid)
    if 0 < len(matches) <= 100:
        matches2 = updatePlayerGames(name, puuid, 100 - len(matches))
    else:
        matches2 = updatePlayerGames(name, puuid, 100)
    for matchID, matchInfo in matches2:
        if matchID in matches.keys():
            continue
        matches[matchID] = matchInfo
    # Una vez llegados a este punto, deberían haberse recuperado un número mínimo de 100 partidas totales.
    # En el caso de que no sean suficientes, se mostrará un mensaje de que no hay suficientes datos para analizar al jugador
    print(f'Se han recuperado {len(matches)} partidas de {name}')
    sortedMatches = dict(sorted(matches.items(), key=lambda x: x[0], reverse=True))
    return sortedMatches


def getMatchesPosition(name, puuid, matches):
    print(f'FUNCIÓN DE PARTIDAS POR POSICIÓN')
    topNorm = jungleNorm = midNorm = adcNorm = suppNorm = topSolo = jungleSolo = midSolo = adcSolo = suppSolo = topFlex \
        = jungleFlex = midFlex = adcFlex = suppFlex = unknown = totalNorm = totalSolo = totalFlex = unknownQueue = 0
    for match in matches.values():
        queueType = match['info']['queueId']
        info = getMatchPlayerInfo(puuid, match)
        if info is None:
            continue
        lane = getPlayerPosition(info)
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
    dicPos = {
        'TOP': {'Normal': topNorm, 'SoloDuo': topSolo, 'Flex': topFlex, 'Total': (topNorm + topSolo + topFlex)},
        'JUNGLE': {'Normal': jungleNorm, 'SoloDuo': jungleSolo, 'Flex': jungleFlex,
                   'Total': (jungleNorm + jungleSolo + jungleFlex)},
        'MIDDLE': {'Normal': midNorm, 'SoloDuo': midSolo, 'Flex': midFlex, 'Total': (midNorm + midSolo + midFlex)},
        'BOTTOM': {'Normal': adcNorm, 'SoloDuo': adcSolo, 'Flex': adcFlex, 'Total': (adcNorm + adcSolo + adcFlex)},
        'UTILITY': {'Normal': suppNorm, 'SoloDuo': suppSolo, 'Flex': suppFlex,
                    'Total': (suppNorm + suppSolo + suppFlex)}
    }

    return dicPos


def plot_positions(dicPos, name):
    positions = ['TOP', 'JUNGLE', 'MIDDLE', 'BOTTOM', 'UTILITY']
    positionsBar = ['Top', 'Jungle', 'Mid', 'Bottom', 'Support']
    totals = [dicPos[pos]['Total'] for pos in positions]

    plt.figure(figsize=(10, 6))
    plt.bar(positionsBar, totals, color=['blue', 'green', 'red', 'purple', 'orange'])
    plt.xlabel('Positions')
    plt.ylabel('Number of games')
    plt.title('Games per position')

    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    return buffer


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
    print(f'FUNCIÓN DE KDA')
    totaldeaths = totalkills = totalassists = deathsNormal = deathsSolo = deathsFlex = killsNormal = killsSolo = \
        killsFlex = assistsNormal = assistsSolo = assistsFlex = totalMatchNormal = totalMatchSolo = totalMatchFlex = 0
    # Creamos los diccionarios vacíos que incluirán las stats por campeones y por partidas
    dicChamps = {}
    dicMatches = {}
    totalGames = len(matches)

    for match in matches.values():
        queueType = match['info']['queueId']
        info = getMatchPlayerInfo(puuid, match)
        if info is None:
            continue
        if queueType != 400 and queueType != 420 and queueType != 440:
            continue
        kills = info['kills']
        deaths = info['deaths']
        assists = info['assists']
        champName = database.getChampionByKey(info['championId'])
        if match['metadata']['matchId'] not in dicMatches:
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

    dicKDA = {}
    if totalGames != 0:
        print(
            f"El jugador {name} ha jugado {len(dicMatches)} partidas entre Normal, Solo/Duo y Flex, obteniendo los siguientes resultados:")
        dicKDA['totalGames'] = len(dicMatches)

        print(
            f"KDA total: ({round(totalkills / totalGames, 2)} / {round(totaldeaths / totalGames, 2)} / {round(totaldeaths / totalGames, 2)}): "
            f"{calculateKDA(totalkills, totaldeaths, totalassists)}")
        print(f"\n\nKDA por colas:")
        dicKDA['kdaTotal'] = {
            'kills': round(totalkills / totalGames, 2),
            'deaths': round(totaldeaths / totalGames, 2),
            'assists': round(totaldeaths / totalGames, 2),
            'kda': calculateKDA(totalkills, totaldeaths, totalassists)
        }
        dicKDA['kdaNormal'] = {}
        dicKDA['kdaSolo'] = {}
        dicKDA['kdaFlex'] = {}
        if totalMatchNormal != 0:
            print(
                f"NormalQueue: ({round(killsNormal / totalMatchNormal, 2)} / {round(deathsNormal / totalMatchNormal, 2)} / {round(assistsNormal / totalMatchNormal, 2)}): "
                f"{calculateKDA(killsNormal, deathsNormal, assistsNormal)}")
            dicKDA['kdaNormal'] = {
                'kills': round(killsNormal / totalMatchNormal, 2),
                'deaths': round(deathsNormal / totalMatchNormal, 2),
                'assists': round(assistsNormal / totalMatchNormal, 2),
                'kda': calculateKDA(killsNormal, deathsNormal, assistsNormal)
            }
        else:
            print(f"No se han obtenido resultados sobre partidas normales")
        if totalMatchSolo != 0:
            print(
                f"Solo/Duo: ({round(killsSolo / totalMatchSolo, 2)} / {round(deathsSolo / totalMatchSolo, 2)} / {round(assistsSolo / totalMatchSolo, 2)}): "
                f"{calculateKDA(killsSolo, deathsSolo, assistsSolo)}")
            dicKDA['kdaSolo'] = {
                'kills': round(killsSolo / totalMatchSolo, 2),
                'deaths': round(deathsSolo / totalMatchSolo, 2),
                'assists': round(assistsSolo / totalMatchSolo, 2),
                'kda': calculateKDA(killsSolo, deathsSolo, assistsSolo)
            }
        else:
            print(f"No se han obtenido resultados sobre partidas solo/duo")
        if totalMatchFlex != 0:
            print(
                f"Flex: ({round(killsFlex / totalMatchFlex, 2)} / {round(deathsFlex / totalMatchFlex, 2)} / {round(deathsFlex / totalMatchFlex, 2)}): "
                f"{calculateKDA(killsFlex, deathsFlex, deathsFlex)}")
            dicKDA['kdaFlex'] = {
                'kills': round(killsFlex / totalMatchFlex, 2),
                'deaths': round(deathsFlex / totalMatchFlex, 2),
                'assists': round(deathsFlex / totalMatchFlex, 2),
                'kda': calculateKDA(killsFlex, deathsFlex, assistsFlex)
            }
        else:
            print(f"No se han obtenido resultados sobre partidas flex")
        print(f"\n\nKDA por campeones jugados:")
        dicKDA['kdaChamps'] = {}
        for champ in dict(sorted(dicChamps.items(), key=lambda x: x[1][3], reverse=True)):
            print(
                f"{champ}: ({round(dicChamps[champ][0] / dicChamps[champ][3], 2)} / {round(dicChamps[champ][1] / dicChamps[champ][3], 2)} / {round(dicChamps[champ][2] / dicChamps[champ][3], 2)}): "
                f"{calculateKDA(dicChamps[champ][0], dicChamps[champ][1], dicChamps[champ][2])} en {dicChamps[champ][3]} partidas jugadas")
            dicKDA['kdaChamps'][champ] = {
                'champId': database.getChampionIdByName(champ),
                'kills': round(dicChamps[champ][0] / dicChamps[champ][3], 2),
                'deaths': round(dicChamps[champ][1] / dicChamps[champ][3], 2),
                'assists': round(dicChamps[champ][2] / dicChamps[champ][3], 2),
                'games': dicChamps[champ][3],
                'kda': calculateKDA(dicChamps[champ][0], dicChamps[champ][1], dicChamps[champ][2])
            }
    else:
        print(
            f"El jugador {name} no ha jugado ninguna partida")
    return dicKDA


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
    print(f'FUNCIÓN DE WINRATE')
    totalVictorias = totalDerrotas = winNormal = loseNormal = winSolo = loseSolo = winFlex = loseFlex = winUnknown = \
        loseUnknown = winTop = loseTop = winJg = loseJg = winMid = loseMid = winAdc = loseAdc = winSupp = loseSupp = 0
    # Creamos un diccionario para los campeones
    dicChamps = {}

    for match in matches.values():
        queueType = match['info']['queueId']
        info = getMatchPlayerInfo(puuid, match)
        if info is None:
            continue
        win = info['win']
        lane = getPlayerPosition(info)
        champName = database.getChampionByKey(info['championId'])

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

    finalDic = {}
    print(f"\nWinrate por campeón:")
    # Se imprimen los campeones con más partidas jugadas
    for champ, stats in sorted(dicChamps.items(), key=lambda x: sum(x[1]), reverse=True):
        print(
            f"{champ}: {stats[0]} victorias de {stats[0] + stats[1]} partidas ({round(stats[0] / (stats[0] + stats[1]) * 100, 2)}%)")
        finalDic[champ] = {
            "champId": database.getChampionIdByName(champ),
            "wins": stats[0],
            "loses": stats[1],
            "games": stats[0] + stats[1],
            "winrate": round(round(stats[0] / (stats[0] + stats[1]), 2) * 100)
        }

    return finalDic


def getMeanDuration(name, puuid, matches):
    # El objetivo de esta función es obtener la duración media de las partidas del jugador. Se puede ampliar a duración
    # media por cola, duración media por campeón y duración media por posición.
    print(f'FUNCIÓN DE DURACIÓN MEDIA DE PARTIDAS')
    rendiciones = remakes = duracionTotal = countMatches = 0
    for match in matches.values():
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
    segundos = round((duracionTotal / countMatches) % 60)
    print(f"La duración promedio de las partidas de {name} son de {minutos} minutos y {segundos} segundos")
    print(f"Han ocurrido {remakes} remake(s) y {rendiciones} rendicion(es)")
    return {'minutes': minutos, 'seconds': segundos}


def getGoldDiffs(name, puuid, matchTimeline):
    # El objetivo de la función es obtener la diferencia de oro promedio que suele sacar el jugador a su rival de posición
    # TODO Función dependiente de tener TIMELINE guardada de la partida concreta
    pass


def definingChampPool2(name, puuid, matches):
    # TODO Posible mejora: Obtener los campeones clasificados en base a la posición
    # El objetivo es definir una champion pool de 3 los campeones recomendados como máximo que mejor rendimiento dan al
    # jugador basándonos en diferentes criterios:
    # - Historial de resultados de cada campeón individual
    # - Historial de resultados de un tipo de campeón (fighter, tank, etc.)
    # - Maestría del jugador con los campeones
    dicChamps = getPlayerWinrate(name, puuid, matches)
    # Filtramos usando como threshold 4 partidas jugadas
    poorChamps = []
    for champ, stats in dicChamps.items():
        if stats["games"] < 4:
            poorChamps.append(champ)
    for champ in poorChamps:
        dicChamps.pop(champ)

    # Apartado de resultados por campeón
    winratesPerChampion = [(champ, stats["wins"] / stats["games"]) for champ, stats in dicChamps.items()]
    winratesPerChampion = sorted(winratesPerChampion, key=lambda x: x[1], reverse=True)
    dicChampsSorted = {champ: dicChamps[champ] for champ, _ in winratesPerChampion}

    # Apartado de resultados por tipo de campeón
    champTags = database.getChampionTags()
    winratesPerTag = {}
    for champ, stats in dicChamps.items():
        tags = champTags.get(champ, [])
        for tag in tags:
            if tag not in winratesPerTag:
                winratesPerTag[tag] = [0, 0]
            winratesPerTag[tag][0] += stats["wins"]
            winratesPerTag[tag][1] += stats["loses"]

    # Apartado de maestrías
    champMasteries = database.getSummonerMasteries(puuid)
    if champMasteries is None:
        print("Este jugador no se encuentra en la base de datos")
        api.registerSummonerByPUUID(puuid)
        champMasteries = database.getSummonerMasteries(puuid)
        if champMasteries is None:
            print("No ha sido posible registrar al jugador")
            exit(-1)

    # Seleccionar los 5 primeros asumiendo que deben ser 2 champion AD, 2 champion AP y 1 comfort pick
    champRating = assignPointsForPool(dicChampsSorted, winratesPerTag, champMasteries)

    # Clasificamos los campeones evaluados por su tipo de daño
    # TODO Eliminar info de los values, y pasar únicamente la puntuación
    ADChamps = {}
    APChamps = {}
    HybridChamps = {}
    for champion, info in champRating.items():
        damageType = info[0]
        info[0] = damageType.name
        print(info)
        if damageType == DamageType.Physical:
            ADChamps[champion] = info
        elif damageType == DamageType.Magical:
            APChamps[champion] = info
        elif damageType == DamageType.Hybrid:
            HybridChamps[champion] = info

    # Seleccionar los dos campeones físicos y los dos campeones mágicos con mayor puntuación
    selectedADChamps = dict(sorted(ADChamps.items(), key=lambda x: x[1], reverse=True)[:2])
    selectedAPChamps = dict(sorted(APChamps.items(), key=lambda x: x[1], reverse=True)[:2])
    selectedChamps = {}
    selectedChamps.update(selectedADChamps)
    selectedChamps.update(selectedAPChamps)
    selectedChampsReversed = dict(sorted(selectedChamps.items(), key=lambda x: x[1][1]))

    # Se itera sobre los campeones híbridos y se sustituye en cualquier conjunto el campeón con menor puntaje, parando
    # la iteración si los 4 campeones seleccionados poseen mejor puntuación que el siguiente híbrido
    changed = False
    for champ, info in HybridChamps.items():
        for selectedChamp, selectedInfo in selectedChampsReversed.items():
            if info[1] > selectedInfo[1]:
                selectedChamps.pop(selectedChamp)
                selectedChamps[champ] = info
                changed = True
                break
        if changed:
            break

    # Falta introducir el quinto y último campeón
    comfortChamp = ''
    for champ, info in champRating.items():
        if champ not in selectedChamps.keys():
            selectedChamps[champ] = info
            comfortChamp = champ
            break
    finalChamps = {'AD': {}, 'AP': {}, 'Comfort': {}}
    # Imprimir los campeones seleccionados
    for champ, champInfo in selectedChamps.items():
        if champInfo[0] == 'Physical':
            finalChamps['AD'][champ] = {'champId': database.getChampionIdByName(champ)}
        elif champInfo[0] == 'Magical':
            finalChamps['AP'][champ] = {'champId': database.getChampionIdByName(champ)}
    finalAD = len(finalChamps['AD'].keys())
    finalAP = len(finalChamps['AP'].keys())
    if finalAD < 2:
        for champ, champInfo in selectedChamps.items():
            if champInfo[0] == 'Hybrid':
                finalChamps['AD'][champ] = {'champId': database.getChampionIdByName(champ)}
                if finalAD >= 2:
                    break
    if finalAP < 2:
        for champ, champInfo in selectedChamps.items():
            if champInfo[0] == 'Hybrid':
                finalChamps['AP'][champ] = {'champId': database.getChampionIdByName(champ)}
                if finalAP >= 2:
                    break
    if comfortChamp in finalChamps['AD']:
        finalChamps['AD'].pop(comfortChamp)
        finalChamps['Comfort'][comfortChamp] = {'champId': database.getChampionIdByName(comfortChamp)}
    elif comfortChamp in finalChamps['AP']:
        finalChamps['AP'].pop(comfortChamp)
        finalChamps['Comfort'][comfortChamp] = {'champId': database.getChampionIdByName(comfortChamp)}
    # for i, selected in enumerate(selectedChamps.keys()):
    #     if i < 2:
    #         print(f"Campeón AD {i%2 + 1}: {selected}")
    #         finalChamps['AD'][selected] = {'champId': database.getChampionIdByName(selected)}
    #     elif i < 4:
    #         print(f"Campeón AP {i%2 + 1}: {selected}")
    #         finalChamps['AP'][selected] = {'champId': database.getChampionIdByName(selected)}
    #     else:
    #         print(f"Campeón comfort: {selected}")
    #         finalChamps['Comfort'][selected] = {'champId': database.getChampionIdByName(selected)}
    return finalChamps


# FUNCIONES ESTADÍSTICAS DESCRIPTIVAS
def definingChampPool(name, puuid, matches):
    # TODO Posible mejora: Obtener los campeones clasificados en base a la posición
    # El objetivo es definir una champion pool de 3 los campeones recomendados como máximo que mejor rendimiento dan al
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
    dicChampsSorted = {champ: dicChamps[champ] for champ, _ in winratesPerChampion}
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
        api.registerSummonerByPUUID(puuid)
        champMasteries = database.getSummonerMasteries(puuid)
        if champMasteries is None:
            print("No ha sido posible registrar al jugador")
            exit(-1)
    print(champMasteries)

    # Seleccionar los 5 primeros asumiendo que deben ser 2 champion AD, 2 champion AP y 1 comfort pick
    champRating = assignPointsForPool(dicChampsSorted, winratesPerTag, champMasteries)
    # Los que sí o sí deben entrar a la selección son los tres primeros, independientemente de cualquier otro criterio
    selectedChamps = list(champRating.keys())[:2]
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
    # CASO 1: Los dos son de tipo mágico
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
    # CASO 2: Los dos son de tipo físico
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
    # CASO 3: Hay un mágico y un físico, o hay al menos un híbrido que se puede usar en ambas categorías, entre los dos seleccionados
    else:
        # En caso de que sí haya al menos uno de cada, añadimos el tercero
        selectedChamps.append(list(champRating.keys())[2])
    # Además, si no hay un AD o un AP seleccionados (un híbrido vale para cualquiera) entonces añadimos el tercero
    if AD == 0 or AP == 0:
        selectedChamps.append(list(champRating.keys())[2])

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
        winrate = stats["winrate"] / 100
        champRating[champ][1] += getPointsGivenRange(winrate, champWinrateRange, champWinratePoints)

        tags = champTags.get(champ)
        totalTagPoints = 0
        for tag in tags:
            tagWinrate = (dicTags.get(tag)[0] / (dicTags.get(tag)[0] + dicTags.get(tag)[1]))
            totalTagPoints += getPointsGivenRange(tagWinrate, tagWinrateRange, tagWinratePoints)
        champRating[champ][1] += int(totalTagPoints / len(tags))

        if stats["games"] < 10:
            champRating[champ][1] = int(champRating[champ][1] * 0.85)
        elif stats["games"] > 35:
            champRating[champ][1] = int(champRating[champ][1] * 1.15)

    # Una vez acabado el bucle, se debería ordenar el diccionario sobre el total de puntos
    champRatingSorted = dict(sorted(champRating.items(), key=lambda x: x[1][1], reverse=True))
    for champ, stats in champRatingSorted.items():
        print(f'{champ}: {stats[1]}')
    return champRatingSorted


def getPointsGivenRange(x, rangeArray, pointsArray):
    # if x > rangeArray[len(rangeArray)-1]:
    #     return pointsArray[len(pointsArray) - 1]
    for i in range(len(rangeArray) - 1, -1, -1):
        if rangeArray[i] <= x:
            return pointsArray[i]
    return pointsArray[0]


def getResultsWithPartner(puuid, matches):
    # Estructura de dicPartners = {puuid: nombre, victorias, derrotas}
    dicPartners = {}
    for match in matches.values():
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

    nonPartners = [puuid for puuid, partner in dicPartners.items() if partner[1] + partner[2] < 3]
    for stranger in nonPartners:
        dicPartners.pop(stranger)
    finalPartners = {}
    for companionPUUID, companion in dicPartners.items():
        iconAndLevel = database.getSummonerIconAndLevel(companionPUUID)
        if iconAndLevel is None:
            api.registerSummonerByPUUID(companionPUUID)
            iconAndLevel = database.getSummonerIconAndLevel(companionPUUID)
        print(
            f'{companion[0]}: {companion[1]} victorias y {companion[2]} derrotas, haciendo un winrate de {round((companion[1] / (companion[1] + companion[2])) * 100, 2)}%')
        finalPartners[companion[0]] = {'games': companion[1] + companion[2], 'wins': companion[1],
                                       'loses': companion[2],
                                       'winrate': round((companion[1] / (companion[1] + companion[2])) * 100, 2),
                                       'icon': iconAndLevel['profileIconId']}
    return finalPartners


def getWinrateAgainstChampions(puuid, matches):
    # El objetivo de esta función es obtener el winrate del jugador contra una serie de campeones concretos.
    # Esto también se puede interpretar como el winrate de cada campeón contra el jugador
    # Creamos cinco diccionarios para los campeones, uno por cada posición
    # La estructura seguida debe ser:
    # {champName: {"champUsed": {"wins": x, "loses": x}, ...}}
    # Es decir, cada campeón almacena un diccionario de los resultados concretos del jugador contra él (campeón usado, victorias del campeón usado y derrotas del campeón usado)
    vsChampsTop = {}
    vsChampsJgl = {}
    vsChampsMid = {}
    vsChampsAdc = {}
    vsChampsSup = {}

    totalCounted = 0
    remakes = 0
    # Recorremos las partidas del diccionario obteniendo la información del jugador en cada una
    for match in matches.values():
        ownInfo = getMatchPlayerInfo(puuid, match)
        if ownInfo is None:
            continue
        if ownInfo['gameEndedInEarlySurrender']:
            remakes += 1
            continue
        # Únicamente nos interesa obtener si el jugador ganó, en qué posición jugó y qué campeón usó
        win = ownInfo['win']
        lane = getPlayerPosition(ownInfo)
        ownChamp = database.getChampionByKey(ownInfo['championId'])
        if ownChamp is None:
            continue

        rivalChamp = None
        # Recorremos los participantes buscando a su rival de línea
        for participant in match['info']['participants']:
            if participant['teamId'] == ownInfo['teamId']:
                continue
            enemyPosition = getPlayerPosition(participant)
            if enemyPosition == lane:
                rivalChamp = database.getChampionByKey(participant['championId'])

        # Procesamos partida en el diccionario de winrate para ese campeón
        if rivalChamp is None:
            continue

        # Determinamos en qué posición jugó el jugador
        if lane == "TOP":
            # Insertamos los resultados en el diccionario correspondiente
            if rivalChamp not in vsChampsTop:
                vsChampsTop[rivalChamp] = {"champId": database.getChampionIdByName(rivalChamp), "results": {}}
            if ownChamp not in vsChampsTop[rivalChamp]['results']:
                if win:
                    vsChampsTop[rivalChamp]['results'][ownChamp] = {"champId": database.getChampionIdByName(ownChamp),
                                                                    "wins": 1, "loses": 0}
                    totalCounted += 1
                else:
                    vsChampsTop[rivalChamp]['results'][ownChamp] = {"champId": database.getChampionIdByName(ownChamp),
                                                                    "wins": 0, "loses": 1}
                    totalCounted += 1
            else:
                if win:
                    vsChampsTop[rivalChamp]['results'][ownChamp]["wins"] += 1
                    totalCounted += 1
                else:
                    vsChampsTop[rivalChamp]['results'][ownChamp]["loses"] += 1
                    totalCounted += 1

        elif lane == "JUNGLE":
            if rivalChamp not in vsChampsJgl:
                vsChampsJgl[rivalChamp] = {"champId": database.getChampionIdByName(rivalChamp), "results": {}}
            if ownChamp not in vsChampsJgl[rivalChamp]['results']:
                if win:
                    vsChampsJgl[rivalChamp]['results'][ownChamp] = {"champId": database.getChampionIdByName(ownChamp),
                                                                    "wins": 1, "loses": 0}
                    totalCounted += 1
                else:
                    vsChampsJgl[rivalChamp]['results'][ownChamp] = {"champId": database.getChampionIdByName(ownChamp),
                                                                    "wins": 0, "loses": 1}
                    totalCounted += 1
            else:
                if win:
                    vsChampsJgl[rivalChamp]['results'][ownChamp]["wins"] += 1
                    totalCounted += 1
                else:
                    vsChampsJgl[rivalChamp]['results'][ownChamp]["loses"] += 1
                    totalCounted += 1

        elif lane == "MIDDLE":
            if rivalChamp not in vsChampsMid:
                vsChampsMid[rivalChamp] = {"champId": database.getChampionIdByName(rivalChamp), "results": {}}
            if ownChamp not in vsChampsMid[rivalChamp]['results']:
                if win:
                    vsChampsMid[rivalChamp]['results'][ownChamp] = {"champId": database.getChampionIdByName(ownChamp),
                                                                    "wins": 1, "loses": 0}
                    totalCounted += 1
                else:
                    vsChampsMid[rivalChamp]['results'][ownChamp] = {"champId": database.getChampionIdByName(ownChamp),
                                                                    "wins": 0, "loses": 1}
                    totalCounted += 1
            else:
                if win:
                    vsChampsMid[rivalChamp]['results'][ownChamp]["wins"] += 1
                    totalCounted += 1
                else:
                    vsChampsMid[rivalChamp]['results'][ownChamp]["loses"] += 1
                    totalCounted += 1

        elif lane == "BOTTOM":
            if rivalChamp not in vsChampsAdc:
                vsChampsAdc[rivalChamp] = {"champId": database.getChampionIdByName(rivalChamp), "results": {}}
            if ownChamp not in vsChampsAdc[rivalChamp]['results']:
                if win:
                    vsChampsAdc[rivalChamp]['results'][ownChamp] = {"champId": database.getChampionIdByName(ownChamp),
                                                                    "wins": 1, "loses": 0}
                    totalCounted += 1
                else:
                    vsChampsAdc[rivalChamp]['results'][ownChamp] = {"champId": database.getChampionIdByName(ownChamp),
                                                                    "wins": 0, "loses": 1}
                    totalCounted += 1
            else:
                if win:
                    vsChampsAdc[rivalChamp]['results'][ownChamp]["wins"] += 1
                    totalCounted += 1
                else:
                    vsChampsAdc[rivalChamp]['results'][ownChamp]["loses"] += 1
                    totalCounted += 1

        elif lane == "UTILITY":
            if rivalChamp not in vsChampsSup:
                vsChampsSup[rivalChamp] = {"champId": database.getChampionIdByName(rivalChamp), "results": {}}
            if ownChamp not in vsChampsSup[rivalChamp]['results']:
                if win:
                    vsChampsSup[rivalChamp]['results'][ownChamp] = {"champId": database.getChampionIdByName(ownChamp),
                                                                    "wins": 1, "loses": 0}
                    totalCounted += 1
                else:
                    vsChampsSup[rivalChamp]['results'][ownChamp] = {"champId": database.getChampionIdByName(ownChamp),
                                                                    "wins": 0, "loses": 1}
                    totalCounted += 1
            else:
                if win:
                    vsChampsSup[rivalChamp]['results'][ownChamp]["wins"] += 1
                    totalCounted += 1
                else:
                    vsChampsSup[rivalChamp]['results'][ownChamp]["loses"] += 1
                    totalCounted += 1

    # Se itera sobre cada vsChamps y se ordena por la suma total de partidas jugadas y cada campeón usado por la suma de sus wins + loses
    # vsChampsList = [vsChampsTop, vsChampsJgl, vsChampsMid, vsChampsAdc, vsChampsSup]
    # for vsChamps in vsChampsList:
    #     vsChamps = dict(sorted(vsChamps.items(),
    #                            key=lambda x: sum(champion["wins"] + champion["loses"] for champion in x[1][1].values()),
    #                            reverse=True))
    #
    #     for enemy, champs in vsChamps.items():
    #         vsChamps[enemy] = dict(sorted(champs.items(), key=lambda x: x[1][1]["wins"] + x[1][1]["loses"], reverse=True))

    vsChamps = {
        'Top': vsChampsTop,
        'Jungle': vsChampsJgl,
        'Mid': vsChampsMid,
        'Adc': vsChampsAdc,
        'Support': vsChampsSup
    }

    for pos, vsChampions in vsChamps.items():
        print(f'Stats en la posición {pos}:')
        for enemy, played in vsChampions.items():
            print(f"\t{enemy}({pos}): ")
            totalWins = totalLoses = 0
            for champ, stats in played['results'].items():
                totalWins += stats["wins"]
                totalLoses += stats["loses"]
                winrate = round(stats["wins"] / (stats["wins"] + stats["loses"]) * 100, 2)
                print(
                    f'\t\t{champ}: {stats["wins"]} victorias y {stats["loses"]} derrotas, haciendo un total de {winrate} %')
            print(
                f"\tEsto hace un balance de {totalWins} victorias y {totalLoses} derrotas contra {enemy}({pos}), con un rendimiento de {round(totalWins / (totalWins + totalLoses) * 100, 2)} %\n")
            vsChamps[pos][enemy]['results']['totalWins'] = totalWins
            vsChamps[pos][enemy]['results']['totalLoses'] = totalLoses
            vsChamps[pos][enemy]['results']['winrate'] = round(totalWins / (totalWins + totalLoses) * 100, 2)
        if pos != 'Support':
            print("\n")
    print(f'TOTAL ANALIZADAS: {totalCounted}')
    # Los remakes no se analizan puesto que sus datos son alterados y dan lugar a incoherencias
    print(f'TOTAL REMAKES: {remakes}')
    return vsChamps


def getPlayerPosition(info):
    if info is None:
        return None
    if info['teamPosition'] == info['individualPosition'] == info['lane']:
        return info['teamPosition']
    if info['teamPosition'] == info['lane']:
        return info['teamPosition']
    if info['teamPosition'] == info['individualPosition']:
        return info['teamPosition']
    if info['lane'] == 'NONE':
        return info['individualPosition']
    return info['lane']


def getWinrateAlongsideChampions(puuid, matches):
    # El objetivo de esta función es obtener el winrate del jugador contra una serie de campeones concretos.
    # Esto también se puede interpretar como el winrate de cada campeón contra el jugador
    # Creamos cinco diccionarios para los campeones, uno por cada posición
    # La estructura seguida debe ser:
    # {champName: {"champUsed": {"wins": x, "loses": x}, ...}}
    # Es decir, cada campeón almacena un diccionario de los resultados concretos del jugador contra él (campeón usado, victorias del campeón usado y derrotas del campeón usado)
    withChamps = {}
    remakes = 0

    # Recorremos las partidas del diccionario obteniendo la información del jugador en cada una
    for match in matches.values():
        ownInfo = getMatchPlayerInfo(puuid, match)
        if ownInfo is None:
            continue
        if ownInfo['gameEndedInEarlySurrender']:
            remakes += 1
            continue
        # Únicamente nos interesa obtener si el jugador ganó, en qué posición jugó, qué campeón utilizó y en qué equipo jugó
        win = ownInfo['win']
        ownChamp = database.getChampionByKey(ownInfo['championId'])
        ownTeam = ownInfo['teamId']
        if ownChamp not in withChamps:
            withChamps[ownChamp] = {'champId': database.getChampionIdByName(ownChamp), 'partners': {}, 'totalWins': 0,
                                    'totalLoses': 0}
        if ownChamp in withChamps.keys():
            if 'totalWins' in withChamps[ownChamp].keys() and 'totalLoses' in withChamps[ownChamp].keys():
                if win:
                    withChamps[ownChamp]['totalWins'] += 1
                else:
                    withChamps[ownChamp]['totalLoses'] += 1

        # Recorremos los participantes buscando a sus compañeros de equipo
        for participant in match['info']['participants']:
            if participant['teamId'] != ownTeam or participant['puuid'] == puuid:
                continue
            partnerPosition = getPlayerPosition(participant)
            partnerChamp = database.getChampionByKey(participant['championId'])
            # Procesamos partida en el diccionario de winrate para ese campeón
            if partnerChamp is None:
                continue
            # Almacenamos la información en función de lo jugador por el jugador y su compañero analizado
            # Insertamos los resultados en el diccionario correspondiente
            if partnerChamp not in withChamps[ownChamp]['partners']:
                withChamps[ownChamp]['partners'][partnerChamp] = {'champId': database.getChampionIdByName(partnerChamp),
                                                                  'results': {}}
            if partnerPosition not in withChamps[ownChamp]['partners'][partnerChamp]['results']:
                if win:
                    withChamps[ownChamp]['partners'][partnerChamp]['results'][partnerPosition] = {"wins": 1, "loses": 0}
                else:
                    withChamps[ownChamp]['partners'][partnerChamp]['results'][partnerPosition] = {"wins": 0, "loses": 1}
            else:
                if win:
                    withChamps[ownChamp]['partners'][partnerChamp]['results'][partnerPosition]["wins"] += 1
                else:
                    withChamps[ownChamp]['partners'][partnerChamp]['results'][partnerPosition]["loses"] += 1

    print(
        f'Se imprimen los campeones compañeros en todas las posiciones independientemente de dónde se jugara el campeón')
    for playerChampion, partners in withChamps.items():
        print(f'Stats para el campeón {playerChampion}:')
        for partner, partnerInfo in partners['partners'].items():
            totalWins = totalLoses = 0
            for pos, stats in partnerInfo['results'].items():
                totalWins += stats["wins"]
                totalLoses += stats["loses"]
                winrate = round(stats["wins"] / (stats["wins"] + stats["loses"]) * 100, 2)
                print(
                    f'\t{partner}({pos}): {stats["wins"]} victorias y {stats["loses"]} derrotas, haciendo un total de {winrate} %')
            print(
                f"\tEsto hace un balance de {totalWins} victorias y {totalLoses} derrotas con {partner} en todas sus posiciones, con un rendimiento de {round(totalWins / (totalWins + totalLoses) * 100, 2)} %\n")
            withChamps[playerChampion]['partners'][partner]['results']['totalWins'] = totalWins
            withChamps[playerChampion]['partners'][partner]['results']['totalLoses'] = totalLoses
            withChamps[playerChampion]['partners'][partner]['results']['winrate'] = round(
                totalWins / (totalWins + totalLoses) * 100, 2)
        print("\n")

    print(f'TOTAL ANALIZADAS: {len(matches) - remakes}')
    print(f'TOTAL REMAKES: {remakes}')
    return withChamps


def getSeasonAndPatch(match):
    version = match['info']['gameVersion']
    regex = r'^(\d+)\.(\d+)\.'
    matchResult = re.match(regex, version)
    if matchResult:
        return {'Season': matchResult.group(1),
                'Version': matchResult.group(2)}
    else:
        return None


def getQuickPlayerInfo(name, puuid, matches):
    mostPlayedPosition = getMostPlayedPosition(name, puuid, matches)
    data = getReferenceData(mostPlayedPosition)
    resultingData = {}
    #  1- Función de daño a objetivos y/o torretas promedio de las 10 últimas partidas jugadas
    proDmgToObjectivesTurretsData = dmgToObjectivesTurrets(data['puuid'], data['matches'], mostPlayedPosition, {})
    playerDmgToObjectivesTurrets = dmgToObjectivesTurrets(puuid, matches, mostPlayedPosition,
                                                          proDmgToObjectivesTurretsData)
    resultingData['Strategic Participation'] = playerDmgToObjectivesTurrets
    print(playerDmgToObjectivesTurrets)
    #  2- Función que calcule los pingeos promedios y los compare con el del jugador
    proMeanPlayerPings = meanPlayerPings(data['puuid'], data['matches'], {})
    playerPings = meanPlayerPings(puuid, matches, proMeanPlayerPings)
    resultingData['Player Pings'] = playerPings
    print(playerPings)
    #  3- Función que compruebe si se lleva la primera kill con frecuencia
    firstKiller = usualFirstKillerOrAssistant(puuid, matches)
    resultingData['FirstKiller'] = firstKiller
    print(firstKiller)
    #  4- Función que compara los daños recibidos e infligidos con los de su rival de posición
    dicDamage = damageTakenAndCaused(puuid, matches, mostPlayedPosition)
    resultingData['Damage Ingame'] = dicDamage
    print(dicDamage)
    #  5- Función que compruebe si ha hecho alguna multikill recientemente
    dicKills = isPlayerMultikiller(puuid, matches)
    resultingData['MultiKiller'] = dicKills
    print(dicKills)
    #  6- Función que compruebe si ha robado objetivos recientemente
    objectiveThief = isObjectiveThief(puuid, matches)
    resultingData['Objective Thief'] = objectiveThief
    print(objectiveThief)
    #  7- Función que obtenga la visión por minuto y valore el resultado
    proVision = getVisionPerMin(data['puuid'], data['matches'], mostPlayedPosition, {})
    playerVision = getVisionPerMin(puuid, matches, mostPlayedPosition, proVision)
    resultingData['Player Vision'] = playerVision
    print(playerVision)
    #  8- Función que devuelve la duración media por partida
    playerGameDuration = getMeanDuration(name, puuid, matches)
    resultingData['Mean Game Duration'] = playerGameDuration
    return resultingData


def dmgToObjectivesTurrets(puuid, matches, position, proData):
    # Habría que valorar estos datos en función de la posición, ya que:
    #  TOP: ++Daño a torres = ++Daño a estructuras > +Daño a objetivos
    #  JUNGLA: ++Daño a objetivos > +Daño a torres = +Daño a estructuras
    #  MID & ADC: +Daño a torres = +Daño a estructuras = +Daño a objetivos
    #  SUPPORT: +Daño a objetivos > -Daño a torres = -Daño a estructuras
    i = 0
    dicDamage = {'damageDealtToBuildings': 0,
                 'damageDealtToObjectives': 0,
                 'damageDealtToTurrets': 0}
    for matchData in matches.values():
        info = getMatchPlayerInfo(puuid, matchData)
        pos = getPlayerPosition(info)
        if pos != position:
            continue
        dicDamage['damageDealtToBuildings'] += info['damageDealtToBuildings']
        dicDamage['damageDealtToObjectives'] += info['damageDealtToObjectives']
        dicDamage['damageDealtToTurrets'] += info['damageDealtToTurrets']
        i += 1
        if i == 10:
            break
    dicDamage['damageDealtToBuildings'] = round(dicDamage['damageDealtToBuildings'] / 10)
    dicDamage['damageDealtToObjectives'] = round(dicDamage['damageDealtToObjectives'] / 10)
    dicDamage['damageDealtToTurrets'] = round(dicDamage['damageDealtToTurrets'] / 10)

    # Si proData está vacío, significa que estamos procesando a un proPlayer para obtener sus datos de referencia
    if proData == {}:
        return dicDamage
    # Si proData NO es vacío, entonces devolvemos los resultados de compararlo con los datos de referencia
    else:
        highImportanceRange = [-1500, -1000, -500, 500, 1000, 1500]
        mediumImportanceRange = [-3000, -1500, -750, 750, 1500, 3000]
        lowImportanceRange = [-5000, -2500, -1000, 1000, 2500, 5000]
        importancePoints = [1, 2, 3, 4, 5, 6, 7]
        pointsBuildings = pointsObjectives = pointsTurrets = 0
        diffBuildings = dicDamage['damageDealtToBuildings'] - proData['damageDealtToBuildings']
        diffObjectives = dicDamage['damageDealtToObjectives'] - proData['damageDealtToObjectives']
        diffTurrets = dicDamage['damageDealtToTurrets'] - proData['damageDealtToTurrets']
        if position == 'TOP':
            pointsBuildings = getPointsGivenRange(diffBuildings, highImportanceRange, importancePoints)
            pointsObjectives = getPointsGivenRange(diffObjectives, mediumImportanceRange, importancePoints)
            pointsTurrets = getPointsGivenRange(diffTurrets, highImportanceRange, importancePoints)
        elif position == 'JUNGLE':
            pointsBuildings = getPointsGivenRange(diffBuildings, mediumImportanceRange, importancePoints)
            pointsObjectives = getPointsGivenRange(diffObjectives, highImportanceRange, importancePoints)
            pointsTurrets = getPointsGivenRange(diffTurrets, mediumImportanceRange, importancePoints)
        elif position == 'MIDDLE':
            pointsBuildings = getPointsGivenRange(diffBuildings, mediumImportanceRange, importancePoints)
            pointsObjectives = getPointsGivenRange(diffObjectives, mediumImportanceRange, importancePoints)
            pointsTurrets = getPointsGivenRange(diffTurrets, lowImportanceRange, importancePoints)
        elif position == 'BOTTOM':
            pointsBuildings = getPointsGivenRange(diffBuildings, mediumImportanceRange, importancePoints)
            pointsObjectives = getPointsGivenRange(diffObjectives, mediumImportanceRange, importancePoints)
            pointsTurrets = getPointsGivenRange(diffTurrets, lowImportanceRange, importancePoints)
        elif position == 'UTILITY':
            pointsBuildings = getPointsGivenRange(diffBuildings, lowImportanceRange, importancePoints)
            pointsObjectives = getPointsGivenRange(diffObjectives, mediumImportanceRange, importancePoints)
            pointsTurrets = getPointsGivenRange(diffTurrets, lowImportanceRange, importancePoints)

        resultDict = {}
        if pointsBuildings <= 2:
            resultDict['Buildings Damage'] = {'result': 'Negative', 'text': 'Low damage to buildings'}
        elif 3 <= pointsBuildings < 6:
            resultDict['Buildings Damage'] = {'result': "Normal", 'text': "Normal damage to buildings"}
        elif 6 <= pointsBuildings:
            resultDict['Buildings Damage'] = {'result': "Good", 'text': "Good damage to buildings"}

        if pointsObjectives <= 2:
            resultDict['Objectives Damage'] = {'result': 'Negative', 'text': 'Low damage to objectives'}
        elif 3 <= pointsObjectives < 6:
            resultDict['Objectives Damage'] = {'result': "Normal", 'text': "Normal damage to objectives"}
        elif 6 <= pointsObjectives:
            resultDict['Objectives Damage'] = {'result': "Good", 'text': "Good damage to objectives"}

        if pointsTurrets <= 2:
            resultDict['Turrets Damage'] = {'result': 'Negative', 'text': 'Low damage to turrets'}
        elif 3 <= pointsTurrets < 6:
            resultDict['Turrets Damage'] = {'result': "Normal", 'text': "Normal damage to turrets"}
        elif 6 <= pointsTurrets:
            resultDict['Turrets Damage'] = {'result': "Good", 'text': "Good damage to turrets"}

        return resultDict


def meanPlayerPings(puuid, matches, proData):
    i = 0
    dicPings = {
        'allInPings': 0,
        'assistMePings': 0,
        'basicPings': 0,
        'commandPings': 0,
        'dangerPings': 0,
        'enemyMissingPings': 0,
        'enemyVisionPings': 0,
        'getBackPings': 0,
        'holdPings': 0,
        'needVisionPings': 0,
        'onMyWayPings': 0,
        'pushPings': 0,
        'visionClearedPings': 0
    }
    for matchID, matchInfo in matches.items():
        playerInfo = getMatchPlayerInfo(puuid, matchInfo)
        for key in dicPings:
            try:
                dicPings[key] += playerInfo[key]
            except KeyError as e:
                print(f'{e} en {matchID} para {puuid}')
        i += 1
        if i >= 10:
            break
    if proData == {}:
        return dicPings
    else:
        proPings = round(sum(proData.values()) * 1.25)
        totalPings = sum(dicPings.values())
        if proPings < totalPings:
            return {'result': "Normal", 'text': "Pings a lot"}
        return {'result': "Normal", 'text': "Does not ping too much"}


def usualFirstKillerOrAssistant(puuid, matches):
    i = 0
    firstKillParticipation = 0
    for matchInfo in matches.values():
        info = getMatchPlayerInfo(puuid, matchInfo)
        if info['firstBloodAssist'] or info['firstBloodKill']:
            firstKillParticipation += 1
        i += 1
        if i >= 15:
            break
    if firstKillParticipation > 4:
        return {'result': "Good", 'text': "First kill participant"}
    return {'result': "Normal", 'text': "Not usually first killer"}


def damageTakenAndCaused(puuid, matches, position):
    i = 0
    dicDamage = {
        'totalDamageDealt': 0,
        'totalDamageDealtToChampions': 0,
        'totalDamageTaken': 0
    }
    for matchID, matchInfo in matches.items():
        info = getMatchPlayerInfo(puuid, matchInfo)
        playerPosition = getPlayerPosition(info)
        if playerPosition != position:
            continue
        totalDamageDealt = info['totalDamageDealt']
        totalDamageDealtToChampions = info['totalDamageDealtToChampions']
        totalDamageTaken = info['totalDamageTaken']
        teamID = info['teamId']
        for participant in matchInfo['info']['participants']:
            if participant['teamId'] == teamID:
                continue
            if getPlayerPosition(participant) == playerPosition:
                rivalDamageDealt = participant['totalDamageDealt']
                rivalDamageDealtToChampions = participant['totalDamageDealtToChampions']
                rivalDamageTaken = participant['totalDamageTaken']

                if totalDamageDealt - rivalDamageDealt < 0:
                    dicDamage['totalDamageDealt'] -= 1
                elif totalDamageDealt - rivalDamageDealt > 0:
                    dicDamage['totalDamageDealt'] += 1
                if totalDamageDealtToChampions - rivalDamageDealtToChampions < 0:
                    dicDamage['totalDamageDealtToChampions'] -= 1
                elif totalDamageDealtToChampions - rivalDamageDealtToChampions > 0:
                    dicDamage['totalDamageDealtToChampions'] += 1
                if totalDamageTaken - rivalDamageTaken < 0:
                    dicDamage['totalDamageTaken'] -= 1
                elif totalDamageTaken - rivalDamageTaken > 0:
                    dicDamage['totalDamageTaken'] += 1
                i += 1
                break
        if i >= 10:
            break

    resultDic = {}
    if dicDamage['totalDamageDealt'] <= -8:
        resultDic['Total Damage Dealt'] = {'result': 'Negative', 'text': 'Very low total damage dealt'}
    elif -8 <= dicDamage['totalDamageDealt'] < -3:
        resultDic['Total Damage Dealt'] = {'result': "Negative", 'text': "Low total damage dealt"}
    elif -3 <= dicDamage['totalDamageDealt'] < 4:
        resultDic['Total Damage Dealt'] = {'result': "Normal", 'text': "Normal total damage dealt"}
    elif 4 <= dicDamage['totalDamageDealt'] < 8:
        resultDic['Total Damage Dealt'] = {'result': "Good", 'text': "High total damage dealt"}
    elif dicDamage['totalDamageDealt'] >= 8:
        resultDic['Total Damage Dealt'] = {'result': "Good", 'text': "Very high total damage dealt"}

    if dicDamage['totalDamageDealtToChampions'] <= -8:
        resultDic['Damage Dealt To Champions'] = {'result': 'Negative',
                                                  'text': 'Very low total damage dealt to champions'}
    elif -8 <= dicDamage['totalDamageDealtToChampions'] < -3:
        resultDic['Damage Dealt To Champions'] = {'result': "Negative", 'text': "Low total damage dealt to champions"}
    elif -3 <= dicDamage['totalDamageDealtToChampions'] < 4:
        resultDic['Damage Dealt To Champions'] = {'result': "Normal", 'text': "Normal total damage dealt to champions"}
    elif 4 <= dicDamage['totalDamageDealtToChampions'] < 8:
        resultDic['Damage Dealt To Champions'] = {'result': "Good", 'text': "High total damage dealt to champions"}
    elif dicDamage['totalDamageDealtToChampions'] >= 8:
        resultDic['Damage Dealt To Champions'] = {'result': "Good", 'text': "Very high total damage dealt to champions"}

    if dicDamage['totalDamageTaken'] <= -8:
        resultDic['Damage Taken'] = {'result': 'Negative', 'text': 'Very low total damage taken'}
    elif -8 <= dicDamage['totalDamageTaken'] < -3:
        resultDic['Damage Taken'] = {'result': "Negative", 'text': "Low total damage taken"}
    elif -3 <= dicDamage['totalDamageTaken'] < 4:
        resultDic['Damage Taken'] = {'result': "Normal", 'text': "Normal total damage taken"}
    elif 4 <= dicDamage['totalDamageTaken'] < 8:
        resultDic['Damage Taken'] = {'result': "Good", 'text': "High total damage taken"}
    elif dicDamage['totalDamageTaken'] >= 8:
        resultDic['Damage Taken'] = {'result': "Good", 'text': "Very high total damage taken"}

    return resultDic


def isObjectiveThief(puuid, matches):
    i = 0
    for matchInfo in matches.values():
        info = getMatchPlayerInfo(puuid, matchInfo)
        if info['objectivesStolen'] > 0:
            return {'result': "Good", 'text': "Objectives thief"}
        i += 1
        if i >= 5:
            break
    return {'result': "Negative", 'text': "Objectives not stolen"}


def isPlayerMultikiller(puuid, matches):
    i = 0
    dicKills = {
        'pentaKills': {'count': 0, 'flag': False},
        'quadraKills': {'count': 0, 'flag': False},
        'tripleKills': {'count': 0, 'flag': False},
        'doubleKills': {'count': 0, 'flag': False}
    }
    for matchID, matchInfo in matches.items():
        info = getMatchPlayerInfo(puuid, matchInfo)
        for key in dicKills:
            try:
                dicKills[key]['count'] += info[key]
            except KeyError as e:
                print(f'{e} en {matchID} para {puuid}')
        i += 1
        if i >= 15:
            break

    resultDic = {}
    if dicKills['pentaKills']['count'] > 0:
        resultDic['PentaKills'] = {'result': "Good", 'text': "Pentakiller"}
    if dicKills['quadraKills']['count'] > 0:
        resultDic['QuadraKills'] = {'result': "Good", 'text': "Quadrakiller"}
    if dicKills['tripleKills']['count'] >= 2:
        resultDic['TripleKills'] = {'result': "Good", 'text': "Triplekiller"}
    if dicKills['doubleKills']['count'] >= 5:
        resultDic['DoubleKills'] = {'result': "Good", 'text': "Doublekiller"}
    return resultDic


def getVisionPerMin(puuid, matches, position, proData):
    i = totalDuration = 0
    dicVision = {
        'visionScore': 0,
        'detectorWardsPlaced': 0,
        'wardsPlaced': 0,
        'wardsKilled': 0
    }
    for matchID, matchData in matches.items():
        info = getMatchPlayerInfo(puuid, matchData)
        if getPlayerPosition(info) != position:
            continue
        totalDuration += matchData['info']['gameDuration']
        for key in dicVision:
            try:
                dicVision[key] += info[key]
            except KeyError as e:
                print(f'{e} en {matchID} para {puuid}')
        i += 1
        if i >= 15:
            break
    totalDuration = round(totalDuration / 60, 2)
    visionPerMin = round(dicVision['visionScore'] / totalDuration, 2)
    dicVision['visionPerMin'] = visionPerMin

    if proData == {}:
        return dicVision
    else:
        diffVisionPerMin = dicVision['visionPerMin'] - proData['visionPerMin']
        diffDetectorWards = dicVision['detectorWardsPlaced'] - proData['detectorWardsPlaced']
        diffVisionWards = dicVision['wardsPlaced'] - proData['wardsPlaced']
        diffWardsKilled = dicVision['wardsKilled'] - proData['wardsKilled']
        dicPlayerVision = {}
        if diffVisionPerMin >= 0.5:
            # Buena visión
            dicPlayerVision['Vision Per Minute'] = {'result': "Good", 'text': "Good vision per minute"}
        elif diffVisionPerMin <= -0.5:
            # Mala visión
            dicPlayerVision['Vision Per Minute'] = {'result': "Negative", 'text': "Bad vision per minute"}
        else:
            # No es buena ni mala
            dicPlayerVision['Vision Per Minute'] = {'result': "Normal", 'text': "Average vision per minute"}

        if diffDetectorWards >= 20:
            # Buena visión
            dicPlayerVision['Pink Wards'] = {'result': "Good", 'text': "Buys pink wards"}
        elif diffDetectorWards <= -20:
            # Mala visión
            dicPlayerVision['Pink Wards'] = {'result': "Negative", 'text': "Not enough pink wards"}
        else:
            # No es buena ni mala
            dicPlayerVision['Pink Wards'] = {'result': "Normal", 'text': "Average pink wards"}

        if diffVisionWards >= 25:
            # Buena visión
            dicPlayerVision['Normal Wards'] = {'result': "Good", 'text': "Good ward placement"}
        elif diffVisionWards <= -25:
            # Mala visión
            dicPlayerVision['Normal Wards'] = {'result': "Negative", 'text': "Bad ward placement"}
        else:
            # No es buena ni mala
            dicPlayerVision['Normal Wards'] = {'result': "Normal", 'text': "Average ward placement"}

        if diffWardsKilled >= 15:
            # Buena visión
            dicPlayerVision['Wards Cleaning'] = {'result': "Good", 'text': "Many wards cleaned"}
        elif diffWardsKilled <= -15:
            # Mala visión
            dicPlayerVision['Wards Cleaning'] = {'result': "Negative", 'text': "Few wards cleaned"}
        else:
            # No es buena ni mala
            dicPlayerVision['Wards Cleaning'] = {'result': "Normal", 'text': "Average wards cleaned"}
        return dicPlayerVision


def getMostPlayedPosition(name, puuid, matches):
    # Obtenemos la posición más jugada
    dicPos = getMatchesPosition(name, puuid, matches)
    pos = None
    aux = 1
    while pos is None:
        for role, modes in dicPos.items():
            total_sum = sum(modes.values())
            other_sum = sum(sum(dicPos[other_role].values()) for other_role in dicPos if other_role != role)
            if total_sum > other_sum * aux:
                pos = role
                break
        aux *= 0.75
    return pos


def getProPlayersHistory():
    # Recuperamos la lista de los mejores proPlayers
    proPlayers = api.getProPlayers()
    dicMatches = {}
    count = 0
    top = jungle = mid = adc = support = False
    for pro in proPlayers:
        if top and jungle and mid and adc and support:
            break
        proPUUID = api.getSummonerPUUIDbySummonerId(pro['summonerId'])
        proName = pro['summonerName']
        print(f'Procesando al jugador {proName}')
        # Si el proPlayer existe en nuestra BBDD, entonces recuperamos sus partidas y las analizamos para obtener los datos de referencia
        if database.checkPlayerDB(proPUUID):
            proMatches = database.getAllPlayersGames(proPUUID)
        # Si no existe, entonces pedimos las primeras 20 partidas de tipo Ranked a la API y obtenemos sus datos de referencia
        else:
            # Registramos al proPlayer
            api.registerSummonerByPUUID(proPUUID)
            proMatches = api.getRankedGames(proPUUID, 0, round(time.time()), 20)
        if 0 <= len(proMatches) < 20:
            proNewMatches = api.getRankedGames(proPUUID, 0, round(time.time()), 20)
            for newMatchID, newMatchInfo in proNewMatches.items():
                if newMatchID in proMatches:
                    continue
                proMatches[newMatchID] = newMatchInfo
            if 0 <= len(proMatches) < 20:
                continue
        position = getMostPlayedPosition(proName, proPUUID, proMatches)
        if position == 'TOP' and top or position == 'JUNGLE' and jungle or position == 'MIDDLE' and mid or position == 'BOTTOM' and adc or position == 'UTILITY' and support:
            continue
        elif position == 'TOP' and not top:
            top = True
            dicMatches[position] = {}
        elif position == 'JUNGLE' and not jungle:
            jungle = True
            dicMatches[position] = {}
        elif position == 'MIDDLE' and not mid:
            mid = True
            dicMatches[position] = {}
        elif position == 'BOTTOM' and not adc:
            adc = True
            dicMatches[position] = {}
        elif position == 'UTILITY' and not support:
            support = True
            dicMatches[position] = {}

        if proPUUID not in dicMatches[position].keys():
            dicMatches[position][proPUUID] = {}
            count += 1
            for matchID, matchInfo in proMatches.items():
                if matchID in dicMatches[position][proPUUID].keys():
                    continue
                dicMatches[position][proPUUID][matchID] = matchInfo
                if database.checkGameDB(matchID):
                    continue
                database.storeGameDB(matchInfo)

    print(f'Se han obtenido las partidas de los {count} proPlayers')
    return dicMatches


def getGivenProPlayersHistoryByPosition(pros, position):
    dicData = None
    for pro in pros:
        proName = api.getSummonerName(pro)
        print(f'Procesando al jugador {proName}')
        if database.checkPlayerDB(pro):
            proMatches = database.getAllPlayersGames(pro)
            if 0 <= len(proMatches) < 20:
                continue
            dicPos = getMatchesPosition(proName, pro, proMatches)
            proPos = sum(dicPos[position].values())
            if proPos >= 15:
                dicData = {'puuid': pro,
                           'name': proName,
                           'matches': {}}
                for matchID, matchInfo in proMatches.items():
                    pos = getPlayerPosition(getMatchPlayerInfo(pro, matchInfo))
                    if pos == position:
                        dicData['matches'][matchID] = matchInfo
                    if database.checkGameDB(matchID):
                        continue
                print(f'Se han obtenido las partidas de {proName}')
                break
        else:
            continue
    return dicData


def getUnknownProPlayersHistoryByPosition(position):
    # Recuperamos la lista de los mejores proPlayers
    proPlayers = api.getProPlayers()
    for pro in proPlayers:
        proPUUID = api.getSummonerPUUIDbySummonerId(pro['summonerId'])
        proName = api.getSummonerName(proPUUID)
        print(f'Procesando al jugador {proName}')
        # Si el proPlayer existe en nuestra BBDD, entonces recuperamos sus partidas y las analizamos para obtener los datos de referencia
        if database.checkPlayerDB(proPUUID):
            proMatches = database.getAllPlayersGames(proPUUID)
        # Si no existe, entonces pedimos las primeras 20 partidas de tipo Ranked a la API y obtenemos sus datos de referencia
        else:
            # Registramos al proPlayer
            api.registerSummonerByPUUID(proPUUID)
            proMatches = api.getRankedGames(proPUUID, 0, round(time.time()), 20)
        if 0 <= len(proMatches) < 20:
            proNewMatches = api.getRankedGames(proPUUID, 0, round(time.time()), 20)
            for newMatchID, newMatchInfo in proNewMatches.items():
                if newMatchID in proMatches:
                    continue
                proMatches[newMatchID] = newMatchInfo
            if 0 <= len(proMatches) < 20:
                continue
        dicPos = getMatchesPosition(proName, proPUUID, proMatches)
        proPos = sum(dicPos[position].values())
        if proPos >= 15:
            dicData = {'puuid': proPUUID,
                       'name': proName,
                       'matches': {}}
            for matchID, matchInfo in proMatches.items():
                pos = getPlayerPosition(getMatchPlayerInfo(proPUUID, matchInfo))
                if pos == position:
                    dicData['matches'][matchID] = matchInfo
                if database.checkGameDB(matchID):
                    continue
                database.storeGameDB(matchInfo)
            print(f'Se han obtenido las partidas de {proName}')
            return dicData


def plotImage(listName, pointList, color):
    scaleFactor = 10
    imagePath = './lib/map/map.png'
    scaledPoints = [((x - 240) / scaleFactor, (14980 - y + 240) / scaleFactor) for x, y in pointList]
    img = mpimg.imread(imagePath)
    plt.imshow(img)
    for scaledX, scaledY in scaledPoints:
        plt.scatter(scaledX, scaledY, color=color, s=75)
    plt.axis('off')
    plt.title(listName)
    plt.show()


def plotHeatMap(listName, pointList):
    plt.clf()
    scaleFactor = 10
    imagePath = '../lib/map/map.png'
    # imagePath = './lib/map/map.png'
    scaledPoints = [((x - 240) / scaleFactor, (14980 - y + 240) / scaleFactor) for x, y in pointList]
    img = mpimg.imread(imagePath)
    plt.imshow(img)

    df = pd.DataFrame(scaledPoints, columns=['x', 'y'])
    plt.xlim(0, 1499)
    plt.ylim(1499, 0)
    for scaledX, scaledY in scaledPoints:
        plt.scatter(scaledX, scaledY, color='white', s=20, alpha=0.2)
    print(f'df: {df} // len_df: {len(df)} // // len_scaledPoints: {len(scaledPoints)} // listname: {listName}')
    # sns.kdeplot(df, x='x', y='y', fill=True, cmap='Spectral', antialiased=True, bw_method=0.35, alpha=0.35)
    sns.kdeplot(df, x='x', y='y', fill=True, cmap='Spectral', antialiased=True, bw_method=0.35, levels=100, alpha=0.35)


    # sns.kdeplot(df, x='x', y='y', fill=True, cmap='Spectral', color='r', thresh=0, bw_method=0.3, levels=80, alpha=0.25)
    plt.axis('off')
    # plt.title(listName)
    plt.show()
    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    # plt.close(img)

    buffer.seek(0)
    return buffer
    # encoded_img = base64.b64encode(buffer.getvalue()).decode('utf-8')
    # return encoded_img


def drawKillsHeatmaps(puuid, matches):
    i = 0
    blueKillPositions = []
    redKillPositions = []
    blueAssistPositions = []
    redAssistPositions = []
    blueDeathPositions = []
    redDeathPositions = []
    for matchID, matchData in matches.items():
        matchTimeline = api.getMatchTimeline(matchID)
        if matchTimeline is None:
            continue
        playerID = 0
        for index, participant in enumerate(matchTimeline['metadata']['participants']):
            if participant == puuid:
                playerID = index + 1
        if playerID == 0:
            continue
        teamID = getMatchPlayerInfo(puuid, matchData)['teamId']
        if teamID != 100 and teamID != 200:
            continue
        frames = matchTimeline['info']['frames']
        for frame in frames:
            for event in frame['events']:
                if event['type'] == 'CHAMPION_KILL':
                    if event['killerId'] == playerID:
                        if teamID == 100:
                            blueKillPositions.append((event['position']['x'], event['position']['y']))
                        elif teamID == 200:
                            redKillPositions.append((event['position']['x'], event['position']['y']))
                    elif event['victimId'] == playerID:
                        if teamID == 100:
                            blueDeathPositions.append((event['position']['x'], event['position']['y']))
                        elif teamID == 200:
                            redDeathPositions.append((event['position']['x'], event['position']['y']))
                    try:
                        if playerID in event['assistingParticipantIds']:
                            if teamID == 100:
                                blueAssistPositions.append((event['position']['x'], event['position']['y']))
                            elif teamID == 200:
                                redAssistPositions.append((event['position']['x'], event['position']['y']))
                    except KeyError:
                        continue
        i += 1
        if i >= 7:
            break

    # plotHeatMap('blueKillPositions', blueKillPositions)
    # plotHeatMap('redKillPositions', redKillPositions)
    # plotHeatMap('blueAssistPositions', blueAssistPositions)
    # plotHeatMap('redAssistPositions', redAssistPositions)
    # plotHeatMap('blueDeathPositions', blueDeathPositions)
    # plotHeatMap('redDeathPositions', redDeathPositions)
    # plotHeatMap('AllKillPositions', blueKillPositions + redKillPositions)
    # plotHeatMap('AllAssistPositions', blueAssistPositions + redAssistPositions)
    # plotHeatMap('AllDeathPositions', blueDeathPositions + redDeathPositions)
    print(len(blueKillPositions))
    print(blueKillPositions)
    print(len(redKillPositions))
    print(len(blueAssistPositions))
    print(len(redAssistPositions))
    print(len(blueDeathPositions))
    print(len(redDeathPositions))
    images = {'blueKillPositions': plotHeatMap('blueKillPositions', blueKillPositions),
              'redKillPositions': plotHeatMap('redKillPositions', redKillPositions),
              'blueAssistPositions': plotHeatMap('blueAssistPositions', blueAssistPositions),
              'redAssistPositions': plotHeatMap('redAssistPositions', redAssistPositions),
              'blueDeathPositions': plotHeatMap('blueDeathPositions', blueDeathPositions),
              'redDeathPositions': plotHeatMap('redDeathPositions', redDeathPositions),
              'AllKillPositions': plotHeatMap('AllKillPositions', blueKillPositions + redKillPositions),
              'AllAssistPositions': plotHeatMap('AllAssistPositions', blueAssistPositions + redAssistPositions),
              'AllDeathPositions': plotHeatMap('AllDeathPositions', blueDeathPositions + redDeathPositions)}
    return images
