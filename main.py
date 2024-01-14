from app import api, database


if __name__ == '__main__':
    database.clearCollection()
    api.updateChampions()
    # summoner_name = input("Introduce tu nombre de usuario: ")
    # api.loginAPI(teamAnalyticAPIKey, summoner_name)
