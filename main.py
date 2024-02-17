from app import api, database, proc_data


if __name__ == '__main__':
    # database.clearCollection(0)
    # database.clearCollection(1)
    # database.clearCollection(2)

    api.updateChampions()
    summoner_name = input("Introduce tu nombre de usuario: ")
    # puuidInicial = api.getSummonerPUUID(summoner_name)
    # api.getMatches(puuidInicial)

    if api.getSummonerPUUID(summoner_name) is None:
        print(f'El jugador {summoner_name} no existe')
    else:
        proc_data.processPlayer(summoner_name)

