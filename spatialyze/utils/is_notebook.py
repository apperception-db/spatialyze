def is_notebook() -> bool:
    try:
        from IPython.core.getipython import get_ipython

        # if 'ZMQInteractiveShell' -> Jupyter notebook or qtconsole
        # if 'TerminalInteractiveShell' -> Terminal running IPython
        return get_ipython().__class__.__name__ == "ZMQInteractiveShell"
    except (NameError, ModuleNotFoundError):
        # NameError -> Probably standard Python interpreter
        # ModuleNotFoundError -> IPython not installed
        return False
