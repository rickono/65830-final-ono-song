from collections import defaultdict
import json
import math
import matplotlib.pyplot as plt
from matplotlib.colorbar import ColorbarBase
import matplotlib
import numpy as np

pd_results_dir = './pd_results'
pg_results_dir = './pg_results'

pg_result_files = ['sf1', 'sf2', 'sf5', 'sf10']
pd_result_files = ['sf1', 'sf2', 'sf5', 'sf10']
pg_scale_factors = [1, 2, 5, 10]
pd_scale_factors = [1, 2, 5, 10]


def load_postgres():
    results = {}
    for filename in pg_result_files:
        with open(f'{pg_results_dir}/{filename}.json', 'r') as file:
            contents = file.read()
            results[filename] = json.loads(contents)
    return results


def load_pandas():
    results = {}
    for filename in pd_result_files:
        with open(f'{pd_results_dir}/{filename}.json', 'r') as file:
            contents = file.read()
            results[filename] = json.loads(contents)
    return results


def averages():
    pd_data = load_pandas()
    pg_data = load_postgres()
    result = defaultdict(list)

    for sf in ['sf1', 'sf2', 'sf5', 'sf10']:
        pg_res = pg_data[sf]['queries']
        pd_res = pd_data[sf]['queries']
        total_sf_pg = 0
        total_sf_pd = 0
        for q in pg_res:
            total_sf_pg += min(pg_res[q])
            total_sf_pd += min(pd_res[q])
        result['pg'].append(total_sf_pg)
        result['pd'].append(total_sf_pd)
        result['pd_load'].append(total_sf_pd + pd_data[sf]['load'])
    print(result)


averages()


def which_bucket_joinsize(b):
    buckets = [128 * 10e3, 4 * 10e6, 16 * 10e6, float('inf')]
    for index, item in enumerate(buckets):
        if item > b:
            return index


def which_bucket_exectime(t):
    buckets = [0.5, 5, 10, float('inf')]
    for index, item in enumerate(buckets):
        if item > t:
            return index


def get_join_sizes(sf):
    with open(f'../explain/{sf}/costs/join_metrics.json', 'r') as f:
        return json.loads(f.read())['all']


def get_costs(sf):
    with open(f'../explain/{sf}/costs/join_metrics_cost.json', 'r') as f:
        return json.loads(f.read())['all']


# Plot the postgres queries, 1-5 for each query to show warm vs. cold cache
def pg_cache_warming():
    results = load_postgres()

    plt.figure(figsize=(10, 8))

    run = [1, 2, 3, 4, 5]

    for i, sf in enumerate(pg_scale_factors):
        plt.subplot(2, 2, i+1)
        for query, runtimes in results[f'sf{sf}']['queries'].items():
            plt.plot(run, runtimes, label=query)
        plt.title(f'Scale factor {sf}')
        plt.xlabel('Round number')
        plt.xticks(run)
        plt.ylabel('Runtime (s)')
    plt.tight_layout()
    plt.show()


