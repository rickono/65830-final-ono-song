folders = ['sf1', 'sf2', 'sf5', 'sf10']
queries = range(1, 23)


def indent_level(line):
    count = 0
    for char in line:
        if char == ' ':
            count += 1
        else:
            break
    return count


# def make_tree(q_plan):


for folder in folders:
    for query in queries:
        with open(f'{folder}/{query}.txt', 'r') as f:
            all = f.read()
            for l_no, line in enumerate(f):
                if line[0:3] != '---':
                    query_start = l_no

                indent = indent_level(line)
