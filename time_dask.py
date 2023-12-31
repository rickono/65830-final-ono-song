# adapted from: https://gist.github.com/UranusSeven/55817bf0f304cc24f5eb63b2f1c3e2cd
# to execute, run "python3 time_pandas.py --data_set 'tpch/dbgen'" from root directory

from tpch_headers import HEADERS
import argparse
import functools
import inspect
import json
import time
import re
from typing import Callable, List, Dict
import warnings

import pandas as pd
import dask.dataframe as dd
from dask.distributed import Client
pd.options.mode.chained_assignment = None


@functools.lru_cache(maxsize=128)
def load_lineitem(data_folder: str, use_dask=True, **storage_options) -> dd.DataFrame:
    data_path = data_folder + "/lineitem.tbl"

    # Use dask.dataframe.read_table instead of pd.read_table
    pkg = dd if use_dask else pd

    ddf = pkg.read_table(
        data_path,
        sep='|',
        names=HEADERS['lineitem'],
        storage_options=storage_options
    )

    ddf["L_SHIPDATE"] = dd.to_datetime(ddf.L_SHIPDATE, format="%Y-%m-%d")
    ddf["L_RECEIPTDATE"] = dd.to_datetime(ddf.L_RECEIPTDATE, format="%Y-%m-%d")
    ddf["L_COMMITDATE"] = dd.to_datetime(ddf.L_COMMITDATE, format="%Y-%m-%d")

    return ddf


@functools.lru_cache(maxsize=128)
def load_part(data_folder: str, use_dask=True, **storage_options) -> dd.DataFrame:
    data_path = data_folder + "/part.tbl"
    pkg = dd if use_dask else pd

    ddf = pkg.read_table(
        data_path,
        sep='|',
        names=HEADERS['part'],
        storage_options=storage_options
    )

    return ddf


@functools.lru_cache(maxsize=128)
def load_orders(data_folder: str, use_dask=True, **storage_options) -> dd.DataFrame:
    data_path = data_folder + "/orders.tbl"
    pkg = dd if use_dask else pd

    ddf = pkg.read_table(
        data_path,
        sep='|',
        names=HEADERS['orders'],
        storage_options=storage_options
    )

    ddf["O_ORDERDATE"] = dd.to_datetime(ddf.O_ORDERDATE, format="%Y-%m-%d")

    return ddf


@functools.lru_cache(maxsize=128)
def load_customer(data_folder: str, use_dask=True, **storage_options) -> dd.DataFrame:
    data_path = data_folder + "/customer.tbl"
    pkg = dd if use_dask else pd

    ddf = pkg.read_table(
        data_path,
        sep='|',
        names=HEADERS['customer'],
        storage_options=storage_options
    )

    return ddf


@functools.lru_cache(maxsize=128)
def load_nation(data_folder: str, use_dask=True, **storage_options) -> dd.DataFrame:
    data_path = data_folder + "/nation.tbl"
    pkg = dd if use_dask else pd

    ddf = pkg.read_table(
        data_path,
        sep='|',
        names=HEADERS['nation'],
        storage_options=storage_options
    )

    return ddf


@functools.lru_cache(maxsize=128)
def load_region(data_folder: str, use_dask=True, **storage_options) -> dd.DataFrame:
    data_path = data_folder + "/region.tbl"
    pkg = dd if use_dask else pd

    ddf = pkg.read_table(
        data_path,
        sep='|',
        names=HEADERS['region'],
        storage_options=storage_options
    )

    return ddf


@functools.lru_cache(maxsize=128)
def load_supplier(data_folder: str, use_dask=True,  **storage_options) -> dd.DataFrame:
    data_path = data_folder + "/supplier.tbl"
    pkg = dd if use_dask else pd

    ddf = pkg.read_table(
        data_path,
        sep='|',
        names=HEADERS['supplier'],
        storage_options=storage_options
    )

    return ddf


@functools.lru_cache(maxsize=128)
def load_partsupp(data_folder: str, use_dask=True, **storage_options) -> dd.DataFrame:
    data_path = data_folder + "/partsupp.tbl"
    pkg = dd if use_dask else pd

    ddf = pkg.read_table(
        data_path,
        sep='|',
        names=HEADERS['partsupp'],
        storage_options=storage_options
    )

    return ddf


def timethis(q: Callable):
    @functools.wraps(q)
    def wrapped(*args, **kwargs):
        runtimes = []

        for i in range(5):
            start_time = time.time()
            ans = q(*args, **kwargs)
            end_time = time.time()
            runtimes.append(end_time - start_time)
        # print(ans)
        print(runtimes)
        print("%s Execution time (s): %f" %
              (q.__name__.upper(), round(min(runtimes), 5)))

    return wrapped


_query_to_datasets: Dict[int, List[str]] = dict()


def collect_datasets(func: Callable):
    _query_to_datasets[int(func.__name__[1:])] = list(
        inspect.signature(func).parameters)
    return func


@timethis
@collect_datasets
def q01(lineitem: dd.DataFrame):
    date = pd.Timestamp("1998-09-02")
    lineitem_filtered = lineitem.loc[
        :,
        [
            "L_QUANTITY",
            "L_EXTENDEDPRICE",
            "L_DISCOUNT",
            "L_TAX",
            "L_RETURNFLAG",
            "L_LINESTATUS",
            "L_SHIPDATE",
            "L_ORDERKEY",
        ],
    ]
    sel = lineitem_filtered.L_SHIPDATE <= date
    lineitem_filtered = lineitem_filtered[sel]
    lineitem_filtered["AVG_QTY"] = lineitem_filtered.L_QUANTITY
    lineitem_filtered["AVG_PRICE"] = lineitem_filtered.L_EXTENDEDPRICE
    lineitem_filtered["DISC_PRICE"] = lineitem_filtered.L_EXTENDEDPRICE * (
        1 - lineitem_filtered.L_DISCOUNT
    )
    lineitem_filtered["CHARGE"] = (
        lineitem_filtered.L_EXTENDEDPRICE
        * (1 - lineitem_filtered.L_DISCOUNT)
        * (1 + lineitem_filtered.L_TAX)
    )
    # as_index=False not supported
    gb = lineitem_filtered.groupby(["L_RETURNFLAG", "L_LINESTATUS"])[
        [
            "L_QUANTITY",
            "L_EXTENDEDPRICE",
            "DISC_PRICE",
            "CHARGE",
            "AVG_QTY",
            "AVG_PRICE",
            "L_DISCOUNT",
            "L_ORDERKEY",
        ]
    ]
    total = gb.agg(
        {
            "L_QUANTITY": "sum",
            "L_EXTENDEDPRICE": "sum",
            "DISC_PRICE": "sum",
            "CHARGE": "sum",
            "AVG_QTY": "mean",
            "AVG_PRICE": "mean",
            "L_DISCOUNT": "mean",
            "L_ORDERKEY": "count",
        }
    )
    # Dask handles sorting during aggregation
    return total.compute()


