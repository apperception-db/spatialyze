def is_notebook() -> bool:
    try:
        from IPython.core.getipython import get_ipython

        shell = get_ipython().__class__.__name__
        if shell == "ZMQInteractiveShell":
            # Jupyter notebook or qtconsole
            return True
        else:
            # shell == 'TerminalInteractiveShell' -> Terminal running IPython
            return False
    except NameError:
        # Probably standard Python interpreter
        return False
