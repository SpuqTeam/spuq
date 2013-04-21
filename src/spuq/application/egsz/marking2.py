"""Implementation of the EGSZ2 marking algorithm for the residual a posteriori error estimator.

The marking is carried out with respect to the
    [a] spatial residual
    [b] upper tail bound for inactive multiindices. 
"""

from __future__ import division
from math import ceil
from collections import defaultdict
from operator import itemgetter

from spuq.application.egsz.residual_estimator import ResidualEstimator
from spuq.application.egsz.multi_vector import MultiVector, supp
from spuq.application.egsz.coefficient_field import CoefficientField
from spuq.fem.fenics.fenics_utils import weighted_H1_norm
from spuq.utils.type_check import takes, anything, optional

import numpy as np
import logging

logger = logging.getLogger(__name__)

class Marking(object):
    """EGSZ2 marking strategy for residual estimator."""

    @classmethod
    @takes(anything, float, MultiVector, float)
    def mark_x(cls, global_eta, eta_local, theta_x):
        """Carry out Doerfler marking (bulk criterion) for elements with parameter theta."""
        # add indicators of all mu and sort
        eta_list = [err for err in eta_local.values()]
        eta_local = eta_list.pop().as_array() ** 2
        while len(eta_list) > 0:
            eta_local += eta_list.pop().as_array() ** 2
        eta_local = np.sqrt(eta_local)
        eta_local_ind = [(x, i) for i, x in enumerate(eta_local)]
        eta_local_ind = sorted(eta_local_ind, key=itemgetter(0), reverse=True)
        logger.info("(mark_x) global residual is %f, want to mark for %f", global_eta, theta_x * global_eta)
        
        # TODO: verify global eta by summing up!
        print "GLOBAL_ETA", global_eta, np.sqrt(sum([x ** 2 for x in eta_local]))
         
        # setup marking sets
        mesh_markers = set()
        marked_eta = 0.0
        for eta_cell in eta_local_ind:
            if theta_x * global_eta <= marked_eta:
                break
            mesh_markers.add(eta_cell[1])
            marked_eta += eta_cell[0]
        logger.info("(mark_x) MARKED elements: %s", len(mesh_markers))
        return mesh_markers

    @classmethod
    @takes(anything, MultiVector, (list, tuple, set))
    def refine_x(cls, w, cell_ids):
        w.refine(cell_ids)

    @classmethod
    @takes(anything, (list, tuple), float, dict, callable, float, int)
    def mark_y(cls, Lambda, global_zeta, zeta, eval_zeta_m, theta_y, max_new_mi=100):
        """Carry out Doerfler marking by activation of new indices."""
        suppLambda = supp(Lambda)
        maxm = max(suppLambda)        
        new_mi = []
        marked_zeta = 0.0
        while True:
            sorted_zeta = sorted(zeta.items(), key=itemgetter(1))
            print "ZZZZZZZZZ", sorted_zeta
            mu = sorted_zeta[-1][0]
            new_mi.append(mu)
            marked_zeta += sorted_zeta[-1][1]
            # extend set if necessary (see section 5.7)
            mu2 = mu.dec(maxm)
            if mu2 in Lambda:
                mu = Lambda[Lambda.index(mu2)]
                logger.debug("extending multiindex canidates since %s is at the boundary of Lambda (reachable from %s)", mu, mu2)
                minm = min(set(range(1, maxm + 2)).difference(set(suppLambda))) # find min(N\setminus supp\Lambda)
                new_mu = mu.inc(minm)
                zeta[new_mu] = eval_zeta_m(mu, minm)
            else:
                logger.debug("no further extension of multiindex candidates required")
            
            # break if sufficiently many new mi are selected
            if theta_y * global_zeta <= marked_zeta or len(new_mi) >= max_new_mi or len(zeta) == 0:
                break 

        if len(zeta) == 0:
            logger.warning("list of mi candidates is empty")

        if len(new_mi) > 0:
            logger.info("SELECTED NEW MULTIINDICES %s", new_mi)
        else:
            logger.info("NO NEW MULTIINDICES SELECTED")
        return new_mi

    @classmethod
    @takes(anything, MultiVector, (list, tuple), callable)
    def refine_y(cls, w, new_mi):
        V = w.basis
        for mu in new_mi:
            w[mu] = V.basis.new_vector()

    @classmethod
    def refine_osc(cls, w, coeff, M):
        osc_refinements = 0
        # TODO
        return osc_refinements
    