@timethis
@collect_datasets
def q02(part, partsupp, supplier, nation, region):
    nation_filtered = nation.loc[:, ["N_NATIONKEY", "N_NAME", "N_REGIONKEY"]]
    region_filtered = region[(region["R_NAME"] == "EUROPE")]
    region_filtered = region_filtered.loc[:, ["R_REGIONKEY"]]

    r_n_merged = nation_filtered.merge(
        region_filtered, left_on="N_REGIONKEY", right_on="R_REGIONKEY", how="inner"
    )
    r_n_merged = r_n_merged.loc[:, ["N_NATIONKEY", "N_NAME"]]
    r_n_merged = r_n_merged.repartition(npartitions=1)
    supplier_filtered = supplier.loc[
        :,
        [
            "S_SUPPKEY",
            "S_NAME",
            "S_ADDRESS",
            "S_NATIONKEY",
            "S_PHONE",
            "S_ACCTBAL",
            "S_COMMENT",
        ],
    ]
    s_r_n_merged = r_n_merged.merge(
        supplier_filtered, left_on="N_NATIONKEY", right_on="S_NATIONKEY", how="inner"
    )
    s_r_n_merged = s_r_n_merged.loc[
        :,
        [
            "N_NAME",
            "S_SUPPKEY",
            "S_NAME",
            "S_ADDRESS",
            "S_PHONE",
            "S_ACCTBAL",
            "S_COMMENT",
        ],
    ]
    partsupp_filtered = partsupp.loc[:, [
        "PS_PARTKEY", "PS_SUPPKEY", "PS_SUPPLYCOST"]]
    ps_s_r_n_merged = s_r_n_merged.merge(
        partsupp_filtered, left_on="S_SUPPKEY", right_on="PS_SUPPKEY", how="inner"
    )
    ps_s_r_n_merged = ps_s_r_n_merged.loc[
        :,
        [
            "N_NAME",
            "S_NAME",
            "S_ADDRESS",
            "S_PHONE",
            "S_ACCTBAL",
            "S_COMMENT",
            "PS_PARTKEY",
            "PS_SUPPLYCOST",
        ],
    ]
    part_filtered = part.loc[:, ["P_PARTKEY", "P_MFGR", "P_SIZE", "P_TYPE"]]
    part_filtered = part_filtered[
        (part_filtered["P_SIZE"] == 15)
        & (part_filtered["P_TYPE"].str.endswith("BRASS"))
    ]
    part_filtered = part_filtered.loc[:, ["P_PARTKEY", "P_MFGR"]]
    merged_df = part_filtered.merge(
        ps_s_r_n_merged, left_on="P_PARTKEY", right_on="PS_PARTKEY", how="inner"
    )
    merged_df = merged_df.loc[
        :,
        [
            "N_NAME",
            "S_NAME",
            "S_ADDRESS",
            "S_PHONE",
            "S_ACCTBAL",
            "S_COMMENT",
            "PS_SUPPLYCOST",
            "P_PARTKEY",
            "P_MFGR",
        ],
    ]
    min_values = merged_df.groupby("P_PARTKEY", sort=False)[
        "PS_SUPPLYCOST"
    ].min().to_frame()
    min_values = min_values.repartition(npartitions=1)  # know it's small
    min_values.columns = ["MIN_SUPPLYCOST"]

    merged_df = merged_df.merge(
        min_values,
        left_on=["P_PARTKEY", "PS_SUPPLYCOST"],
        right_on=["P_PARTKEY", "MIN_SUPPLYCOST"],
        how="inner",
    ).compute()

    total = merged_df.loc[
        :,
        [
            "S_ACCTBAL",
            "S_NAME",
            "N_NAME",
            "P_PARTKEY",
            "P_MFGR",
            "S_ADDRESS",
            "S_PHONE",
            "S_COMMENT",
        ],
    ].compute()
    total = total.sort_values(
        by=["S_ACCTBAL", "N_NAME", "S_NAME", "P_PARTKEY"],
        ascending=[False, True, True, True],
    )
    return total


@timethis
@collect_datasets
def q03(lineitem, orders, customer):
    date = pd.Timestamp("1995-03-04")
    lineitem_filtered = lineitem.loc[
        :, ["L_ORDERKEY", "L_EXTENDEDPRICE", "L_DISCOUNT", "L_SHIPDATE"]
    ]
    orders_filtered = orders.loc[
        :, ["O_ORDERKEY", "O_CUSTKEY", "O_ORDERDATE", "O_SHIPPRIORITY"]
    ]
    customer_filtered = customer.loc[:, ["C_MKTSEGMENT", "C_CUSTKEY"]]
    lsel = lineitem_filtered.L_SHIPDATE > date
    osel = orders_filtered.O_ORDERDATE < date
    csel = customer_filtered.C_MKTSEGMENT == "HOUSEHOLD"
    flineitem = lineitem_filtered[lsel]
    forders = orders_filtered[osel]
    fcustomer = customer_filtered[csel]
    jn1 = fcustomer.merge(forders, left_on="C_CUSTKEY", right_on="O_CUSTKEY")
    jn2 = jn1.merge(flineitem, left_on="O_ORDERKEY", right_on="L_ORDERKEY")
    jn2["TMP"] = jn2.L_EXTENDEDPRICE * (1 - jn2.L_DISCOUNT)
    total = (
        jn2.groupby(
            ["L_ORDERKEY", "O_ORDERDATE", "O_SHIPPRIORITY"], sort=False
        )["TMP"]
        .sum()
        .to_frame()
        .sort_values(["TMP"], ascending=False)
        .reset_index()  # this might be expensive idk
    )
    res = total.loc[:, ["L_ORDERKEY", "TMP", "O_ORDERDATE", "O_SHIPPRIORITY"]]
    # head implicitly calls compute()
    return res.head(10)


@timethis
@collect_datasets
def q04(lineitem, orders):
    date1 = pd.Timestamp("1993-11-01")
    date2 = pd.Timestamp("1993-08-01")
    lsel = lineitem.L_COMMITDATE < lineitem.L_RECEIPTDATE
    osel = (orders.O_ORDERDATE < date1) & (orders.O_ORDERDATE >= date2)
    flineitem = lineitem[lsel]
    forders = orders[osel]
    jn = forders[forders["O_ORDERKEY"].isin(flineitem["L_ORDERKEY"].compute())]
    total = (
        jn.groupby("O_ORDERPRIORITY")["O_ORDERKEY"].count()
        # skip sort when Mars enables sort in groupby
        # .sort_values(["O_ORDERPRIORITY"])
    )
    return total.compute()


