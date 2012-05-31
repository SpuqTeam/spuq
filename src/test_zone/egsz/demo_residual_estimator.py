from __future__ import division
import logging
import os
from math import sqrt

from spuq.application.egsz.adaptive_solver import AdaptiveSolver
from spuq.application.egsz.multi_operator import MultiOperator
from spuq.application.egsz.sample_problems import SampleProblem
from spuq.application.egsz.mc_error_sampling import sample_error_mc
from spuq.math_utils.multiindex import Multiindex
from spuq.math_utils.multiindex_set import MultiindexSet
from spuq.utils.plot.plotter import Plotter
try:
    from dolfin import (Function, FunctionSpace, Mesh, Constant, UnitSquare, plot, interactive, set_log_level, set_log_active)
    from spuq.application.egsz.fem_discretisation import FEMPoisson
    from spuq.fem.fenics.fenics_vector import FEniCSVector
except:
    import traceback
    print traceback.format_exc()
    print "FEniCS has to be available"
    os.sys.exit(1)

# ------------------------------------------------------------

# setup logging
# log level and format configuration
LOG_LEVEL = logging.INFO
log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
logging.basicConfig(filename=__file__[:-2] + 'log', level=LOG_LEVEL,
                    format=log_format)

# FEniCS logging
from dolfin import (set_log_level, set_log_active, INFO, DEBUG, WARNING)
set_log_active(True)
set_log_level(WARNING)
fenics_logger = logging.getLogger("FFC")
fenics_logger.setLevel(logging.WARNING)
fenics_logger = logging.getLogger("UFL")
fenics_logger.setLevel(logging.WARNING)

# module logger
logger = logging.getLogger(__name__)
logging.getLogger("spuq.application.egsz.multi_operator").disabled = True
#logging.getLogger("spuq.application.egsz.marking").setLevel(logging.INFO)
# add console logging output
ch = logging.StreamHandler()
ch.setLevel(LOG_LEVEL)
ch.setFormatter(logging.Formatter(log_format))
logger.addHandler(ch)
logging.getLogger("spuq").addHandler(ch)

# determine path of this module
path = os.path.dirname(__file__)
lshape_xml = os.path.join(path, 'lshape.xml')

# ------------------------------------------------------------

# utility functions 

# setup initial multivector
def setup_vec(mesh):
    fs = FunctionSpace(mesh, "CG", 1)
    vec = FEniCSVector(Function(fs))
    return vec


# ============================================================
# PART A: Simulation Options
# ============================================================

# flag for residual graph plotting
PLOT_RESIDUAL = True

# flag for final solution plotting
PLOT_MESHES = False

# flag for final solution export
SAVE_SOLUTION = '' #"results/demo-residual"

# flags for residual, projection, new mi refinement 
REFINEMENT = {"RES":True, "PROJ":True, "MI":True}
UNIFORM_REFINEMENT = False

# MC error sampling
MC_RUNS = 1
MC_N = 3
MC_HMAX = 1 / 10


# ============================================================
# PART B: Problem Setup
# ============================================================

# define source term
#f = Expression("10.*exp(-(pow(x[0] - 0.6, 2) + pow(x[1] - 0.4, 2)) / 0.02)", degree=3)
f = Constant("1.0")

# define initial multiindices
mis = [Multiindex(mis) for mis in MultiindexSet.createCompleteOrderSet(2, 1)]

# debug---
#mis = (Multiindex(),)
# ---debug

# setup meshes 
mesh0 = Mesh(lshape_xml)
#mesh0 = UnitSquare(4, 4)
#meshes = SampleProblem.setupMeshes(mesh0, len(mis), {"refine":10, "random":(0.4, 0.3)})
meshes = SampleProblem.setupMeshes(mesh0, len(mis), {"refine":0})

# debug---
#from dolfin import refine
#meshes[1] = refine(meshes[1])
# ---debug

w = SampleProblem.setupMultiVector(dict([(mu, m) for mu, m in zip(mis, meshes)]), setup_vec)
logger.info("active indices of w after initialisation: %s", w.active_indices())

# ---debug
#from spuq.application.egsz.multi_vector import MultiVectorWithProjection
#if SAVE_SOLUTION != "":
#    w.pickle(SAVE_SOLUTION)
#u = MultiVectorWithProjection.from_pickle(SAVE_SOLUTION, FEniCSVector)
#import sys
#sys.exit()
# ---debug

