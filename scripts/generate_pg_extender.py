import os

with open('./install.sql', 'w') as f:
    f.write('\n'.join(map(
        lambda x: f'\i {x};',
        sorted(filter(
            lambda x: x.endswith('sql') and x != 'install.sql',
            os.listdir('.'),
        )),
    )))