@timethis
@collect_datasets
def q05(lineitem, orders, customer, nation, region, supplier):
    date1 = pd.Timestamp("1996-01-01")
    date2 = pd.Timestamp("1997-01-01")
    rsel = region.R_NAME == "ASIA"
    osel = (orders.O_ORDERDATE >= date1) & (orders.O_ORDERDATE < date2)
    forders = orders[osel]
    fregion = region[rsel]
    jn1 = fregion.merge(nation, left_on="R_REGIONKEY", right_on="N_REGIONKEY")
    jn2 = jn1.merge(customer, left_on="N_NATIONKEY", right_on="C_NATIONKEY")
    jn3 = jn2.merge(forders, left_on="C_CUSTKEY", right_on="O_CUSTKEY")
    jn4 = jn3.merge(lineitem, left_on="O_ORDERKEY", right_on="L_ORDERKEY")
    jn5 = supplier.merge(
        jn4, left_on=["S_SUPPKEY", "S_NATIONKEY"], right_on=["L_SUPPKEY", "N_NATIONKEY"]
    )
    jn5["TMP"] = jn5.L_EXTENDEDPRICE * (1.0 - jn5.L_DISCOUNT)
    gb = jn5.groupby("N_NAME", sort=False)["TMP"].sum().to_frame()
    total = gb.sort_values("TMP", ascending=False)
    return total.compute()


@timethis
@collect_datasets
def q06(lineitem):
    date1 = pd.Timestamp("1996-01-01")
    date2 = pd.Timestamp("1997-01-01")
    lineitem_filtered = lineitem.loc[
        :, ["L_QUANTITY", "L_EXTENDEDPRICE", "L_DISCOUNT", "L_SHIPDATE"]
    ]
    sel = (
        (lineitem_filtered.L_SHIPDATE >= date1)
        & (lineitem_filtered.L_SHIPDATE < date2)
        & (lineitem_filtered.L_DISCOUNT >= 0.08)
        & (lineitem_filtered.L_DISCOUNT <= 0.1)
        & (lineitem_filtered.L_QUANTITY < 24)
    )
    flineitem = lineitem_filtered[sel]
    total = (flineitem.L_EXTENDEDPRICE * flineitem.L_DISCOUNT).sum()
    return total.compute()


@timethis
@collect_datasets
def q07(lineitem, supplier, orders, customer, nation):
    """This version is faster than q07_old. Keeping the old one for reference"""
    lineitem_filtered = lineitem[
        (lineitem["L_SHIPDATE"] >= pd.Timestamp("1995-01-01"))
        & (lineitem["L_SHIPDATE"] < pd.Timestamp("1997-01-01"))
    ]
    lineitem_filtered["L_YEAR"] = lineitem_filtered["L_SHIPDATE"].dt.year
    lineitem_filtered["VOLUME"] = lineitem_filtered["L_EXTENDEDPRICE"] * (
        1.0 - lineitem_filtered["L_DISCOUNT"]
    )
    lineitem_filtered = lineitem_filtered.loc[
        :, ["L_ORDERKEY", "L_SUPPKEY", "L_YEAR", "VOLUME"]
    ]
    supplier_filtered = supplier.loc[:, ["S_SUPPKEY", "S_NATIONKEY"]]
    orders_filtered = orders.loc[:, ["O_ORDERKEY", "O_CUSTKEY"]]
    customer_filtered = customer.loc[:, ["C_CUSTKEY", "C_NATIONKEY"]]
    n1 = nation[(nation["N_NAME"] == "FRANCE")
                ].loc[:, ["N_NATIONKEY", "N_NAME"]]
    n2 = nation[(nation["N_NAME"] == "GERMANY")
                ].loc[:, ["N_NATIONKEY", "N_NAME"]]

    # ----- do nation 1 -----
    N1_C = customer_filtered.merge(
        n1, left_on="C_NATIONKEY", right_on="N_NATIONKEY", how="inner"
    )
    N1_C = N1_C.drop(columns=["C_NATIONKEY", "N_NATIONKEY"]).rename(
        columns={"N_NAME": "CUST_NATION"}
    )
    N1_C_O = N1_C.merge(
        orders_filtered, left_on="C_CUSTKEY", right_on="O_CUSTKEY", how="inner"
    )
    N1_C_O = N1_C_O.drop(columns=["C_CUSTKEY", "O_CUSTKEY"])

    N2_S = supplier_filtered.merge(
        n2, left_on="S_NATIONKEY", right_on="N_NATIONKEY", how="inner"
    )
    N2_S = N2_S.drop(columns=["S_NATIONKEY", "N_NATIONKEY"]).rename(
        columns={"N_NAME": "SUPP_NATION"}
    )
    N2_S_L = N2_S.merge(
        lineitem_filtered, left_on="S_SUPPKEY", right_on="L_SUPPKEY", how="inner"
    )
    N2_S_L = N2_S_L.drop(columns=["S_SUPPKEY", "L_SUPPKEY"])

    total1 = N1_C_O.merge(
        N2_S_L, left_on="O_ORDERKEY", right_on="L_ORDERKEY", how="inner"
    )
    total1 = total1.drop(columns=["O_ORDERKEY", "L_ORDERKEY"])

    # ----- do nation 2 -----
    N2_C = customer_filtered.merge(
        n2, left_on="C_NATIONKEY", right_on="N_NATIONKEY", how="inner"
    )
    N2_C = N2_C.drop(columns=["C_NATIONKEY", "N_NATIONKEY"]).rename(
        columns={"N_NAME": "CUST_NATION"}
    )
    N2_C_O = N2_C.merge(
        orders_filtered, left_on="C_CUSTKEY", right_on="O_CUSTKEY", how="inner"
    )
    N2_C_O = N2_C_O.drop(columns=["C_CUSTKEY", "O_CUSTKEY"])

    N1_S = supplier_filtered.merge(
        n1, left_on="S_NATIONKEY", right_on="N_NATIONKEY", how="inner"
    )
    N1_S = N1_S.drop(columns=["S_NATIONKEY", "N_NATIONKEY"]).rename(
        columns={"N_NAME": "SUPP_NATION"}
    )
    N1_S_L = N1_S.merge(
        lineitem_filtered, left_on="S_SUPPKEY", right_on="L_SUPPKEY", how="inner"
    )
    N1_S_L = N1_S_L.drop(columns=["S_SUPPKEY", "L_SUPPKEY"])

    total2 = N2_C_O.merge(
        N1_S_L, left_on="O_ORDERKEY", right_on="L_ORDERKEY", how="inner"
    )
    total2 = total2.drop(columns=["O_ORDERKEY", "L_ORDERKEY"])

    # concat results
    total = dd.multi.concat([total1, total2])

    total = total.groupby(["SUPP_NATION", "CUST_NATION", "L_YEAR"]).agg(
        REVENUE=pd.NamedAgg(column="VOLUME", aggfunc="sum")
    )

    return total.compute()


