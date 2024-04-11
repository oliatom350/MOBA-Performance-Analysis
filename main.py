from app import api, proc_data, database

if __name__ == '__main__':
    # database.clearCollection(0)
    # database.clearCollection(1)
    # database.clearCollection(2)

    api.updateChampions()
    summonerName = input("Introduce tu nombre de usuario: ")
    summonerTag = input("Introduce tu riotID: ")
    puuidInicial = api.getSummonerPUUID(summonerName, summonerTag)
    if puuidInicial is None:
        print(f'El jugador {summonerName} no existe')
    else:
        # api.getMatches(puuidInicial)
        # proc_data.processPlayer(summoner_name)
        # database.getQueues()
        # print(api.registerSummonerByRiotId(summonerName, summonerTag))
        # print(api.registerSummonerByPUUID(puuidInicial))
        for player in database.getAllPlayers():
            api.registerSummonerByPUUID(player["puuid"])
