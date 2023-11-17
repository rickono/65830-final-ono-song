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

def main(file):
    db_params = config()
    conn = psycopg2.connect(**db_params)
    cursor = conn.cursor()
    
    query = read_query_from_file(file)
    
    runtimes = []
    
    for _ in range(10):
        start_time = time.time()
        cursor.execute(query)
        end_time = time.time()
        runtimes.append(end_time - start_time)
    
    print(f"Minimum execution time after 10 rounds: {round(min(runtimes), 5)}")
    
    # Fetch the results
    results = cursor.fetchall()
    
    # Close the cursor and connection
    cursor.close()
    conn.close()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Please provide a sql query to run. Ex: python3 time_query.py test.sql")
        sys.exit()
    main(sys.argv[1])
