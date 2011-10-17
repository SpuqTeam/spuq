from exceptions import TypeError, AttributeError
from spuq.utils.enum import Enum
#from spuq.fem import *
#from spuq.fem.fenics import *
from spuq.fem.fem_basis import FEMBasis
#from spuq.fem.fenics.fenics_vector import FEniCSVector
from spuq.fem.fenics.fenics_mesh import FEniCSMesh
from spuq.linalg.operator import MatrixOperator
from dolfin import FunctionSpace, FunctionSpaceBase, Function, \
                TestFunction, TrialFunction, Mesh, assemble, dx
from dolfin.fem.interpolation import interpolate
from dolfin.fem.projection import project

class FEniCSBasis(FEMBasis):
    '''wrapper for FEniCS/dolfin FunctionSpace'''
    
    PROJECTION = Enum('INTERPOLATION','L2PROJECTION')

    def __init__(self, mesh=None, family='CG', degree=1, functionspace=None):
        '''initialise discrete basis on mesh'''
        if functionspace is not None:
            assert(mesh is None)
            assert(isinstance(functionspace, FunctionSpaceBase))
            UFL = functionspace.ufl_element()
            family = UFL.family()
            degree = UFL.degree()
            mesh = functionspace.mesh()
            
        assert(mesh is not None)
        self.family = family
        self.degree = degree
        if isinstance(mesh, FEniCSMesh):
            self._mesh = mesh
            mesh = mesh.mesh
        elif isinstance(mesh, Mesh):
            self._mesh = FEniCSMesh(mesh)
        else:
            raise TypeError
        self._functionspace = FunctionSpace(mesh, family, degree)
        self._dim = self.__functionspace.dim()

    def refine(self, cells=None):
        '''refines mesh of basis uniformly or wrt cells, return new (FEniCSBasis,prolongate,restrict)'''
        import spuq.fem.fenics.fenics_vector   # NOTE: from ... import FEniCSVector does not work (cyclic dependencies require module imports)
        newmesh = self.mesh.refine(cells)
        newFB = FEniCSBasis(newmesh, self.family, self.degree)
        prolongate = lambda vec: spuq.fem.fenics.fenics_vector.FEniCSVector(function=project(vec.F, newFB.functionspace))
        restrict = lambda vec: spuq.fem.fenics.fenics_vector.FEniCSVector(function=project(vec.F, self.functionspace))
        return (newFB,prolongate,restrict)

    def project(self, vec, vecbasis=None, ptype=PROJECTION.INTERPOLATION):
        """Project vector vec to this basis.
        
            vec can either be a FEniCSVector (in which case vecbasis has to be None) or an array
            (in which case vecbasis has to be provided as dolfin FunctionSpace)."""
            
        import spuq.fem.fenics.fenics_vector   # NOTE: from ... import FEniCSVector does not work (cyclic dependencies require module imports)
        if ptype == self.PROJECTION.INTERPOLATION:
            T = interpolate
        elif ptype == self.PROJECTION.L2PROJECTION:
            T = project
        else:
            raise AttributeError
                
        if isinstance(vec, spuq.fem.fenics.fenics_vector.FEniCSVector):
            assert(vecbasis is None)
            F = T(vec.F, self.functionspace)
            newvec = spuq.fem.fenics.fenics_vector.FEniCSVector(F.vector(), F.function_space())
            return newvec
        else:
            F = T(Function(vecbasis, vec), self.functionspace)
            return (F.vector().array(), F.function_space())

    def interpolate(self, F):
        '''interpolate FEniCS Expression/Function on basis'''
        return interpolate(F, self.functionspace)

    @property
    def functionspace(self):
        return self._functionspace

    @property
    def mesh(self):
        return self._mesh
    
    @property
    def dim(self):
        return self._dim
    
    @property
    def gramian(self):
        """Returns the Gramian as a LinearOperator"""
        u = TrialFunction(self._functionspace)
        v = TestFunction(self._functionspace)
        a = (u*v)*dx
        A = assemble(a)
        return MatrixOperator(A.array())
