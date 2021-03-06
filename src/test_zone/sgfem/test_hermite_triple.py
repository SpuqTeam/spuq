from matplotlib.pyplot import figure, show, spy

from spuq.math_utils.multiindex_set import MultiindexSet
from spuq.polyquad.structure_coefficients import evaluate_triples
from spuq.polyquad.polynomials import LegendrePolynomials


I = MultiindexSet.createCompleteOrderSet(4, 3, reversed=True).arr
print I

#H = evaluate_Hermite_triple(I, I, J)
#print "shape of H:", H.shape
    # create polynomial instance
lp = LegendrePolynomials()

L = evaluate_triples(lp, I, I)
print len(L), L[0].shape

# fig = figure()
# spy(np.sum(H, axis=2))
fig = figure()
#spy(np.sum(L))
spy(L[3])
show()
