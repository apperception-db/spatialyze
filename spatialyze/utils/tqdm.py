from .is_notebook import is_notebook

if is_notebook():
    from tqdm.notebook import tqdm as _tqdm
else:
    from tqdm.notebook import tqdm as _tqdm


tqdm = _tqdm