@timethis
@collect_datasets
def q08(part, lineitem, supplier, orders, customer, nation, region):
    part_filtered = part[(part["P_TYPE"] == "ECONOMY ANODIZED STEEL")]
    part_filtered = part_filtered.loc[:, ["P_PARTKEY"]]
    lineitem_filtered = lineitem.loc[:, [
        "L_PARTKEY", "L_SUPPKEY", "L_ORDERKEY"]]
    lineitem_filtered["VOLUME"] = lineitem["L_EXTENDEDPRICE"] * (
        1.0 - lineitem["L_DISCOUNT"]
    )
    total = part_filtered.merge(
        lineitem_filtered, left_on="P_PARTKEY", right_on="L_PARTKEY", how="inner"
    )
    total = total.loc[:, ["L_SUPPKEY", "L_ORDERKEY", "VOLUME"]]
    supplier_filtered = supplier.loc[:, ["S_SUPPKEY", "S_NATIONKEY"]]
    total = total.merge(
        supplier_filtered, left_on="L_SUPPKEY", right_on="S_SUPPKEY", how="inner"
    )
    total = total.loc[:, ["L_ORDERKEY", "VOLUME", "S_NATIONKEY"]]
    orders_filtered = orders[
        (orders["O_ORDERDATE"] >= pd.Timestamp("1995-01-01"))
        & (orders["O_ORDERDATE"] < pd.Timestamp("1997-01-01"))
    ]
    orders_filtered["O_YEAR"] = orders_filtered["O_ORDERDATE"].dt.year
    orders_filtered = orders_filtered.loc[:, [
        "O_ORDERKEY", "O_CUSTKEY", "O_YEAR"]]
    total = total.merge(
        orders_filtered, left_on="L_ORDERKEY", right_on="O_ORDERKEY", how="inner"
    )
    total = total.loc[:, ["VOLUME", "S_NATIONKEY", "O_CUSTKEY", "O_YEAR"]]
    customer_filtered = customer.loc[:, ["C_CUSTKEY", "C_NATIONKEY"]]
    total = total.merge(
        customer_filtered, left_on="O_CUSTKEY", right_on="C_CUSTKEY", how="inner"
    )
    total = total.loc[:, ["VOLUME", "S_NATIONKEY", "O_YEAR", "C_NATIONKEY"]]
    n1_filtered = nation.loc[:, ["N_NATIONKEY", "N_REGIONKEY"]]
    n2_filtered = nation.loc[:, ["N_NATIONKEY", "N_NAME"]].rename(
        columns={"N_NAME": "NATION"}
    )
    total = total.merge(
        n1_filtered, left_on="C_NATIONKEY", right_on="N_NATIONKEY", how="inner"
    )
    total = total.loc[:, ["VOLUME", "S_NATIONKEY", "O_YEAR", "N_REGIONKEY"]]
    total = total.merge(
        n2_filtered, left_on="S_NATIONKEY", right_on="N_NATIONKEY", how="inner"
    )
    total = total.loc[:, ["VOLUME", "O_YEAR", "N_REGIONKEY", "NATION"]]
    region_filtered = region[(region["R_NAME"] == "AMERICA")]
    region_filtered = region_filtered.loc[:, ["R_REGIONKEY"]]
    total = total.merge(
        region_filtered, left_on="N_REGIONKEY", right_on="R_REGIONKEY", how="inner"
    )
    total = total.loc[:, ["VOLUME", "O_YEAR", "NATION"]]

    def udf(df):
        demonimator = df["VOLUME"].sum()
        df = df[df["NATION"] == "BRAZIL"]
        numerator = df["VOLUME"].sum()
        return numerator / demonimator

    # TODO: CHECK CORRECTNESS FROM GROUPBY->APPLY; MAY NEED TO USE META
    total = total.groupby("O_YEAR").apply(udf).to_frame().reset_index()
    total.columns = ["O_YEAR", "MKT_SHARE"]
    total = total.sort_values(by=["O_YEAR"], ascending=[True])
    return total.compute()


@timethis
@collect_datasets
def q09(lineitem, orders, part, nation, partsupp, supplier):
    psel = part.P_NAME.str.contains("ghost")
    fpart = part[psel]
    jn1 = lineitem.merge(fpart, left_on="L_PARTKEY", right_on="P_PARTKEY")
    jn2 = jn1.merge(supplier, left_on="L_SUPPKEY", right_on="S_SUPPKEY")
    jn3 = jn2.merge(nation, left_on="S_NATIONKEY", right_on="N_NATIONKEY")
    jn4 = partsupp.merge(
        jn3, left_on=["PS_PARTKEY", "PS_SUPPKEY"], right_on=["L_PARTKEY", "L_SUPPKEY"]
    )
    jn5 = jn4.merge(orders, left_on="L_ORDERKEY", right_on="O_ORDERKEY")
    jn5["TMP"] = jn5.L_EXTENDEDPRICE * (1 - jn5.L_DISCOUNT) - (
        (1 * jn5.PS_SUPPLYCOST) * jn5.L_QUANTITY
    )
    jn5["O_YEAR"] = jn5.O_ORDERDATE.dt.year
    gb = jn5.groupby(["N_NAME", "O_YEAR"], sort=False)["TMP"].sum().to_frame()
    total = gb.sort_values(["N_NAME", "O_YEAR"], ascending=[True, False])
    return total.compute()


@timethis
@collect_datasets
def q10(lineitem, orders, customer, nation):
    date1 = pd.Timestamp("1994-11-01")
    date2 = pd.Timestamp("1995-02-01")
    osel = (orders.O_ORDERDATE >= date1) & (orders.O_ORDERDATE < date2)
    lsel = lineitem.L_RETURNFLAG == "R"
    forders = orders[osel]
    flineitem = lineitem[lsel]
    jn1 = flineitem.merge(forders, left_on="L_ORDERKEY", right_on="O_ORDERKEY")
    jn2 = jn1.merge(customer, left_on="O_CUSTKEY", right_on="C_CUSTKEY")
    jn3 = jn2.merge(nation, left_on="C_NATIONKEY", right_on="N_NATIONKEY")
    jn3["TMP"] = jn3.L_EXTENDEDPRICE * (1.0 - jn3.L_DISCOUNT)
    gb = jn3.groupby(
        [
            "C_CUSTKEY",
            "C_NAME",
            "C_ACCTBAL",
            "C_PHONE",
            "N_NAME",
            "C_ADDRESS",
            "C_COMMENT",
        ],

        sort=False,
    )["TMP"].sum().to_frame()
    total = gb.sort_values("TMP", ascending=False)
    return total.head(20)


