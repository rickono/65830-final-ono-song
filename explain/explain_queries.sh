#!/bin/bash

out_folder=$1

# Define an array of query file names
query_files=("1.sql" "2.sql" "3.sql" "4.sql" "5.sql" "6.sql" "7.sql" "8.sql" "9.sql" 
    "10.sql" "11.sql" "12.sql" "13.sql" "14.sql" "15.sql" "16.sql" "17.sql"
    "18.sql" "19.sql" "20.sql" "21.sql" "22.sql")

# Database connection details
db_user="postgres"
db_name="tpchdb"

# Loop through the query files and run each query
for query_file in "${query_files[@]}"; do
    # Define output file name based on the query file name
    output_file="${query_file%.sql}_analyze.txt"
    echo $query_file

    # Run the query using psql and save the output to the corresponding file
    psql -U "$db_user" -d "$db_name" -a -f "../tpch/dbgen/explain_analyze_queries/$query_file" > "$out_folder/$output_file"

    # Check if the psql command was successful
    if [ $? -eq 0 ]; then
        echo "Query from $query_file executed successfully. Output saved to $output_file"
    else
        echo "Error executing query from $query_file"
    fi
done
