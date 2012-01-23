import numpy as np

from spuq.utils.testing import *
from spuq.math_utils.multiindex import *


def test_init():
    # make sure we can create multiindices from integer arrays and
    # list, but not from floats
    Multiindex([0, 1, 3, 0])
    Multiindex(np.array([0, 1, 3, 0]))
    assert_raises(TypeError, Multiindex, [0, 1.3, 3, 0])
    assert_raises(TypeError, Multiindex, np.array([0, 1.3, 3, 0]))


def test_normalised():
    # make sure the result is normalised
    alpha = Multiindex(np.array([0, 1, 3, 0]))
    assert_array_equal(alpha.as_array, np.array([0, 1, 3]))


def test_copy():
    # make sure the result is copied
    arr = [0, 1, 3, 0]
    mi = Multiindex(arr)
    arr[2] = 4
    assert_equal(mi, Multiindex([0, 1, 3, 0]))

    arr = np.array([0, 1, 3, 0])
    mi = Multiindex(arr)
    arr[2] = 4
    assert_equal(mi, Multiindex([0, 1, 3, 0]))

    #assert_equal(mi.as_array, np.array([0, 1, 3]))


def test_len():
    alpha = Multiindex(np.array([0, 1, 3, 0]))
    assert_equal(len(alpha), 3)
    alpha = Multiindex(np.array([0, 1, 3, 0, 4, 0, 0]))
    assert_equal(len(alpha), 5)


def test_equality():
    alpha = Multiindex(np.array([0, 1, 3, 0]))
    beta = Multiindex(np.array([0, 1, 3, 0, 0, 0]))
    gamma = Multiindex(np.array([0, 1, 3, 0, 4, 0, 0]))

    assert_true(alpha == beta)
    assert_true(alpha != gamma)
    assert_true(not(alpha != beta))
    assert_true(not(alpha == gamma))


def test_hash():
    alpha = Multiindex(np.array([0, 1, 3, 0]))
    beta = Multiindex(np.array([0, 1, 3, 0, 0, 0]))
    assert_equal(hash(alpha), hash(beta))


def test_order():
    alpha = Multiindex(np.array([0, 1, 3, 0]))
    beta = Multiindex(np.array([0, 1, 3, 0, 4, 0]))
    assert_equal(alpha.order, 4)
    assert_equal(beta.order, 8)


def test_inc_dec():
    alpha_orig = Multiindex(np.array([0, 1, 3, 0]))
    alpha = Multiindex(np.array([0, 1, 3, 0]))
    beta = Multiindex(np.array([0, 1, 3, 0, 7, 0]))

    assert_equal(alpha.inc(4, 7), beta)
    assert_equal(alpha, alpha_orig)
    assert_equal(beta.dec(4, 7), alpha)
    assert_equal(alpha.dec(0, 1), None)
    assert_equal(alpha.dec(8, 1), None)