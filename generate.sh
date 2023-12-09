if [ -z $1 ]; then
    echo "Usage: source generate.sh <scale_factor>"
    return
fi
ORIG=$PWD
# Go to dbgen and remove all existing tables
cd tpch/dbgen
rm *.tbl

# Generate the .tbl files with scale factor passed in
./dbgen -s $1

# Make sure all tables exist in the tpchdb database (make sure its running on port 5432)
psql -p5432 "tpchdb" -f $ORIG/create_tables.sql

# Insert each .tbl file into the database
tables=("lineitem" "partsupp" "orders" "customer" "supplier" "nation" "region" "part")

# Edit the tables to remove the trailing DELIMITER
for table in ${tables[@]}; do 
    sed -i.bak 's/.$//' $table.tbl
done 

rm *.bak

# Insert into database
for table in ${tables[@]}; do 
    psql -p5432 "tpchdb" -c "\COPY $table FROM '$table.tbl' DELIMITER '|';"
done

cd $ORIG

psql -p5432 "tpchdb" -f $ORIG/create_index.sql
psql -p5432 "tpchdb" -f $ORIG/vacuum.sql
