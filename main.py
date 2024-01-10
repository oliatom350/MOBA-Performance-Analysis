from app import api

teamAnalyticAPIKey = 'RGAPI-5b5ad231-cb44-4bd0-9306-d58dc37ca228'

if __name__ == '__main__':
    #api.updateChampionsDB()
    summoner_name = input("Introduce tu nombre de usuario: ")
    api.loginAPI(teamAnalyticAPIKey, summoner_name)
