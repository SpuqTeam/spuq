from __future__ import division
import numpy as np

from spuq.application.egsz.multi_vector import MultiVectorWithProjection
from spuq.application.egsz.multi_operator import MultiOperator, PreconditioningOperator
from spuq.application.egsz.coefficient_field import CoefficientField
from spuq.application.egsz.pcg import pcg
from spuq.stochastics.random_variable import NormalRV, UniformRV
from spuq.math_utils.multiindex import Multiindex
from spuq.linalg.vector import inner

from dolfin import Expression, FunctionSpace, UnitSquare, interpolate
from spuq.application.egsz.fem_discretisation import FEMPoisson
from spuq.fem.fenics.fenics_vector import FEniCSVector

a = [Expression('A*sin(pi*I*x[0]*x[1])', A=1, I=i, degree=2) for i in range(1, 4)]
rvs = [UniformRV(), NormalRV(mu=0.5)]
coeff_field = CoefficientField(a, rvs)

A = MultiOperator(coeff_field, FEMPoisson.assemble_operator)
mis = [Multiindex([0]),
       Multiindex([1]),
       Multiindex([0, 1]),
       Multiindex([0, 2])]
mesh = UnitSquare(4, 4)
fs = FunctionSpace(mesh, "CG", 1)
F = [interpolate(Expression("*".join(["x[0]"] * i)) , fs) for i in range(1, 5)]
vecs = [FEniCSVector(f) for f in F]

w = MultiVectorWithProjection()
for mi, vec in zip(mis, vecs):
    w[mi] = vec
v = A * w
P = PreconditioningOperator(a[0], FEMPoisson.assemble_solve_operator)
w2, zeta, numit = pcg(A, v, P, 0 * v)

print v
print w
print w2
print inner(w, w)
print inner(w - w2, w - w2)