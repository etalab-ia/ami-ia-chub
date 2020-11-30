from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import OperationalError
from pymantic import sparql
import pandas as pd
import logging


class PostgresqlDB:

    instance = None

    def __init__(self, *args, **kwargs):
        if not PostgresqlDB.instance:
            PostgresqlDB.instance = PostgresqlDbInit(*args, **kwargs)

    def __getattr__(self, name):
        return getattr(self.instance, name)


class PostgresqlDbInit:
    def __init__(self, app, host=None, db_name=None, user=None, pwd=None):
        if app:
            self.db = SQLAlchemy(app)
            self.connexion = self.db.get_engine()
        else:
            self.db = SQLAlchemy()
            self.connexion = self.db.create_engine('postgresql://'+user+':'+pwd+'@'+host+'/'+db_name,
                                                   {})
        self.logger = logging.getLogger('PostgresqlDb')

    def load_data(self, sql_query):
        self.logger.debug(sql_query)
        # Load the data
        try:
            return pd.read_sql(sql_query, self.connexion)
        except OperationalError as err:
            self.logger.error(str(err))
            raise RuntimeError(str(err))
        except Exception as err:
            self.logger.error(str(err))
            raise ValueError(str(err))


class SparqlDB:
    instance = None

    def __init__(self, **kwargs):
        if not SparqlDB.instance:
            SparqlDB.instance = SparqlDbInit(**kwargs)

    def __getattr__(self, name):
        return getattr(self.instance, name)


class SparqlDbInit:
    def __init__(self, host, use_metadata=True):
        self.connexion = sparql.SPARQLServer(host)
        self.logger = logging.getLogger('SparqlDb')
        self.use_metadata = use_metadata
        if not self.use_metadata:
            self.logger.warn("Sparql link is deactivated")

    def load_data(self, sparql_query):
        try:
            # Load the data
            if not self.use_metadata:
                return None
            self.logger.debug(sparql_query)
            return self.connexion.query(sparql_query)
        except Exception as err:
            self.logger.error(str(err))
            raise ValueError(str(err))