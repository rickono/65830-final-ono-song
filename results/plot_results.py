import json
import matplotlib.pyplot as plt

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
        print(pg_sf)
        max_pd = 0
        max_pg = 0
        for query in pd_sf:
            pd_perf = min(pd_sf[query])
            pg_perf = min(pg_sf[query])
            max_pg = max(max_pg, pg_perf)
            max_pd = max(max_pd, pd_perf)

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

    for i, sf in enumerate(min(pd_scale_factors, pg_scale_factors)):
        subp = ax[i // 2, i % 2]
        pd_sf = pd_results[f'sf{sf}']['queries']
        pg_sf = pg_results[f'sf{sf}']['queries']
        queries = []
        proportion = []
        for query in pd_sf:
            pd_perf = min(pd_sf[query])
            pg_perf = min(pg_sf[query])
            queries.append(query)
            proportion.append(pg_perf / pd_perf)

        subp.set_title(f'Scale factor {sf}')
        subp.set_xlabel('Query')
        subp.set_ylabel('Postgres runtime / Pandas runtime')
        subp.bar(queries, proportion)
        subp.axhline(y=1, color='red', linestyle='--')

    fig.suptitle('Postgres vs. Pandas runtimes', fontsize=16)
    plt.tight_layout()
    plt.show()


# pd_vs_pg_scatter()
pd_vs_pg_bar()
# pd_cache_warming_prop()
# pg_cache_warming_prop()