# define coefficient field
coeff_field = SampleProblem.setupCF("EF-square-cos", decayexp=2, amp=1, freqscale=1)
# NOTE: gamma has to be adjusted w.r.t. the coefficient field expansion!
gamma = 0.65                # EW decay=-2
#gamma = 0.085               # EW decay=-4
#coeff_field = SampleProblem.setupCF("constant", decayexp=2)
a0, _ = coeff_field[0]

# define multioperator
A = MultiOperator(coeff_field, FEMPoisson.assemble_operator)


# ============================================================
# PART C: Adaptive Algorithm
# ============================================================

# -------------------------------------------------------------
# -------------- ADAPTIVE ALGORITHM OPTIONS -------------------
# -------------------------------------------------------------
# error constants
cQ = 1.0
ceta = 1.0
# marking parameters
theta_eta = 0.5         # residual marking bulk parameter
theta_zeta = 0.3        # projection marking threshold factor
min_zeta = 1e-15        # minimal projection error considered
maxh = 1 / 10           # maximal mesh width for projection maximum norm evaluation
maxm = 10               # maximal search length for new new multiindices
theta_delta = 0.9       # number new multiindex activation bound
max_Lambda_frac = 1 / 10 # fraction of |Lambda| for max number of new multiindices 
# pcg solver
pcg_eps = 2e-6
pcg_maxiter = 100
error_eps = 1e-5
# refinements
max_refinements = 7

if MC_RUNS > 0:
    w_history = []
else:
    w_history = None


# refinement loop
# ===============
w0 = w
w, sim_stats = AdaptiveSolver(A, coeff_field, f, mis, w0, mesh0, gamma=gamma, cQ=cQ, ceta=ceta,
                    # marking parameters
                    theta_eta=theta_eta, theta_zeta=theta_zeta, min_zeta=min_zeta, maxh=maxh, maxm=maxm, theta_delta=theta_delta,
                    max_Lambda_frac=max_Lambda_frac,
                    # pcg solver
                    pcg_eps=pcg_eps, pcg_maxiter=pcg_maxiter,
                    # adaptive algorithm threshold
                    error_eps=error_eps,
                    # refinements
                    max_refinements=max_refinements, do_refinement=REFINEMENT, do_uniform_refinement=UNIFORM_REFINEMENT,
                    w_history=w_history)

from operator import itemgetter
active_mi = [(mu, w[mu]._fefunc.function_space().mesh().num_cells()) for mu in w.active_indices()]
active_mi = sorted(active_mi, key=itemgetter(1), reverse=True)
logger.info("==== FINAL MESHES ====")
for mu in active_mi:
    logger.info("--- %s has %s cells", mu[0], mu[1])
print "ACTIVE MI:", active_mi


# ============================================================
# PART D: MC Error Sampling
# ============================================================
if MC_RUNS > 0:
    ref_maxm = w_history[-1].max_order
    for i, w in enumerate(w_history):
        logger.info("MC error sampling for w[%i] (of %i)", i, len(w_history))
        if i == 0:
            continue
        L2err, H1err, L2err_a0, H1err_a0 = sample_error_mc(w, A, f, coeff_field, mesh0, ref_maxm, MC_RUNS, MC_N, MC_HMAX)
        sim_stats[i - 1]["MC-L2ERR"] = L2err
        sim_stats[i - 1]["MC-H1ERR"] = H1err
        sim_stats[i - 1]["MC-L2ERR_a0"] = L2err_a0
        sim_stats[i - 1]["MC-H1ERR_a0"] = H1err_a0


# ============================================================
# PART E: Plotting and Export of Data
# ============================================================

# save solution
if SAVE_SOLUTION != "":
    # save solution (also creates directory if not existing)
    w.pickle(SAVE_SOLUTION)
    # save simulation data
    import pickle
    with open(os.path.join(SAVE_SOLUTION, 'SIM-STATS.pkl'), 'wb') as f:
        pickle.dump(sim_stats, f)

