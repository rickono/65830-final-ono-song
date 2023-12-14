# 6.5830 Database Systems Final Project

## Environment Set Up

Set up a virtual environment (using `python3 -m venv venv` or similar) and activate it.

Run `pip3 install -r requirements.txt`.

## Timing SQL queries

Prerequisites:

- Postgres and psql
- A database named "tpchdb" running on port 5432

### Seeding the database

1. Compile the TPC-H `dbgen` tool by running `make` in `tpch/dbgen`.
2. Run `source generate.sh <scale_factor>` to generate data. This will use `dbgen` to generate `.tbl` files that are copied into the Postgres database running on your machine.

### Timing queries

To time Postgres, run `python3 time_query.py <file/to/query.sql>` from the root directory. This runs the query several times and takes the minimum execution time. Note that `generate.sh` currently stores the `.tbl` files in the folder `tpch/dbgen`.

To time pandas, run `python3 time_pandas.py --data_set <file/to/query.sql>`. Note that several arguments are available:
- To run a particular query or list of queries, you can use the `--queries` argument with a comma separated string of the queries of interest (e.g. `--queries '2,5'`. Not specifying will run all 22 queries.
- To downcast nationkey and regionkey and columns with integer/float dtypes, add the `--cast` argument.

## Results and plots
Query plans from our runs at SF=5 and Sf=10 can be found in the `explain/` folder. Plots can be found in the `results/` folder. Each have generating scripts that you run to visualize results should you execute queries locally.