@timethis
@collect_datasets
def q11(partsupp, supplier, nation):
    partsupp_filtered = partsupp.loc[:, ["PS_PARTKEY", "PS_SUPPKEY"]]
    partsupp_filtered["TOTAL_COST"] = (
        partsupp["PS_SUPPLYCOST"] * partsupp["PS_AVAILQTY"]
    )
    supplier_filtered = supplier.loc[:, ["S_SUPPKEY", "S_NATIONKEY"]]
    ps_supp_merge = partsupp_filtered.merge(
        supplier_filtered, left_on="PS_SUPPKEY", right_on="S_SUPPKEY", how="inner"
    )
    ps_supp_merge = ps_supp_merge.loc[:, [
        "PS_PARTKEY", "S_NATIONKEY", "TOTAL_COST"]]
    nation_filtered = nation[(nation["N_NAME"] == "GERMANY")]
    nation_filtered = nation_filtered.loc[:, ["N_NATIONKEY"]]
    ps_supp_n_merge = ps_supp_merge.merge(
        nation_filtered, left_on="S_NATIONKEY", right_on="N_NATIONKEY", how="inner"
    )
    ps_supp_n_merge = ps_supp_n_merge.loc[:, ["PS_PARTKEY", "TOTAL_COST"]]
    sum_val = ps_supp_n_merge["TOTAL_COST"].sum() * 0.0001
    total = ps_supp_n_merge.groupby(["PS_PARTKEY"], sort=False).agg(
        VALUE=pd.NamedAgg(column="TOTAL_COST", aggfunc="sum")
    )
    total = total[total["VALUE"] > sum_val]
    total = total.sort_values("VALUE", ascending=False)
    return total.compute()


@timethis
@collect_datasets
def q12(lineitem, orders):
    date1 = pd.Timestamp("1994-01-01")
    date2 = pd.Timestamp("1995-01-01")
    sel = (
        (lineitem.L_RECEIPTDATE < date2)
        & (lineitem.L_COMMITDATE < date2)
        & (lineitem.L_SHIPDATE < date2)
        & (lineitem.L_SHIPDATE < lineitem.L_COMMITDATE)
        & (lineitem.L_COMMITDATE < lineitem.L_RECEIPTDATE)
        & (lineitem.L_RECEIPTDATE >= date1)
        & ((lineitem.L_SHIPMODE == "MAIL") | (lineitem.L_SHIPMODE == "SHIP"))
    )
    flineitem = lineitem[sel]
    jn = flineitem.merge(orders, left_on="L_ORDERKEY", right_on="O_ORDERKEY")

    # custom_g1 = dd.groupby.Aggregation(
    #     'custom_g1',
    #     chunk=lambda x: ((x == "1-URGENT") | (x == "2-HIGH")),
    #     agg=lambda x1: dd.from_array(x1.count(), columns=['custom_g1_count'], meta=('x', 'i8'))
    # )

    # custom_g2 = dd.groupby.Aggregation(
    #     'custom_g2',
    #     chunk=lambda x: ((x != "1-URGENT") & (x != "2-HIGH")),
    #     agg=lambda x1: dd.from_array(x1.count(), columns=['custom_g2_count'], meta=('x', 'i8'))
    # )

    # total = jn.groupby("L_SHIPMODE")["O_ORDERPRIORITY"].agg([custom_g1, custom_g2])

    # Define conditions
    condition_g1 = ((jn["O_ORDERPRIORITY"] == "1-URGENT")
                    | (jn["O_ORDERPRIORITY"] == "2-HIGH"))
    condition_g2 = ((jn["O_ORDERPRIORITY"] != "1-URGENT")
                    & (jn["O_ORDERPRIORITY"] != "2-HIGH"))

    # Apply conditions and calculate counts
    g1_count = jn[condition_g1].groupby(
        "L_SHIPMODE")["O_ORDERPRIORITY"].count().rename('custom_g1_count')
    g2_count = jn[condition_g2].groupby(
        "L_SHIPMODE")["O_ORDERPRIORITY"].count().rename('custom_g2_count')

    g1_count = g1_count.clear_divisions()
    g2_count = g2_count.clear_divisions()

    # Concatenate the results
    total = dd.concat([g1_count, g2_count], axis=1)
    total = total.reset_index()  # reset index to keep consistency with pandas
    # skip sort when groupby does sort already
    # total = total.sort_values("L_SHIPMODE")
    return total.compute()


@timethis
@collect_datasets
def q13(customer, orders):
    customer_filtered = customer.loc[:, ["C_CUSTKEY"]]
    orders_filtered = orders[
        ~orders["O_COMMENT"].str.contains(r"special[\S|\s]*requests")
    ]
    orders_filtered = orders_filtered.loc[:, ["O_ORDERKEY", "O_CUSTKEY"]]
    c_o_merged = customer_filtered.merge(
        orders_filtered, left_on="C_CUSTKEY", right_on="O_CUSTKEY", how="left"
    )
    c_o_merged = c_o_merged.loc[:, ["C_CUSTKEY", "O_ORDERKEY"]]
    count_df = c_o_merged.groupby(["C_CUSTKEY"], sort=False).agg(
        C_COUNT=pd.NamedAgg(column="O_ORDERKEY", aggfunc="count")
    )
    total = count_df.groupby(
        ["C_COUNT"], sort=False).size().to_frame().reset_index()
    total.columns = ["C_COUNT", "CUSTDIST"]
    total = total.sort_values(
        by=["CUSTDIST", "C_COUNT"], ascending=[False, False])
    return total.compute()


@timethis
@collect_datasets
def q14(lineitem, part):
    startDate = pd.Timestamp("1994-03-01")
    endDate = pd.Timestamp("1994-04-01")
    p_type_like = "PROMO"
    part_filtered = part.loc[:, ["P_PARTKEY", "P_TYPE"]]
    lineitem_filtered = lineitem.loc[
        :, ["L_EXTENDEDPRICE", "L_DISCOUNT", "L_SHIPDATE", "L_PARTKEY"]
    ]
    sel = (lineitem_filtered.L_SHIPDATE >= startDate) & (
        lineitem_filtered.L_SHIPDATE < endDate
    )
    flineitem = lineitem_filtered[sel]
    jn = flineitem.merge(
        part_filtered, left_on="L_PARTKEY", right_on="P_PARTKEY")
    jn["TMP"] = jn.L_EXTENDEDPRICE * (1.0 - jn.L_DISCOUNT)
    total = jn[jn.P_TYPE.str.startswith(
        p_type_like)].TMP.sum() * 100 / jn.TMP.sum()
    return total.compute()


@timethis
@collect_datasets
def q15(lineitem, supplier):
    lineitem_filtered = lineitem[
        (lineitem["L_SHIPDATE"] >= pd.Timestamp("1996-01-01"))
        & (
            lineitem["L_SHIPDATE"]
            < (pd.Timestamp("1996-01-01") + pd.DateOffset(months=3))
        )
    ]
    lineitem_filtered["REVENUE_PARTS"] = lineitem_filtered["L_EXTENDEDPRICE"] * (
        1.0 - lineitem_filtered["L_DISCOUNT"]
    )
    lineitem_filtered = lineitem_filtered.loc[:, [
        "L_SUPPKEY", "REVENUE_PARTS"]]
    revenue_table = (
        lineitem_filtered.groupby("L_SUPPKEY", sort=False)
        .agg(TOTAL_REVENUE=pd.NamedAgg(column="REVENUE_PARTS", aggfunc="sum"))
        .reset_index()
        .rename(columns={"L_SUPPKEY": "SUPPLIER_NO"})
    )
    max_revenue = revenue_table["TOTAL_REVENUE"].max()
    revenue_table = revenue_table[revenue_table["TOTAL_REVENUE"]
                                  == max_revenue]
    supplier_filtered = supplier.loc[:, [
        "S_SUPPKEY", "S_NAME", "S_ADDRESS", "S_PHONE"]]
    total = supplier_filtered.merge(
        revenue_table, left_on="S_SUPPKEY", right_on="SUPPLIER_NO", how="inner"
    )
    total = total.loc[
        :, ["S_SUPPKEY", "S_NAME", "S_ADDRESS", "S_PHONE", "TOTAL_REVENUE"]
    ]
    return total.compute()


