from pymongo import MongoClient


def get_database():
    # MongoDB Connection String
    CONNECTION_STRING = 'mongodb://localhost:27017/'

    client = MongoClient(CONNECTION_STRING)

    # return database, format = client['database_name']
    return client['ceci-csic']


def get_regulation_id(db, regulation_title):
    collection = db['regulations']

    query = {'title': regulation_title}
    document = collection.find_one(query)

    if document:
        return document['_id']
    else:
        return None
