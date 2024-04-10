from app import api, proc_data, database

if __name__ == '__main__':
    # database.clearCollection(0)
    # database.clearCollection(1)
    # database.clearCollection(2)

    api.updateChampions()
    summoner_name = input("Introduce tu nombre de usuario: ")
    puuidInicial = api.getSummonerPUUID(summoner_name)
    if puuidInicial is None:
        print(f'El jugador {summoner_name} no existe')
    else:
        # api.getMatches(puuidInicial)
        # proc_data.processPlayer(summoner_name)
        # database.getQueues()
        for player in database.getAllPlayers():
            if player["name"] != "":
                api.registerSummoner(player["name"])
            else:
                api.registerSummoner(player["puuid"])