# Plot the postgres queries, 1-5 by performance increase
def pg_cache_warming_prop():
    results = load_postgres()

    fig, ax = plt.subplots(nrows=2, ncols=2, figsize=(10, 8))
    run = [1, 2, 3, 4, 5]
    labels = []

    for i, sf in enumerate(pg_scale_factors):
        subp = ax[i // 2, i % 2]
        for query, runtimes in results[f'sf{sf}']['queries'].items():
            performance = [rt / runtimes[0] for rt in runtimes]
            subp.plot(run, performance, label=query)
            labels.append(query)
        subp.set_title(f'Scale factor {sf}')
        subp.set_xlabel('Round number')
        subp.set_xticks(run)
        subp.set_ylabel('Performance')

    fig.legend(loc='upper right',
               labels=sorted(set(labels), key=lambda x: int(x[1:])))
    fig.suptitle('Cache warming effect in Postgres', fontsize=16)
    plt.tight_layout()
    plt.show()


# Plot the pandas queries, 1-5 by performance increase
def pd_cache_warming_prop():
    results = load_pandas()

    fig, ax = plt.subplots(nrows=2, ncols=2, figsize=(10, 8))
    run = [1, 2, 3, 4, 5]
    labels = []

    for i, sf in enumerate(pd_scale_factors):
        subp = ax[i // 2, i % 2]
        for query, runtimes in results[f'sf{sf}']['queries'].items():
            performance = [rt / runtimes[0] for rt in runtimes]
            subp.plot(run, performance, label=query)
            labels.append(query)
        subp.set_title(f'Scale factor {sf}')
        subp.set_xlabel('Round number')
        subp.set_xticks(run)
        subp.set_ylabel('Performance')

    fig.legend(loc='upper right',
               labels=sorted(set(labels), key=lambda x: int(x[1:])))
    fig.suptitle('Cache warming effect in Pandas', fontsize=16)
    plt.tight_layout()
    plt.show()


def pd_vs_pg_scatter():
    pd_results = load_pandas()
    pg_results = load_postgres()

    fig, ax = plt.subplots(nrows=2, ncols=2, figsize=(10, 8))

    for i, sf in enumerate(min(pd_scale_factors, pg_scale_factors)):
        subp = ax[i // 2, i % 2]
        pd_sf = pd_results[f'sf{sf}']['queries']
        pg_sf = pg_results[f'sf{sf}']['queries']
        max_pd = 0
        max_pg = 0
        for query in pd_sf:
            pd_perf = min(pd_sf[query])
            pg_perf = min(pg_sf[query])
            max_pg = max(max_pg, pg_perf)
            max_pd = max(max_pd, pd_perf)
            est_cost = costs[int(query[1:])]

            subp.scatter(pd_perf, pg_perf)
            subp.set_title(f'Scale factor {sf}')
            subp.set_xlabel('Pandas runtime (s)')
            subp.set_ylabel('Postgres runtime (s)')
        subp.plot([0, min(max_pd, max_pg)], [0, min(max_pd, max_pg)])

    fig.suptitle('Postgres vs. Pandas runtimes', fontsize=16)
    plt.tight_layout()
    plt.show()


def pd_vs_pg_bar():
    pd_results = load_pandas()
    pg_results = load_postgres()

    fig, ax = plt.subplots(nrows=2, ncols=2, figsize=(10, 8))
    bucket_colors = [(0.594508, 0.175701, 0.501241), (0.828886, 0.262229, 0.430644),
                     (0.973381, 0.46152, 0.361965), (0.997341, 0.733545, 0.505167)]

    for i, sf in enumerate(min(pd_scale_factors, pg_scale_factors)):
        costs = get_costs(f'sf{sf}')
        subp = ax[i // 2, i % 2]
        pd_sf = pd_results[f'sf{sf}']['queries']
        pg_sf = pg_results[f'sf{sf}']['queries']
        queries = []
        proportion = []
        pg_perfs = []
        for query in pd_sf:
            pd_perf = min(pd_sf[query])
            pg_perf = min(pg_sf[query])
            pg_perfs.append(pg_perf)
            queries.append(query)
            proportion.append(pg_perf / pd_perf)
        cost = np.array(costs)
        cost = (cost - np.min(cost)) / (np.max(cost) - np.min(cost))
        pg_perfs = np.array(pg_perfs)
        pg_perfs = (pg_perfs - np.min(pg_perfs)) / (np.max(pg_perfs) -
                                                    np.min(pg_perfs))
        guesses = [abs(cost - r)
                   for cost, r in zip(cost, pg_perfs)]
        print(guesses, proportion)
        print(np.corrcoef(np.array(guesses), np.array(proportion))[0, 1])

        join_sizes = get_join_sizes(f'sf{sf}')
        buckets = [which_bucket_joinsize(s) for s in join_sizes]
        colors = [bucket_colors[b] for b in buckets]

        proportion = [math.log2(x) for x in proportion]
        # print(f'corcoef={np.corrcoef(np.array(proportion), join_sizes)[0, 1]}')

        subp.set_title(f'Scale factor {sf}')
        subp.set_xlabel('Query')
        subp.set_ylabel('log2(Postgres runtime / Pandas runtime)')
        subp.bar(queries, proportion, color=colors)
        subp.set_xticks([q for i, q in enumerate(queries) if i % 2 == 0])

    fig.suptitle('Postgres vs. Pandas runtimes', fontsize=16)
    plt.tight_layout()
    plt.show()


pd_vs_pg_bar()


def pd_vs_pg_bar_cost():
    pd_results = load_pandas()
    pg_results = load_postgres()

    fig, ax = plt.subplots(nrows=2, ncols=2, figsize=(10, 8))
    cmap = plt.get_cmap('viridis')

    for i, sf in enumerate(min(pd_scale_factors, pg_scale_factors)):
        subp = ax[i // 2, i % 2]
        pd_sf = pd_results[f'sf{sf}']['queries']
        pg_sf = pg_results[f'sf{sf}']['queries']
        queries = []
        proportion = []
        load_time = pd_results[f'sf{sf}']['load']
        for query in pd_sf:
            pd_perf = min(pd_sf[query])
            pg_perf = min(pg_sf[query])
            queries.append(query)
            proportion.append(pg_perf / pd_perf)

        proportion = [math.log2(x) for x in proportion]

        costs = get_costs(f'sf{sf}')
        print(f'corcoef={np.corrcoef(np.array(proportion), costs)[0, 1]}')
        max_cost = max(costs)
        min_cost = min(costs)

        colors = [cmap((c - min_cost) / (max_cost - min_cost)) for c in costs]

        subp.set_title(f'Scale factor {sf}')
        subp.set_xlabel('Query')
        subp.set_ylabel('log2(Postgres runtime / Pandas runtime)')
        subp.bar(queries, proportion)
        subp.set_xticks([q for i, q in enumerate(queries) if i % 2 == 0])

    # cbar_ax = fig.add_axes([0.95, 0.1, 0.01, 0.1])
    # colorbar = ColorbarBase(ax=cbar_ax, cmap=cmap,
    #                         norm=matplotlib.colors.Normalize(vmin=min_cost,
    #                                                          vmax=max_cost))
    # colorbar.set_label('Cost', rotation=90)
    # colorbar.set_ticks([min_cost, max_cost])
    # colorbar.set_ticklabels(['Min Cost', 'Max Cost'])

    plt.tight_layout()
    plt.show()


def pg_vs_sf(prop=False, log=False, pandas=False):
    load = load_pandas if pandas else load_postgres
    results = load()

    results_parsed = defaultdict(list)

    sfs = pd_scale_factors if pandas else pg_scale_factors
    for i, sf in enumerate(sfs):
        for query, runtimes in results[f'sf{sf}']['queries'].items():
            if prop:
                if i == 0:
                    results_parsed[query].append(min(runtimes))
                    results_parsed[query].append(1)
                else:
                    min_rt = min(runtimes)
                    prop_val = min_rt / results_parsed[query][0]
                    results_parsed[query].append(prop_val)
            else:
                results_parsed[query].append(min(runtimes))

    for query, runtimes in results_parsed.items():
        print(runtimes)
        if prop:
            runtimes = runtimes[1:]
        if log:
            runtimes = [math.log2(r) for r in runtimes]
        plt.plot(pg_scale_factors, runtimes)

    n = 'Pandas' if pandas else 'Postgres'
    plt.title(f'{n} performance vs. scale factor')
    plt.xlabel('Scale factor')
    plt.xticks(pg_scale_factors)
    plt.ylabel('Proportional runtime increase')
    yticklocs = [0, 2, 4, 6, 8, 10]
    plt.yticks(yticklocs, [f'{y}^2' for y in yticklocs])
    plt.legend(loc='upper right',
               labels=results_parsed.keys())
    plt.show()


def pd_vs_pg_bar_cost_omit(minrt):
    pd_results = load_pandas()
    pg_results = load_postgres()

    # fig, ax = plt.subplots(nrows=1, ncols=1, figsize=(10, 8))

    sf = 10
    pd_sf = pd_results[f'sf{sf}']['queries']
    pg_sf = pg_results[f'sf{sf}']['queries']
    queries = []
    proportion = []
    for query in pd_sf:
        pd_perf = min(pd_sf[query])
        pg_perf = min(pg_sf[query])
        if min(pd_perf, pg_perf) < minrt:
            continue
        queries.append(query)
        proportion.append(pg_perf / pd_perf)

    proportion = [math.log2(x) for x in proportion]

    plt.title(f'Scale factor {sf}, long queries (>10s)')
    plt.xlabel('Query')
    plt.ylabel('log2(Postgres runtime / Pandas runtime)')
    plt.bar(queries, proportion)
    # subp.set_xticks([q for i, q in enumerate(queries) if i % 2 == 0])

    plt.tight_layout()
    plt.show()


def pd_vs_pg_bar_colorby_time():
    pd_results = load_pandas()
    pg_results = load_postgres()

    fig, ax = plt.subplots(nrows=2, ncols=2, figsize=(10, 8))
    bucket_colors = [(0.594508, 0.175701, 0.501241), (0.828886, 0.262229, 0.430644),
                     (0.973381, 0.46152, 0.361965), (0.997341, 0.733545, 0.505167)]

    for i, sf in enumerate(min(pd_scale_factors, pg_scale_factors)):
        subp = ax[i // 2, i % 2]
        pd_sf = pd_results[f'sf{sf}']['queries']
        pg_sf = pg_results[f'sf{sf}']['queries']
        queries = []
        proportion = []
        colors = []
        for query in pd_sf:
            pd_perf = min(pd_sf[query])
            pg_perf = min(pg_sf[query])
            queries.append(query)
            colors.append(bucket_colors[
                which_bucket_exectime(min(pd_perf, pg_perf))])
            proportion.append(pg_perf / pd_perf)

        proportion = [math.log2(x) for x in proportion]
        subp.set_title(f'Postgres vs. Pandas runtime, SF=10')
        subp.set_xlabel('Query')
        subp.set_ylabel('log2(Postgres runtime / Pandas runtime)')
        subp.bar(queries, proportion, color=colors)
        subp.set_xticks([q for i, q in enumerate(queries) if i % 2 == 0])

    fig.suptitle('Postgres vs. Pandas runtimes', fontsize=16)
    plt.tight_layout()
    plt.show()


# pg_vs_sf()
# pg_vs_sf(prop=True)
# pd_vs_pg_bar_cost_omit(10)
# pd_vs_pg_bar_colorby_time()
# pg_vs_sf(prop=True, log=True, pandas=True)
# pd_vs_pg_scatter()
# pd_vs_pg_bar()
pd_vs_pg_bar_cost()
# pd_cache_warming_prop()
# pg_cache_warming_prop()
# pg_cache_warming_prop()
