import psycopg2
from configparser import ConfigParser
import time
import sys

def config(filename='database.ini', section='postgresql'):
    parser = ConfigParser()
    parser.read(filename)

    db_params = {}
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            db_params[param[0]] = param[1]
    else:
        raise Exception(f'Section {section} not found in the {filename} file.')

    return db_params

def read_query_from_file(filename):
    with open(filename, 'r') as file:
        return file.read()

def main(start=1):
    f = open("results.txt", "w")
    
    for q in range(start, 23):
        db_params = config()
        conn = psycopg2.connect(**db_params)
        cursor = conn.cursor()
        file = f"tpch/dbgen/queries/{q}.sql"
        print(f"Running query: {file}")
        
        query = read_query_from_file(file)
        
        runtimes = []
        
        for r in range(5):
            start_time = time.time()
            cursor.execute(query)
            end_time = time.time()
            runtime = end_time - start_time
            runtimes.append(runtime)
            print(f"\tQ{q} round {r+1}: {runtime}")

        f.write(f"Q{q}: {round(min(runtimes), 5)}\n")
        print(f"Minimum execution Q{q}: {round(min(runtimes), 5)}\n")
        cursor.close()
        conn.close()
        
    
    
    # Close the cursor and connection

    f.close()

if __name__ == "__main__":
    args = sys.argv
    if len(args) == 3:
        if args[1] == '-s':
            main(start=int(args[2]))
    main()
