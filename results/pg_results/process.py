import json
files = ['sf1', 'sf2', 'sf5', 'sf10']

for file in files:
    query_results = {}
    with open(f'{file}.txt', 'r') as results:
        for line in results:
            colon = line.index(':')
            close_b = line.index(']')
            query = line[:colon]
            results = line[colon+2:close_b+1]
            query_num = int(query[1:])
            query_results[f'Q{query_num:02}'] = json.loads(results)
    results_dict = {}
    results_dict['queries'] = query_results
    with open(f'{file}.json', 'w') as json_res:
        json.dump(results_dict, json_res)
