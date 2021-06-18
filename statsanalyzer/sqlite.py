import sqlite3
import pandas as pd
import util

import warnings

warnings.filterwarnings("ignore")

db = sqlite3.connect(":memory:")


def load_df(d, name="df"):
    d.to_sql(name, db)
    db.create_function("get_ratio", 2, util.get_ratio)
    db.create_function("blocks_to_bytes", 1, util.blocks_to_bytes)
    db.create_function("tz_to_notz", 1, util.tz_to_notz)
    db.create_function("convert_bytes", 1, util.convert_bytes)
    db.create_function("get_percentage", 2, util.get_percentage)
    db.create_function("divide", 2, util.divide)


def execute_to_df(sql, squeeze=False):
    if squeeze:
        return pd.read_sql(sql.format(sql), db).squeeze()
    else:
        return pd.read_sql(sql.format(sql), db)


def unload_df(name="df"):
    db.execute("drop table {}".format(name))
