from sqlalchemy import create_engine
import pandas as pd


def export_to_df(dbname, table):
    """
    Connect to the Postgres database and get the data frame

    :return: A data frame containing
    """

    PG_ACCESS_HOST = 'localhost'
    PG_ACCESS_PORT = '5432'
    PG_ACCESS_DBNAME = dbname       # 'chu-bordeaux' pour obs_fact et 'ghpsj-v2' pour les 2 autres
    PG_ACCESS_USER = 'admin'
    PG_ACCESS_PASS = 'admin'

    PG_ACCESS_URL = ('postgresql+psycopg2://'
                     + PG_ACCESS_USER + ':'
                     + PG_ACCESS_PASS + '@'
                     + PG_ACCESS_HOST + ':'
                     + PG_ACCESS_PORT + '/'
                     + PG_ACCESS_DBNAME)

    engine = create_engine(PG_ACCESS_URL)

    sql_query = 'SELECT * FROM ' + table

    df_obs = pd.read_sql_query(sql_query, con=engine)

    return df_obs
