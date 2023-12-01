from .is_notebook import is_notebook


if is_notebook():
    from tqdm.notebook import tqdm
else:
    from tqdm import tqdm