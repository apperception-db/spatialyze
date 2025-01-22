for q in [1, 2, 3, 4]:
    runtime = 0
    with open(f'eva-times-q{q}.txt', 'r') as f:
        for line in f.readlines():
            if line == "":
                continue
            rt = float(line.split()[-1])
            # print(rt)
            runtime += rt
    print('--', runtime)
