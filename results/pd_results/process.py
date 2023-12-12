import json

files = ['sf1','sf2','sf5']
for file in files:
    results_dict = {}
    with open(f'{file}.txt', 'r') as results:
        for line in results:
            if 'loading' in line:
                loading_time = float(line.split()[-1])
                results_dict['load'] = loading_time
            elif 'Execution time' in line:
                continue
            elif 'Total' in line:
                results_dict['total'] = float(line.split()[-1])
            elif 'Average' in line:
                continue
            else:
                colon = line.index(':')
                print(line)
                close_b = line.index(']')
                query = line[:colon]
                q_result = line[colon+2:close_b+1]
                results_dict[query] = json.loads(q_result)
    print(results_dict)
    with open(f'{file}.json', 'w') as json_res:
        json.dump(results_dict, json_res)