# plot residuals
if PLOT_RESIDUAL and len(sim_stats) > 1:
    try:
        from matplotlib.pyplot import figure, show, legend
        x = [s["DOFS"] for s in sim_stats]
        L2 = [s["L2"] for s in sim_stats]
        H1 = [s["H1"] for s in sim_stats]
        mcL2 = [s["MC-L2ERR"] for s in sim_stats]
        mcH1 = [s["MC-H1ERR"] for s in sim_stats]
        mcL2_a0 = [s["MC-L2ERR_a0"] for s in sim_stats]
        mcH1_a0 = [s["MC-H1ERR_a0"] for s in sim_stats]
        errest = [sqrt(s["EST"]) for s in sim_stats]
        reserr = [s["RES"] for s in sim_stats]
        projerr = [s["PROJ"] for s in sim_stats]
        effest = [est / err for est, err in zip(errest, mcH1)]
        mi = [s["MI"] for s in sim_stats]
        num_mi = [len(m) for m in mi]
        print "mcH1", mcH1
        print "errest", errest
        print "efficiency", [est / err for est, err in zip(errest, mcH1)]
        # figure 1
        # --------
        fig = figure()
        fig.suptitle("error")
        ax = fig.add_subplot(111)
        ax.loglog(x, H1, '-g<', label='H1 residual')
        ax.loglog(x, L2, '-c+', label='L2 residual')
        ax.loglog(x, mcH1, '-b^', label='MC H1 error')
        ax.loglog(x, mcL2, '-ro', label='MC L2 error')
        ax.loglog(x, mcH1_a0, '-.b^', label='MC H1 error a0')
        ax.loglog(x, mcL2_a0, '-.ro', label='MC L2 error a0')
        legend(loc='upper right')
        if SAVE_SOLUTION != "":
            fig.savefig(os.path.join(SAVE_SOLUTION, 'RES.png'))
        # figure 2
        # --------
        fig2 = figure()
        fig2.suptitle("residual estimator")
        ax = fig2.add_subplot(111)
        if REFINEMENT["MI"]:
            ax.loglog(x, num_mi, '--y+', label='active mi')
        ax.loglog(x, errest, '-g<', label='error estimator')
        ax.loglog(x, reserr, '-.cx', label='residual part')
        ax.loglog(x[1:], projerr[1:], '-.m>', label='projection part')
        ax.loglog(x, mcH1, '-b^', label='MC H1 error')
        ax.loglog(x, mcL2, '-ro', label='MC L2 error')
#        ax.loglog(x, H1, '-b^', label='H1 residual')
#        ax.loglog(x, L2, '-ro', label='L2 residual')
        legend(loc='upper right')
        if SAVE_SOLUTION != "":
            fig2.savefig(os.path.join(SAVE_SOLUTION, 'EST.png'))
        # figure 3
        # --------
        fig3 = figure()
        fig3.suptitle("efficiency residual estimator")
        ax = fig3.add_subplot(111)
        ax.loglog(x, errest, '-g<', label='error estimator')
        ax.loglog(x, mcH1, '-b^', label='MC H1 error')
        ax.loglog(x, effest, '-ro', label='efficiency')        
        legend(loc='upper right')
        if SAVE_SOLUTION != "":
            fig3.savefig(os.path.join(SAVE_SOLUTION, 'ESTEFF.png'))
        show()  # this invalidates the figure instances...
    except:
        import traceback
        print traceback.format_exc()
        logger.info("skipped plotting since matplotlib is not available...")

# plot final meshes
if PLOT_MESHES:
    USE_MAYAVI = Plotter.hasMayavi() and False
    for mu, vec in w.iteritems():
        if USE_MAYAVI:
            # mesh
#            Plotter.figure(bgcolor=(1, 1, 1))
#            mesh = vec.basis.mesh
#            Plotter.plotMesh(mesh.coordinates(), mesh.cells(), representation='mesh')
#            Plotter.axes()
#            Plotter.labels()
#            Plotter.title(str(mu))
            # function
            Plotter.figure(bgcolor=(1, 1, 1))
            mesh = vec.basis.mesh
            Plotter.plotMesh(mesh.coordinates(), mesh.cells(), vec.coeffs)
            Plotter.axes()
            Plotter.labels()
            Plotter.title(str(mu))
        else:
            plot(vec.basis.mesh, title="mesh " + str(mu), interactive=False, axes=True)
#            vec.plot(title=str(mu), interactive=False)
    if USE_MAYAVI:
        Plotter.show(stop=True)
        Plotter.close(allfig=True)
    else:
        interactive()