@timethis
@collect_datasets
def q16(part, partsupp, supplier):
    part_filtered = part[
        (part["P_BRAND"] != "Brand#45")
        & (~part["P_TYPE"].str.contains("^MEDIUM POLISHED"))
        & part["P_SIZE"].isin([49, 14, 23, 45, 19, 3, 36, 9])
    ]
    part_filtered = part_filtered.loc[:, [
        "P_PARTKEY", "P_BRAND", "P_TYPE", "P_SIZE"]]
    partsupp_filtered = partsupp.loc[:, ["PS_PARTKEY", "PS_SUPPKEY"]]
    total = part_filtered.merge(
        partsupp_filtered, left_on="P_PARTKEY", right_on="PS_PARTKEY", how="inner"
    )
    total = total.loc[:, ["P_BRAND", "P_TYPE", "P_SIZE", "PS_SUPPKEY"]]
    supplier_filtered = supplier[
        supplier["S_COMMENT"].str.contains(
            r"Customer(\S|\s)*Complaints", regex=True)
    ]
    supplier_filtered = supplier_filtered.loc[:, [
        "S_SUPPKEY"]].drop_duplicates()
    # left merge to select only PS_SUPPKEY values not in supplier_filtered
    total = total.merge(
        supplier_filtered, left_on="PS_SUPPKEY", right_on="S_SUPPKEY", how="left"
    )
    total = total[total["S_SUPPKEY"].isna()]
    total = total.loc[:, ["P_BRAND", "P_TYPE", "P_SIZE", "PS_SUPPKEY"]]
    total = total.groupby(["P_BRAND", "P_TYPE", "P_SIZE"], sort=False)[
        "PS_SUPPKEY"
    ].nunique().to_frame().reset_index()
    total.columns = ["P_BRAND", "P_TYPE", "P_SIZE", "SUPPLIER_CNT"]
    total = total.sort_values(
        by=["SUPPLIER_CNT", "P_BRAND", "P_TYPE", "P_SIZE"],
        ascending=[False, True, True, True],
    )
    return total.compute()


@timethis
@collect_datasets
def q17(lineitem, part):
    left = lineitem.loc[:, ["L_PARTKEY", "L_QUANTITY", "L_EXTENDEDPRICE"]]
    right = part[((part["P_BRAND"] == "Brand#23") &
                  (part["P_CONTAINER"] == "MED BOX"))]
    right = right.loc[:, ["P_PARTKEY"]]
    line_part_merge = left.merge(
        right, left_on="L_PARTKEY", right_on="P_PARTKEY", how="inner"
    )
    line_part_merge = line_part_merge.loc[
        :, ["L_QUANTITY", "L_EXTENDEDPRICE", "P_PARTKEY"]
    ]
    lineitem_filtered = lineitem.loc[:, ["L_PARTKEY", "L_QUANTITY"]]
    lineitem_avg = lineitem_filtered.groupby(
        ["L_PARTKEY"], sort=False
    ).agg(avg=pd.NamedAgg(column="L_QUANTITY", aggfunc="mean")).reset_index()
    lineitem_avg["avg"] = 0.2 * lineitem_avg["avg"]
    lineitem_avg = lineitem_avg.loc[:, ["L_PARTKEY", "avg"]]
    total = line_part_merge.merge(
        lineitem_avg, left_on="P_PARTKEY", right_on="L_PARTKEY", how="inner"
    )
    total = total[total["L_QUANTITY"] < total["avg"]]
    total = pd.DataFrame(
        {"avg_yearly": [[total["L_EXTENDEDPRICE"].sum() / 7.0]]})
    return total


@timethis
@collect_datasets
def q18(lineitem, orders, customer):
    gb1 = lineitem.groupby("L_ORDERKEY", sort=False)[
        "L_QUANTITY"].sum().to_frame()
    fgb1 = gb1[gb1.L_QUANTITY > 300]
    jn1 = fgb1.merge(orders, left_on="L_ORDERKEY", right_on="O_ORDERKEY")
    jn2 = jn1.merge(customer, left_on="O_CUSTKEY", right_on="C_CUSTKEY")
    gb2 = jn2.groupby(
        ["C_NAME", "C_CUSTKEY", "O_ORDERKEY", "O_ORDERDATE", "O_TOTALPRICE"],

        sort=False,
    )["L_QUANTITY"].sum().to_frame()
    total = gb2.sort_values(
        ["O_TOTALPRICE", "O_ORDERDATE"], ascending=[False, True])
    return total.head(100)


