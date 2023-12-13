#!/bin/bash

out_folder=$1

sfs=("sf1" "sf2" "sf5" "sf10")

# Define an array of query file names
query_files=("1.txt" "2.txt" "3.txt" "4.txt" "5.txt" "6.txt" "7.txt" "8.txt" "9.txt" 
    "10.txt" "11.txt" "12.txt" "13.txt" "14.txt" "15.txt" "16.txt" "17.txt"
    "18.txt" "19.txt" "20.txt" "21.txt" "22.txt")

for sf in "${sfs[@]}"; do
    for query_file in "${query_files[@]}"; do
        output_file="${query_file%.txt}_explain_cost.txt"
        grep -oE ".*cost=.*" $sf/$query_file > "$sf/costs/${output_file}"
    done
done

