import numpy as np

import theano
from   theano import tensor

#=========================================================================================
# Data type
#=========================================================================================

def asarray(x):
    return np.asarray(x, dtype=theano.config.floatX)

def zeros(shape):
    return np.zeros(shape, dtype=theano.config.floatX)

def shared(x, name=None):
    return theano.shared(np.asarray(x, theano.config.floatX), name=name)

def clipping_multiplier(norm, max_norm):
    """
    Multiplier for renormalizing a vector.

    """
    return tensor.switch(norm > max_norm, max_norm/norm, 1)

def choice(rng, a, size=1, replace=True, p=None):
    """
    A version of `numpy.random.RandomState.choice` that works with `float32`.

    """
    # Format and Verify input
    if isinstance(a, int):
        if a > 0:
            pop_size = a #population size
        else:
            raise ValueError("a must be greater than 0")
    else:
        a = np.array(a, ndmin=1, copy=0)
        if a.ndim != 1:
            raise ValueError("a must be 1-dimensional")
        pop_size = a.size
        if pop_size is 0:
            raise ValueError("a must be non-empty")

    if p is not None:
        p = np.array(p, dtype=p.dtype, ndmin=1, copy=0)
        if p.ndim != 1:
            raise ValueError("p must be 1-dimensional")
        if p.size != pop_size:
            raise ValueError("a and p must have same size")
        if np.any(p < 0):
            raise ValueError("probabilities are not non-negative")
        if not np.allclose(p.sum(), 1):
            raise ValueError("probabilities do not sum to 1")

    # Actual sampling
    if replace:
        if p is not None:
            cdf = p.cumsum()
            cdf /= cdf[-1]
            uniform_samples = rng.rand(size)
            idx = cdf.searchsorted(uniform_samples, side='right')
        else:
            idx = rng.randint(0, pop_size, size=size)
    else:
        if size > pop_size:
            raise ValueError(''.join(["Cannot take a larger sample than ",
                                      "population when 'replace=False'"]))

        if p is not None:
            if np.sum(p > 0) < size:
                raise ValueError("Fewer non-zero entries in p than size")
            n_uniq = 0
            p = p.copy()
            found = np.zeros(size, dtype=np.int)
            while n_uniq < size:
                x = rng.rand(size - n_uniq)
                if n_uniq > 0:
                    p[found[0:n_uniq]] = 0
                cdf = np.cumsum(p)
                cdf /= cdf[-1]
                new = cdf.searchsorted(x, side='right')
                new = np.unique(new)
                found[n_uniq:n_uniq + new.size] = new
                n_uniq += new.size
            idx = found
        else:
            idx = rng.permutation(pop_size)[:size]

    #Use samples as indices for a if a is array-like
    #if isinstance(a, int):
    #    print("HERE")
    assert len(idx) == 1
    return idx[0]
    #else:
    #    return a.take(idx)

#=========================================================================================
# Output activations
#=========================================================================================

def softmax(x, temp=1):
    return tensor.nnet.softmax(x/temp)

def softmax3(x, temp=1):
    """
    Softmax function for theano.tensor.tensor3.

    Parameters
    ----------

    x : theano.tensor.tensor3
        The probability distribution is over the last dimension of `x`.

    """
    sh = x.shape
    x  = x.reshape((sh[0]*sh[1], sh[2]))
    y  = tensor.nnet.softmax(x/temp)
    y  = y.reshape(sh)

    return y

def normalization(x):
    x2 = tensor.sqr(x) + 1e-6

    return x2/tensor.sum(x2, axis=-1, keepdims=True)

def normalization3(x):
    sh = x.shape
    x  = x.reshape((sh[0]*sh[1], sh[2]))
    y  = normalization(x)
    y  = y.reshape(sh)

    return y

#=========================================================================================
# Functions
#=========================================================================================
