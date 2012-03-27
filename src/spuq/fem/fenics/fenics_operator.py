import numpy as np

import dolfin

from spuq.linalg.operator import Operator
from spuq.fem.fenics.fenics_basis import FEniCSBasis
from spuq.fem.fenics.fenics_vector import FEniCSVector
from spuq.utils.type_check import takes, anything

class FEniCSOperatorBase(Operator):
    @takes(anything, dolfin.Matrix, FEniCSBasis)
    def __init__(self, matrix, basis):
        self._matrix = matrix
        self._basis = basis

    @property
    def domain(self):
        return self._basis

    @property
    def codomain(self):
        return self._basis

class FEniCSOperator(FEniCSOperatorBase):
    @takes(anything, FEniCSVector)
    def apply(self, vec):
        new_vec = vec.copy()
        new_vec.coeffs = self._matrix * vec.coeffs
        return new_vec

class FEniCSSolveOperator(FEniCSOperatorBase):
    @takes(anything, FEniCSVector)
    def apply(self, vec):
        ind = 7
        a0 = vec.coeffs[ind]
        new_vec = vec.copy()
        new_vec.coeffs = dolfin.solve(self._matrix, new_vec.coeffs, vec.coeffs)
        print a0, vec.coeffs[ind], new_vec.coeffs[ind]
        print (vec - new_vec).coeffs.array()
        print (vec.coeffs - self._matrix * new_vec.coeffs).array()
        return new_vec

    @property
    def domain(self):
        return self._basis
    @property
    def codomain(self):
        return self._basis