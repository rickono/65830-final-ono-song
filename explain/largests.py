import math
import json

queries = range(1, 23)

for sf in ['sf1', 'sf2', 'sf5', 'sf10']:
    results = []
    for query in queries:
        with open(f'{sf}/costs/{query}_explain.txt', 'r') as f:
            m = 0
            for line in f:
                print(line)
                cost_i = line.find('cost=')
                cost = line[cost_i:]
                cost = cost[cost.index('=')+1:]
                cost = cost.split()[0]
                cost = cost.split('..')
                this_one = float(cost[1])
                print(this_one)
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

    with open(f'{sf}/costs/join_metrics_cost.json', 'w') as f:
        json.dump(metrics, f)