@timethis
@collect_datasets
def q19(lineitem, part):
    Brand31 = "Brand#31"
    Brand43 = "Brand#43"
    SMBOX = "SM BOX"
    SMCASE = "SM CASE"
    SMPACK = "SM PACK"
    SMPKG = "SM PKG"
    MEDBAG = "MED BAG"
    MEDBOX = "MED BOX"
    MEDPACK = "MED PACK"
    MEDPKG = "MED PKG"
    LGBOX = "LG BOX"
    LGCASE = "LG CASE"
    LGPACK = "LG PACK"
    LGPKG = "LG PKG"
    DELIVERINPERSON = "DELIVER IN PERSON"
    AIR = "AIR"
    AIRREG = "AIRREG"
    lsel = (
        (
            ((lineitem.L_QUANTITY <= 36) & (lineitem.L_QUANTITY >= 26))
            | ((lineitem.L_QUANTITY <= 25) & (lineitem.L_QUANTITY >= 15))
            | ((lineitem.L_QUANTITY <= 14) & (lineitem.L_QUANTITY >= 4))
        )
        & (lineitem.L_SHIPINSTRUCT == DELIVERINPERSON)
        & ((lineitem.L_SHIPMODE == AIR) | (lineitem.L_SHIPMODE == AIRREG))
    )
    psel = (part.P_SIZE >= 1) & (
        (
            (part.P_SIZE <= 5)
            & (part.P_BRAND == Brand31)
            & (
                (part.P_CONTAINER == SMBOX)
                | (part.P_CONTAINER == SMCASE)
                | (part.P_CONTAINER == SMPACK)
                | (part.P_CONTAINER == SMPKG)
            )
        )
        | (
            (part.P_SIZE <= 10)
            & (part.P_BRAND == Brand43)
            & (
                (part.P_CONTAINER == MEDBAG)
                | (part.P_CONTAINER == MEDBOX)
                | (part.P_CONTAINER == MEDPACK)
                | (part.P_CONTAINER == MEDPKG)
            )
        )
        | (
            (part.P_SIZE <= 15)
            & (part.P_BRAND == Brand43)
            & (
                (part.P_CONTAINER == LGBOX)
                | (part.P_CONTAINER == LGCASE)
                | (part.P_CONTAINER == LGPACK)
                | (part.P_CONTAINER == LGPKG)
            )
        )
    )
    flineitem = lineitem[lsel]
    fpart = part[psel]
    jn = flineitem.merge(fpart, left_on="L_PARTKEY", right_on="P_PARTKEY")
    jnsel = (
        (jn.P_BRAND == Brand31)
        & (
            (jn.P_CONTAINER == SMBOX)
            | (jn.P_CONTAINER == SMCASE)
            | (jn.P_CONTAINER == SMPACK)
            | (jn.P_CONTAINER == SMPKG)
        )
        & (jn.L_QUANTITY >= 4)
        & (jn.L_QUANTITY <= 14)
        & (jn.P_SIZE <= 5)
        | (jn.P_BRAND == Brand43)
        & (
            (jn.P_CONTAINER == MEDBAG)
            | (jn.P_CONTAINER == MEDBOX)
            | (jn.P_CONTAINER == MEDPACK)
            | (jn.P_CONTAINER == MEDPKG)
        )
        & (jn.L_QUANTITY >= 15)
        & (jn.L_QUANTITY <= 25)
        & (jn.P_SIZE <= 10)
        | (jn.P_BRAND == Brand43)
        & (
            (jn.P_CONTAINER == LGBOX)
            | (jn.P_CONTAINER == LGCASE)
            | (jn.P_CONTAINER == LGPACK)
            | (jn.P_CONTAINER == LGPKG)
        )
        & (jn.L_QUANTITY >= 26)
        & (jn.L_QUANTITY <= 36)
        & (jn.P_SIZE <= 15)
    )
    jn = jn[jnsel]
    total = (jn.L_EXTENDEDPRICE * (1.0 - jn.L_DISCOUNT)).sum()
    return total.compute()


@timethis
@collect_datasets
def q20(lineitem, part, nation, partsupp, supplier):
    date1 = pd.Timestamp("1996-01-01")
    date2 = pd.Timestamp("1997-01-01")
    psel = part.P_NAME.str.startswith("azure")
    nsel = nation.N_NAME == "JORDAN"
    lsel = (lineitem.L_SHIPDATE >= date1) & (lineitem.L_SHIPDATE < date2)
    fpart = part[psel]
    fnation = nation[nsel]
    flineitem = lineitem[lsel]
    jn1 = fpart.merge(partsupp, left_on="P_PARTKEY", right_on="PS_PARTKEY")
    jn2 = jn1.merge(
        flineitem,
        left_on=["PS_PARTKEY", "PS_SUPPKEY"],
        right_on=["L_PARTKEY", "L_SUPPKEY"],
    )
    gb = jn2.groupby(
        ["PS_PARTKEY", "PS_SUPPKEY", "PS_AVAILQTY"], sort=False
    )["L_QUANTITY"].sum().reset_index()
    gbsel = gb.PS_AVAILQTY > (0.5 * gb.L_QUANTITY)
    fgb = gb[gbsel]
    jn3 = fgb.merge(supplier, left_on="PS_SUPPKEY", right_on="S_SUPPKEY")
    jn4 = fnation.merge(jn3, left_on="N_NATIONKEY", right_on="S_NATIONKEY")
    jn4 = jn4.loc[:, ["S_NAME", "S_ADDRESS"]]
    total = jn4.sort_values("S_NAME").drop_duplicates()
    return total.compute()


@timethis
@collect_datasets
# TODO: check for conflict in txn graph???
def q21(lineitem, orders, supplier, nation):
    lineitem_filtered = lineitem.loc[
        :, ["L_ORDERKEY", "L_SUPPKEY", "L_RECEIPTDATE", "L_COMMITDATE"]
    ]

    # Keep all rows that have another row in linetiem with the same orderkey and different suppkey
    lineitem_orderkeys = (
        lineitem_filtered.loc[:, ["L_ORDERKEY", "L_SUPPKEY"]]
        .groupby("L_ORDERKEY", sort=False)["L_SUPPKEY"]
        .nunique()
        .reset_index()
    )
    lineitem_orderkeys.columns = ["L_ORDERKEY", "nunique_col"]
    lineitem_orderkeys = lineitem_orderkeys[lineitem_orderkeys["nunique_col"] > 1]
    lineitem_orderkeys = lineitem_orderkeys.loc[:, ["L_ORDERKEY"]]

    # Keep all rows that have l_receiptdate > l_commitdate
    lineitem_filtered = lineitem_filtered[
        lineitem_filtered["L_RECEIPTDATE"] > lineitem_filtered["L_COMMITDATE"]
    ]
    lineitem_filtered = lineitem_filtered.loc[:, ["L_ORDERKEY", "L_SUPPKEY"]]

    # Merge Filter + Exists
    lineitem_filtered = lineitem_filtered.merge(
        lineitem_orderkeys, on="L_ORDERKEY", how="inner"
    )

    # Not Exists: Check the exists condition isn't still satisfied on the output.
    lineitem_orderkeys = lineitem_filtered.groupby(
        "L_ORDERKEY", sort=False
    )["L_SUPPKEY"].nunique().reset_index()
    lineitem_orderkeys.columns = ["L_ORDERKEY", "nunique_col"]
    lineitem_orderkeys = lineitem_orderkeys[lineitem_orderkeys["nunique_col"] == 1]
    lineitem_orderkeys = lineitem_orderkeys.loc[:, ["L_ORDERKEY"]]

    # Merge Filter + Not Exists
    lineitem_filtered = lineitem_filtered.merge(
        lineitem_orderkeys, on="L_ORDERKEY", how="inner"
    )

    orders_filtered = orders.loc[:, ["O_ORDERSTATUS", "O_ORDERKEY"]]
    orders_filtered = orders_filtered[orders_filtered["O_ORDERSTATUS"] == "F"]
    orders_filtered = orders_filtered.loc[:, ["O_ORDERKEY"]]
    total = lineitem_filtered.merge(
        orders_filtered, left_on="L_ORDERKEY", right_on="O_ORDERKEY", how="inner"
    )
    total = total.loc[:, ["L_SUPPKEY"]]

    supplier_filtered = supplier.loc[:, ["S_SUPPKEY", "S_NATIONKEY", "S_NAME"]]
    total = total.merge(
        supplier_filtered, left_on="L_SUPPKEY", right_on="S_SUPPKEY", how="inner"
    )
    total = total.loc[:, ["S_NATIONKEY", "S_NAME"]]
    nation_filtered = nation.loc[:, ["N_NAME", "N_NATIONKEY"]]
    nation_filtered = nation_filtered[nation_filtered["N_NAME"]
                                      == "SAUDI ARABIA"]
    total = total.merge(
        nation_filtered, left_on="S_NATIONKEY", right_on="N_NATIONKEY", how="inner"
    )
    total = total.loc[:, ["S_NAME"]]
    total = total.groupby("S_NAME", sort=False).size().to_frame().reset_index()
    total.columns = ["S_NAME", "NUMWAIT"]
    total = total.sort_values(
        by=["NUMWAIT", "S_NAME"], ascending=[False, True])
    return total.compute()


