#!/bin/bash

DATA_SET_PATH="tpch/dbgen"



for query_number in {1..22}
do
  # Run the Python script with the current query number
  python3 time_pandas.py --data_set="$DATA_SET_PATH" --queries="$query_number"
done

for query_number in {1..22}
do
  # Run the Python script with the current query number
  python3 time_dask.py --data_set="$DATA_SET_PATH" --queries="$query_number"
done
