from pymongo import MongoClient
from app import api

teamAnalyticAPIKey = 'RGAPI-5b5ad231-cb44-4bd0-9306-d58dc37ca228'
# TODO Si migramos la base de datos de local a otro sitio, hay que cambiar el argumento de MongoClient(), ya que
#  así funciona para localhost:27017
cliente = MongoClient()
db = cliente['TFG']
dbChampions = db['Champions']
dbMatches = db['Matches']
dbSummoner = db['Summoners']

if __name__ == '__main__':
    api.updateChampionsDB()
    #summoner_name = input("Introduce tu nombre de usuario: ")
    #loginAPI(dbSummoner, teamAnalyticAPIKey, summoner_name)