@timethis
@collect_datasets
def q22(customer, orders):
    customer_filtered = customer.loc[:, ["C_ACCTBAL", "C_CUSTKEY"]]
    customer_filtered["CNTRYCODE"] = customer["C_PHONE"].str.slice(0, 2)
    customer_filtered = customer_filtered[
        (customer["C_ACCTBAL"] > 0.00)
        & customer_filtered["CNTRYCODE"].isin(
            ["13", "31", "23", "29", "30", "18", "17"]
        )
    ]
    avg_value = customer_filtered["C_ACCTBAL"].mean()
    customer_filtered = customer_filtered[customer_filtered["C_ACCTBAL"] > avg_value]
    # Select only the keys that don't match by performing a left join and only selecting columns with an na value
    orders_filtered = orders.loc[:, ["O_CUSTKEY"]].drop_duplicates()
    customer_keys = customer_filtered.loc[:, ["C_CUSTKEY"]].drop_duplicates()
    customer_selected = customer_keys.merge(
        orders_filtered, left_on="C_CUSTKEY", right_on="O_CUSTKEY", how="left"
    )
    customer_selected = customer_selected[customer_selected["O_CUSTKEY"].isna(
    )]
    customer_selected = customer_selected.loc[:, ["C_CUSTKEY"]]
    customer_selected = customer_selected.merge(
        customer_filtered, on="C_CUSTKEY", how="inner"
    )
    customer_selected = customer_selected.loc[:, ["CNTRYCODE", "C_ACCTBAL"]]
    agg1 = customer_selected.groupby(
        ["CNTRYCODE"], sort=False).size().to_frame().reset_index()
    agg1.columns = ["CNTRYCODE", "NUMCUST"]
    agg2 = customer_selected.groupby(["CNTRYCODE"], sort=False).agg(
        TOTACCTBAL=pd.NamedAgg(column="C_ACCTBAL", aggfunc="sum")
    )
    total = agg1.merge(agg2, on="CNTRYCODE", how="inner")
    total = total.sort_values(by=["CNTRYCODE"], ascending=[True])
    return total.compute()


def cast_cols(
    root: str,
    datasets_to_load=list(HEADERS.keys()),
    verbose=False
):
    ddfs = []

    for dataset in datasets_to_load:
        ddf = globals()[f"load_{dataset}"](root, use_dask=False)

        if verbose:
            print(dataset + "\n-------------")
            print("Memory usage w/no casting: {}".format(ddf.memory_usage(deep=True)))

        # categorical casting
        pattern = r"^[A-MO-QS-Z]_(NATIONKEY|REGIONKEY)$"
        regex = re.compile(pattern)
        matches = [s for s in ddf.columns if regex.match(s)]

        if matches:
            print("Casting {} as categorical".format(', '.join(matches)))
            for match in matches:
                ddf[match] = ddf[match].astype("category")

        # numeric downcasting; compile ddf back into pandas dataframe
        ddf = ddf.apply(
            lambda x: pd.to_numeric(x, downcast="float") if x.dtype == 'float64'
            else pd.to_numeric(x, downcast="integer") if x.dtype == 'int64'
            else x,
            axis=0
        )

        if verbose:
            print("Memory usage w/ casting: {}".format(ddf.memory_usage(deep=True)))

        # convert back to dask dataframe
        ddfs.append(dd.from_pandas(ddf, chunksize=128))

    return ddfs


def run_queries(
    root: str,
    storage_options: Dict[str, str],
    queries: List[int],
    cast_types=False
):
    total_start = time.time()
    print("Start data loading")
    queries_to_args = dict()
    datasets_to_load = set()
    for query in queries:
        if cast_types:
            args = cast_cols(root, _query_to_datasets[query])
        else:
            args = [globals()[f"load_{dataset}"](
                root, **storage_options) for dataset in _query_to_datasets[query]]
            # for dataset in _query_to_datasets[query]:
            #     args.append(
            #         globals()[f"load_{dataset}"](root, **storage_options)
            #     )
        queries_to_args[query] = args
    print(f"Data loading time (s): {time.time() - total_start}")

    total_start = time.time()
    for query in queries:
        globals()[f"q{query:02}"](*queries_to_args[query])

    total_end = time.time()
    print(f"Total query execution time (s): {total_end - total_start}")
    print(
        f"Average total query execution time for 1 round: {(total_end - total_start) / 5}")


def main():
    warnings.filterwarnings("ignore")
    parser = argparse.ArgumentParser(description="tpch-queries")
    parser.add_argument(
        "--data_set",
        type=str,
        required=True,
        help="Path to the TPC-H dataset.",
    )
    parser.add_argument(
        "--storage_options",
        type=str,
        required=False,
        help="Path to the storage options json file.",
    )
    parser.add_argument(
        "--queries",
        type=int,
        nargs="+",
        required=False,
        help="Comma separated TPC-H queries to run.",
    )
    parser.add_argument(
        "--pyarrow-dtype",
        default=False,
        action="store_true",
        help="Use arrow dtype.",
    )
    parser.add_argument(
        "--lazy-copy",
        default=False,
        action="store_true",
        help="Use arrow dtype.",
    )

    parser.add_argument(
        "--cast",
        action="store_true",
        help="Downcast nation/region and numerics"
    )

    args = parser.parse_args()
    data_set = args.data_set
    cast_types = True if args.cast else False

    if args.pyarrow_dtype:
        print("Enable pyarrow dtype")
        pd.set_option("mode.dtype_backend", "pyarrow")

    if args.lazy_copy:
        print("Enable lazy copy")
        pd.set_option("mode.copy_on_write", True)

    # credentials to access the datasource.
    storage_options = {}
    if args.storage_options is not None:
        with open(args.storage_options, "r") as fp:
            storage_options = json.load(fp)
    print(f"Storage options: {storage_options}")

    queries = list(range(1, 23))
    if args.queries is not None:
        queries = args.queries
    print(f"Queries to run: {queries}")

    run_queries(
        data_set,
        storage_options=storage_options,
        queries=queries,
        cast_types=cast_types
    )


if __name__ == "__main__":
    print(f"Running TPC-H against pandas v{pd.__version__} with Dask")
    client = Client()  # start distributed scheduler locally.
    main()
