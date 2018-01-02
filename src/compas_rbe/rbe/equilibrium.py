from numpy import array
from numpy import zeros
from numpy import diagflat
from numpy import absolute

import cvxopt
import cvxpy

from compas_rbe.rbe.utilities import make_Aeq
from compas_rbe.rbe.utilities import make_Aiq


__author__    = ['Ursula Frick', 'Tom Van Mele', ]
__copyright__ = 'Copyright 2016 - Block Research Group, ETH Zurich'
__license__   = 'MIT License'
__email__     = 'vanmelet@ethz.ch'


def compute_interface_forces_xfunc(data):
    from compas_rbe.rbe.assembly import Assembly
    from compas_rbe.rbe.block import Block
    assembly = Assembly.from_data(data['assembly'])
    assembly.blocks = {int(key): Block.from_data(data['blocks'][key]) for key in data['blocks']}
    config = data['config']
    compute_interface_forces(assembly, **config)
    return {
        'assembly': assembly.to_data(),
        'blocks': {str(key): assembly.blocks[key].to_data() for key in assembly.blocks}
    }


def compute_interface_forces(assembly, friction8=False, mu=0.6, density=1.0, verbose=False):
    r"""Compute the forces at the interfaces between the blocks of an assembly.

    Solve the following optimisation problem:

    .. math::


    Parameters:
        assembly (compas_rbe.rbe.assembly.Assembly): The rigid block assembly.
        friction8 (bool): Use an eight-sided friction pyramid. Default is False.
        mu (float):
        density (float):
    """

    n = assembly.number_of_vertices()

    key_index = {key: index for index, key in enumerate(assembly.vertices())}

    fixed = [key for key in assembly.vertices_where({'is_support': True})]
    fixed = [key_index[key] for key in fixed]
    free  = [index for index in range(n) if index not in fixed]

    # ==========================================================================
    # equality constraints
    # ==========================================================================

    A, vcount = make_Aeq(assembly)
    A = A.toarray()
    A = A[[index * 6 + i for index in free for i in range(6)], :]

    b = [[0, 0, assembly.blocks[key].volume() * density, 0, 0, 0] for key, attr in assembly.vertices(True)]
    b = array(b, dtype=float)
    b = -1.0 * b
    b = b[free, :].reshape((-1, 1), order='C')  # row-major ordering => fx, fy, fz, mx, my, mz, fx, fy, fz, mx, my, mz, ...

    # ==========================================================================
    # inequality constraints
    # ==========================================================================

    G = make_Aiq(vcount, False)
    G = G.toarray()

    h = zeros((G.shape[0], 1))

    # ==========================================================================
    # objective function
    # ==========================================================================

    a1 = 1.0   # weights on the compression forces
    a2 = 1e+5  # weights on the tension forces
    a3 = 1e+2  # weights on the friction forces (same as compression weights in Whiting)

    # add alpha := 1 / compression forces

    p = array([a1, a2, a3, a3] * vcount)
    P = diagflat(p)

    q = zeros((4 * vcount, 1))

    # ==========================================================================
    # weighting matrix
    # ==========================================================================

    # W

    # ==========================================================================
    # sanity check
    # ==========================================================================

    if verbose:
        print 'P', P.shape
        print 'q', q.shape
        print 'G', G.shape
        print 'h', h.shape
        print 'A', A.shape
        print 'b', b.shape

    # ==========================================================================
    # sole with cvxpy
    # ==========================================================================

    x = cvxpy.Variable(P.shape[0])

    objective = cvxpy.Minimize(0.5 * cvxpy.quad_form(x, P) + q.T * x)

    constraints = [
        A * x == b,
        G * x <= h
    ]

    problem = cvxpy.Problem(objective, constraints)

    problem.solve(solver=cvxpy.CVXOPT, verbose=verbose)

    x1 = array(x.value).reshape((-1, 1))

    if verbose:
        print problem.value

    # ==========================================================================
    # solve with cvxopt
    # (use sparse matrices!)
    # ==========================================================================

    # min   0.5 * xT * P * x + qT * x
    # s.t.  A * x == b
    #       G * x <= h

    # instead do:
    # min   0.5 * xT * W * P * x (+ qT * x)

    # solve iteratively
    # at every iteration
    # update W based on the compression forces in the previous iteration
    # W is diagonal with
    # 1 / f+, 1, 1 / f+, 1 / f+

    # res = cvxopt.solvers.qp(
    #     cvxopt.sparse(cvxopt.matrix(P), tc='d'),
    #     cvxopt.matrix(q),
    #     cvxopt.sparse(cvxopt.matrix(G), tc='d'),
    #     cvxopt.matrix(h),
    #     cvxopt.sparse(cvxopt.matrix(A), tc='d'),
    #     cvxopt.matrix(b)
    # )

    # x2 = array(res['x']).reshape((-1, 1))

    # if verbose:
    #     print res['primal objective']

    # ==========================================================================
    # update
    # ==========================================================================

    x = x1

    x[absolute(x) < 1e-6] = 0.0

    if verbose:
        print x

    x = x.flatten().tolist()

    offset = 0

    for u, v, attr in assembly.edges(True):

        n = len(attr['interface_points'])

        attr['interface_forces'] = []

        for i in range(n):
            attr['interface_forces'].append({
                'c_np': x[offset + 4 * i + 0],
                'c_nn': x[offset + 4 * i + 1],
                'c_u' : x[offset + 4 * i + 2],
                'c_v' : x[offset + 4 * i + 3]
            })

        offset += 4 * n


# ==============================================================================
# Debugging
# ==============================================================================

if __name__ == "__main__":
    pass
