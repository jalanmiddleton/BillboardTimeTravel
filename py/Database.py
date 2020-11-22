import MySQLdb
from secrets import secrets

class Database:
    __instance = None

    @staticmethod
    def getInstance():
        if Database.__instance is None:
            Database()
        return Database.__instance

    def __init__(self):
        if Database.__instance is  None:
            self.__conn = MySQLdb.connect(host="localhost", user="root",
                                    passwd=secrets["HOST_PASSWORD"], db="billboard",
                                    use_unicode=True, charset="utf8")
            self.__cur = self.__conn.cursor()
            Database.__instance = self

    def insert(query):
        self.__cur.execute(query)
        self.__conn.commit()

    def select(query):
        self.__cur.execute(query)
        return self.__cur.fetchall()
