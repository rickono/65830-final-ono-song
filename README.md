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

Run `python3 time_query.py <file/to/query.sql>`. This runs the query several times and takes the minimum execution time.
