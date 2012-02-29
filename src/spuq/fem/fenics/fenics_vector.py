from dolfin import Function

from spuq.utils.type_check import takes, anything
from spuq.linalg.vector import Scalar
from spuq.linalg.basis import check_basis
from spuq.fem.fenics.fenics_basis import FEniCSBasis
from spuq.fem.fem_vector import FEMVector

class FEniCSVector(FEMVector):
    '''Wrapper for FEniCS/dolfin Function.

        Provides a FEniCSBasis and a FEniCSFunction (with the respective coefficient vector).'''

    @takes(anything, Function)
    def __init__(self, fefunc):
        '''Initialise with coefficient vector and Function'''
        self._fefunc = fefunc

    @property
    def basis(self):
        '''return FEniCSBasis'''
        return FEniCSBasis(self._fefunc.function_space())

    @property
    def coeffs(self):
        '''return FEniCS coefficient vector of Function'''
        return self._fefunc.vector()

    @coeffs.setter
    def coeffs(self, val):
        '''set FEniCS coefficient vector of Function'''
        self._fefunc.vector()[:] = val

    def array(self):
        '''return copy of coefficient vector as numpy array'''
        return self._fefunc.vector().array()

    def eval(self, x):
        return self._fefunc(x)

    def _create_copy(self, coeffs):
        # TODO: remove create_copy and retain only copy()
        new_fefunc = Function(self._fefunc.function_space(), coeffs)
        return self.__class__(new_fefunc)

    def __eq__(self, other):
        """Compare vectors for equality.

        Note that vectors are only considered equal when they have
        exactly the same type."""
#        print "************* EQ "
#        print self.coeffs.array()
#        print other.coeffs.array()
#        print (type(self) == type(other),
#                self.basis == other.basis,
#                self.coeffs.size() == other.coeffs.size())

        return (type(self) == type(other) and
                self.basis == other.basis and
                self.coeffs.size() == other.coeffs.size() and
                (self.coeffs == other.coeffs).all())

    @takes(anything)
    def __neg__(self):
        return self._create_copy(-self.coeffs)

    @takes(anything, "FEniCSVector")
    def __iadd__(self, other):
        check_basis(self.basis, other.basis)
        self.coeffs += other.coeffs
        return self

    @takes(anything, "FEniCSVector")
    def __isub__(self, other):
        check_basis(self.basis, other.basis)
        self.coeffs -= other.coeffs
        return self

    @takes(anything, Scalar)
    def __imul__(self, other):
        self.coeffs *= other
        return self
