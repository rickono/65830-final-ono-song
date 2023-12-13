import math
import json

queries = range(1, 23)

results = []
for query in queries:
    with open(f'{query}_explain.txt', 'r') as f:
        m = 0
        for line in f:
            rows_i = line.find('rows=')
            rows, width = line[rows_i:-2].split()
            rows = rows[rows.index('=')+1:]
            width = width[width.index('=')+1:]
            this_one = int(rows) * int(width)
            m = max(m, this_one)
    results.append(m)

results_no_zero = [r for r in results if r != 0]
n = len(results_no_zero)
metrics = {}

metrics['min'] = min(results_no_zero)
metrics['max'] = max(results_no_zero)
metrics['mean'] = sum(results_no_zero) / len(results_no_zero)
metrics['median'] = (sorted(results_no_zero)[math.floor(n / 2)] +
                     sorted(results_no_zero)[math.ceil(n / 2)]) / 2
metrics['all'] = results
metrics['no_zero'] = results_no_zero

with open('join_metrics.json', 'w') as f:
    json.dump(metrics, f)
