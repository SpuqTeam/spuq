import numpy as np

from spuq.utils.testing import *
from spuq.math_utils.multiindex_set import MultiindexSet
from spuq.stochastics.random_variable import NormalRV
from spuq.application.egsz.multi_vector import MultiVector
from spuq.application.egsz.multi_operator import MultiOperator
from spuq.application.egsz.coefficient_field import CoefficientField

try:
    from dolfin import UnitSquare, FunctionSpace, Function, Expression
    from spuq.fem.fenics.fenics_vector import FEniCSVector
    from spuq.fem.fenics.fenics_function import FEniCSExpression
    from spuq.application.egsz.sample_problems import SampleProblem
    from spuq.application.egsz.fem_discretisation import FEMPoisson
    HAVE_FENICS=True
except:
    HAVE_FENICS=False


@skip_if(not HAVE_FENICS, "Fenics not installed.")
def test_multioperator_fenics():
    # instantiate discretisation
    FEM = FEMPoisson()

    # set initial solution and set of active indices Lambda
    # MultiindexSet
    m = 2
    p = 3
    mi = MultiindexSet.createCompleteOrderSet(m, p)
    # init MultiVector
    mesh = UnitSquare(5,5)
    degree = 1
    V = FunctionSpace(mesh, "CG", degree)
    f = Function(V)
    initvector = FEniCSVector(function=f)
    wN1 = MultiVector(mi, initvector)
    # init test coefficient field
    F = list()
    for i, j in enumerate(mi.arr.tolist()):
        ex1 = Expression('x[0]*x[0]+A*sin(10.*x[1])', A=i)
        Dex1 = Expression(('2.*x[0]', 'A*10.*cos(10.*x[1])'), A=i)
        F.append(FEniCSExpression(fexpression=ex1, Dfexpression=Dex1))
    CF1 = CoefficientField(F, (NormalRV(),))
    MO1 = MultiOperator(FEM, CF1, 3)
    uN1 = MO1.apply(wN1)

    # create test case with identical 5x5 meshes (order 1 spaces)
    M2 = SampleProblem.createMeshes("square",("uniform",(5,5)),mi.count)
    V2 = FEniCSVector.create(M2, "CG", degree)
    wN2 = MultiVector(mi, V2)
    CF2 = SampleProblem.createCF("EF", 10)
    MO2 = MultiOperator(FEM, CF2, 3)
    uN2 = MO2.apply(wN2)

    # create test case with random meshes (order 1 spaces)
    M3 = SampleProblem.createMeshes("square",("random",(5,10),(5,10)),mi.count)
    V3 = FEniCSVector.create(M3, "CG", degree)
    wN3 = MultiVector(mi, V3)
    CF3 = SampleProblem.createCF("monomial", 10)
    MO3 = MultiOperator(FEM, CF3, 3)
    uN3 = MO3.apply(wN3)



from spuq.linalg.function import ConstFunction, SimpleFunction
from spuq.stochastics.random_variable import NormalRV, UniformRV

def test_multioperator():
    a = [ConstFunction(1), SimpleFunction(np.sin), SimpleFunction(np.cos)]
    a = [ConstFunction(1), SimpleFunction(np.sin)]
    rvs = [UniformRV(), NormalRV()]
    coeff_field = CoefficientField(a, rvs)
    assemble = lambda a: DiagonalOperator(a)
    A = MultiOperator(coeff_field, assemble)

    #A*mv

    


test_main()