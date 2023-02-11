import json
import random

import sqlalchemy as db


class DB:

    def __init__(self,host, port, user, password, database):


        db_user = user
        db_pwd = password
        db_host = host
        db_port = port
        db_name = database

        connection_str = f'mysql+pymysql://{db_user}:{db_pwd}@{db_host}:{db_port}/{db_name}'

        self.engine = db.create_engine(connection_str)
        self.connection = self.engine.connect()
        self.metadata = db.MetaData()
        self.logTable = db.Table('python_logs_kyc', self.metadata, autoload=True, autoload_with=self.engine)
        print(self.logTable.columns.keys())



    def insertLog(self,refId, timestamp, level, log,logType,devEnv ,screenshotPath):
        query = db.insert(self.logTable).values(refId = refId,timestamp=timestamp, level=level, log=log,type = logType,
                                                screenshotName=screenshotPath,devEnvironment = devEnv)
        ResultProxy = self.connection.execute(query)


    def close(self):
        self.connection.close()
        self.engine.dispose()












