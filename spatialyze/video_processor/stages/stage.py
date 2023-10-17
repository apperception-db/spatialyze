import time
from typing import TYPE_CHECKING, Any, Generic, Iterable, Type, TypeVar

from bitarray import bitarray


def is_notebook() -> bool:
    if TYPE_CHECKING:
        return False
    try:
        shell = get_ipython().__class__.__name__
        if shell == "ZMQInteractiveShell":
            # Jupyter notebook or qtconsole
            return True
        elif shell == "TerminalInteractiveShell":
            # Terminal running IPython
            return False
        else:
            # Other type (?)
            return False
    except NameError:
        # Probably standard Python interpreter
        return False


if is_notebook():
    from tqdm.notebook import tqdm
else:
    from tqdm import tqdm

if TYPE_CHECKING:
    from ..payload import Payload


T = TypeVar("T")


class Stage(Generic[T]):
    progress: "bool" = False
    benchmark: "list[dict]"
    keeps: "list[tuple[int, int]]"

    def __new__(cls, *_, **__):
        obj = super(Stage, cls).__new__(cls)
        obj.benchmark = []
        obj.keeps = []
        return obj

    def _run(self, payload: "Payload") -> "tuple[bitarray | None, dict[str, list[T]] | None]":
        return payload.keep, payload.metadata

    def run(self, payload: "Payload") -> "tuple[bitarray | None, dict[str, list[T]] | None]":
        keep_before = payload.keep
        s = time.time()
        out = self._run(payload)
        e = time.time()
        keep_after = out[0]

        if keep_after is None:
            keep_after = keep_before
        _keep = keep_after & keep_before

        self.benchmark.append(
            {
                "name": payload.video.videofile,
                "runtime": e - s,
                "keep": (sum(_keep), sum(keep_before)),
            }
        )

        return out

    def __repr__(self) -> "str":
        return self.classname()

    @classmethod
    def classname(cls):
        return ".".join(_get_classnames(cls))

    _T = TypeVar("_T")

    @classmethod
    def get(cls: "Type[Stage[_T]]", d: "dict[str, list] | Payload") -> "list[_T] | None":
        if not isinstance(d, dict):
            d = d.metadata

        classname = cls.classname()
        for k, v in reversed(d.items()):
            if k.startswith(classname):
                return v
        return None

    @classmethod
    def encode_json(cls, o: "Any") -> "Any":
        return None

    @classmethod
    def enable_progress(cls, progress: "bool" = True):
        cls.progress = progress

    _T2 = TypeVar("_T2")

    @classmethod
    def tqdm(cls, iterable: "Iterable[_T2]", *args, **kwargs) -> "Iterable[_T2]":
        if Stage.progress:
            desc = cls.classname()
            if "desc" in kwargs:
                desc += f" {kwargs['desc']}"
            return tqdm(iterable, *args, **{**kwargs, "desc": desc})
        else:
            return iterable


def _get_classnames(cls: "type") -> "list[str]":
    if cls == Stage:
        return []
    return [*_get_classnames(cls.__base__), cls.__name__]
