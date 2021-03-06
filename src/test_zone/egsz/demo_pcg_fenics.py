from __future__ import division
from itertools import count
import numpy as np

from spuq.application.egsz.multi_vector import MultiVectorWithProjection
from spuq.application.egsz.multi_operator import MultiOperator, PreconditioningOperator
from spuq.application.egsz.coefficient_field import ParametricCoefficientField
from spuq.application.egsz.pcg import pcg
from spuq.stochastics.random_variable import NormalRV, UniformRV
from spuq.math_utils.multiindex import Multiindex
from spuq.linalg.vector import inner
from spuq.linalg.operator import MultiplicationOperator

from dolfin import Expression, FunctionSpace, UnitSquare, interpolate, Constant
from spuq.application.egsz.fem_discretisation import FEMPoisson
from spuq.fem.fenics.fenics_vector import FEniCSVector

#def A(i, j):
#    return 1 / ((i + 1) ** 2 + (j + 1) ** 2)
#a = [Expression('A*cos(pi*I*x[0])*cos(pi*J*x[1])', A=A(i, j), I=i, J=j, degree=2) for i in range(3) for j in range(3)]
#rvs = [UniformRV()] * 8
#coeff_field = CoefficientField(a, rvs)
a0 = Constant("1.0")
a = (Expression('A*cos(pi*I*x[0])*cos(pi*I*x[1])', A=1 / i ** 2, I=i, degree=2) for i in count(1))
rvs = (UniformRV() for _ in count())
coeff_field = ParametricCoefficientField(func_func=a, rv_func=rvs, mean_func=a0)

pde = FEMPoisson()
A = MultiOperator(coeff_field, pde.assemble_operator)
mis = [Multiindex([0]),
       Multiindex([1]),
       Multiindex([0, 1]),
       Multiindex([0, 2])]
mesh = UnitSquare(4, 4)
fs = FunctionSpace(mesh, "CG", 1)
F = [interpolate(Expression("*".join(["x[0]"] * i)), fs) for i in range(1, 5)]
vecs = [FEniCSVector(f) for f in F]

w = MultiVectorWithProjection()
for mi, vec in zip(mis, vecs):
    w[mi] = vec
v = A * w
#P = MultiplicationOperator(1, vecs[0].basis)
P = PreconditioningOperator(a0, pde.assemble_solve_operator)
w2, zeta, numit = pcg(A, v, P, 0 * v)

print
print zeta, numit
print inner(w - w2, w - w2) / inner(w, w)
v2 = A * w2
print inner(v - v2, v - v2) / inner(v, v)
