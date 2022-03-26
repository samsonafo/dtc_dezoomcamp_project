import os

from time import time

import pandas as import pd
from sqlalchemy import create_engine


def ingest_callable(user, password, host, port, db, table_name, csv_file, execution_date):
    print(table_name, csv_file, execution_date)

    engine = create_engine(f'postgresql://{user}:{password}@{host}:{port}/{db}')
    engine.connect()

    print('connection established succesfully, importing data ...')

    t_start = time()
    df_iter = pd.read_csv(csv_file, iterator=True, chunksize=10000)

    df = next(df_iter)

    df.starttime = pd.to_datetime(df.starttime)
    df.stoptime = pd.to_datetime(df.stoptime)

    df.head(n=0).to_sql(name=table_name, con=engine, if_exists='replace')

    df.to_sql(name=table_name, con=engine, if_exists='append')

    t_end = time()
    print('inserted the first chunk, took %.3f second' % (t_end - t_start))

    while True: 
        t_start = time()

        try:
            df = next(df_iter)
        except StopIteration:
            print("completed")
            break

        df.starttime = pd.to_datetime(df.starttime)
        df.stoptime = pd.to_datetime(df.stoptime)

        df.to_sql(name=table_name, con=engine, if_exists='append')

        t_end = time()

        print('inserted another chunk, took %.3f second' % (t_end - t_start))
