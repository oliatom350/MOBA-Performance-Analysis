from app import api, database

teamAnalyticAPIKey = 'RGAPI-5b5ad231-cb44-4bd0-9306-d58dc37ca228'

if __name__ == '__main__':
    database.clearCollection()
    api.updateChampions()
    # summoner_name = input("Introduce tu nombre de usuario: ")
    # api.loginAPI(teamAnalyticAPIKey, summoner_name)
