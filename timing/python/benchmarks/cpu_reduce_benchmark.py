import torch
import math
import numpy as np

from framework import Benchmark
from framework import utils


def make_size(dim, size_):
    if dim == 1:
        size = size_
    else:
        size = [0] * dim
        for i in range(dim):
            size[i] = int(math.pow(size_, 1.0 / float(dim)))
        size = tuple(size)
    return size


def make_tensor(size_, dtype, cont, dim, trans):
    size = make_size(dim, size_)
    if cont:
        tv = torch.rand(size).type(dtype)
    else:
        size = [size[0]] + list(size)
        size[dim] = 18
        size = tuple(size)
        tv = torch.rand(size).type(dtype)
        tv = tv.select(dim, 0)
    if trans:
        # tv = tv.transpose(dim -2, dim -1)
        tv = tv.transpose(0, 1)
    return tv


ALL_REDUCE_FUNCTIONS = [("mean", "mean"), ("prod", "prod"), ("sum", "sum")]


class NumpyReduceComparison(Benchmark):

    # NB: NumPy doesn't parallelize it's reductions
    args = utils.grid(
        {
            "dims": ((3, None), (3, 2), (3, 1), (3, 0)),
            "mag": (6,),
            "cont": (False, True),
            "trans": (False, True),
            "dtype": (torch.float,),
            "function": ALL_REDUCE_FUNCTIONS,
            "framework": ("Torch",),  # "NumPy"),
        }
    )

    user_counters = {"shape": 10 * " "}

    def _benchmark(self, state, arg):
        if arg.framework == "Torch":
            if arg.dims[1]:
                getattr(torch, arg.function[0])(
                    state.torch_tensor, arg.dims[1], out=state.output
                )
            else:
                getattr(torch, arg.function[0])(state.torch_tensor)
        else:
            if arg.dims[1]:
                getattr(np, arg.function[1])(
                    state.numpy_tensor, axis=arg.dims[1], out=state.output
                )
            else:
                getattr(np, arg.function[1])(state.numpy_tensor)

    def setupRun(self, state, arg):
        size_ = int(math.pow(10, arg.mag))
        tv = make_tensor(size_, arg.dtype, arg.cont, arg.dims[0], arg.trans)
        state.shape = str(tv.size())
        state.torch_tensor = tv
        state.output = None
        if arg.framework == "NumPy":
            if arg.dtype == torch.float:
                state.numpy_tensor = state.torch_tensor.numpy()
                assert state.numpy_tensor.dtype == np.float32
            if arg.dtype == torch.double:
                state.numpy_tensor = state.torch_tensor.numpy()
                assert state.numpy_tensor.dtype == np.float64
        self._benchmark(state, arg)

    def benchmark(self, state, arg):
        self._benchmark(state, arg)
