import numpy as np


def lrpd(a):
    """L,R,P,D,DA aus der LR = PDA Zerlegung
    Methode aus Dahmen W., Reusken A.; Numerik fuer Ingenieure und Naturwissenschaeftler; Springer S. 79
    :param a: numpy.matrix NxN
    """
    n = a.shape[0]
    p = np.matrix(np.eye(n).astype(dtype=float))
    d = np.matrix(np.eye(n).astype(dtype=float))
    da = np.matrix(np.zeros_like(p))
    l = np.matrix(np.eye(n))
    r = np.matrix(np.zeros_like(p))
    indexes_r = range(n)
    # max_aij = 0.0
    for i in range(n):
        d[i, i] = 1 / abs(a[i]).sum()
        # Skalierung
        da[i] = d[i, i] * a[i]
    for j in range(n):
        # max_aij = max(abs(da[j:, j]))
        indexes_r[j] = j + abs(da[j:, j]).argmax()
        # Spaltenpivotisierung
        da[[j, indexes_r[j]]] = da[[indexes_r[j], j]]
        p[[j, indexes_r[j]]] = p[[indexes_r[j], j]]
        for i in range(j + 1, n):
            # neue Eintraege in L
            da[i, j] = da[i, j] / da[j, j]
            for k in range(j + 1, n):
                # neue Eintraege in R
                da[i, k] = da[i, k] - da[i, j] * da[j, k]
    for i in range(n):
        l[i + 1:n, i] = da[i + 1:n, i]
        r[i, i:n] = da[i, i:n]
    return l, r, p, d, da


def gausselimination(a, b):
    """Loesung des Systems Ax = b (LRx=PDb) durch Vorwaertseinsetzen aus Ly = Pb, und danach
    Rueckwaertseinsetzen aus Rx = y
    :param a: numpy.matrix n X n
    :param b: numpy.matrix n X 1
    """
    n = a.shape[0]
    x = np.matrix(np.zeros_like(b))
    y = np.matrix(np.zeros_like(b))
    l, r, p, d, da = lrpd(a)
    pdb = p * d * b
    sum_lik_xk = 0
    sum_lik_yk = 0
    for j in range(0, n, +1):
        # Vorwaertseinsetzen Ly = PDb
        for k in range(0, j, +1):
            sum_lik_yk = sum_lik_yk + l[j, k] * y[k]
        y[j] = (pdb[j, 0] - sum_lik_yk) / 1.0
        sum_lik_yk = 0
    for j in range(n - 1, -1, -1):
        # Rueckwaertseinsetzen Rx = y
        for k in range(n - 1, j, -1):
            sum_lik_xk = sum_lik_xk + r[j, k] * x[k]
        x[j] = (y[j, 0] - sum_lik_xk) / r[j, j]
        sum_lik_xk = 0
    return x


# A = np.matrix([[1, 5, 0], [2, 2, 2], [-2, 0, 2]]).astype(dtype=float)
# A = np.matrix([[2, -1, -3, 3], [4, 0, -3, 1], [6, 1, -1, 6], [-2, -5, 4, 1]]).astype(dtype=float)
# l, r, p, d, da = lrpd(A)
# for mat in [l, r, p, d, da, l * r]:
#     mat = Matrix(mat)
#     for i in range(mat.shape[0]):
#         mat[i, :] = Matrix(map(nsimplify, mat[i, :])).T
#     pprint(mat)
#     print "\n"
# pprint(gausselimination(A, Matrix(np.matrix([1, 2, 3, 4])).T))

# noinspection PyAugmentAssignment
def nr_ls(x0, f, j, tol, max_it, inner_loop_condition,
          notify_status_func, method_loops, process_func_handle):
    x = x0
    # Newton method: G(x) = J(x)^-1 * F(x)
    outer_it_k = 0
    inner_it_j = 0
    j_val = j(x)
    f_val = f(x)
    y = np.matrix(np.ones(len(x))).T * tol / (np.sqrt(len(x)) * tol)
    magnitude_f = np.sqrt((f_val.T * f_val).item())
    # Line search variable lambda
    lambda_ls = 0.0
    accum_step = 0.0
    # For progress bar, use log scale to compensate for quadratic convergence
    log10_to_o_max_magnitude_f = np.log10(tol / magnitude_f)
    progress_k = (1.0 - np.log10(tol / magnitude_f) /
                  log10_to_o_max_magnitude_f) * 100.0
    diff = np.matrix(np.empty([len(x), 1]))
    diff.fill(np.nan)
    stop = False
    divergent = False
    # Non-functional status notification
    notify_status_func(progress_k, stop, outer_it_k,
                       inner_it_j, lambda_ls, accum_step,
                       x, diff, f_val, lambda_ls * y,
                       method_loops)
    # End non-functional notification
    while outer_it_k <= max_it and not stop:
        outer_it_k += 1
        method_loops[1] += 1
        inner_it_j = 0
        lambda_ls = 1.0
        accum_step += lambda_ls
        x_k_m_1 = x
        progress_k_m_1 = progress_k
        y = gausselimination(j_val, -f_val)
        # First attempt without backtracking
        x = x + lambda_ls * y
        diff = x - x_k_m_1
        j_val =     j(x)
        f_val = f(x)
        magnitude_f = np.sqrt((f_val.T * f_val).item())
        # Non-functional status notification
        notify_status_func(progress_k, stop, outer_it_k,
                           inner_it_j, lambda_ls, accum_step,
                           x, diff, f_val, lambda_ls * y,
                           method_loops)
        # End non-functional notification
        if magnitude_f < tol and inner_loop_condition(x):
            stop = True  # Procedure successful
        else:
            # For progress use log scale to compensate for quadratic
            # convergence
            progress_k = (1.0 - np.log10(tol / magnitude_f) /
                          log10_to_o_max_magnitude_f) * 100.0
            if np.isnan(magnitude_f) or np.isinf(magnitude_f):
                stop = True  # Divergent method
                divergent = True
                progress_k = 0.0
            else:
                pass
            if round(progress_k) == round(progress_k_m_1):
                # Non-functional gui processing
                process_func_handle()
                # End non-functional processing
                # if form.progress_var.wasCanceled():
                # stop = True
        while inner_it_j <= max_it and \
                not inner_loop_condition(x) and \
                not stop:
            # Backtrack if any conc < 0. Line search method.
            # Ref. http://dx.doi.org/10.1016/j.compchemeng.2013.06.013
            inner_it_j += 1
            lambda_ls = lambda_ls / 2.0
            accum_step += -lambda_ls
            x = x_k_m_1
            progress_k = progress_k_m_1
            x = x + lambda_ls * y
            diff = x - x_k_m_1
            j_val = j(x)
            f_val = f(x)
            # Non-functional status notification
            notify_status_func(progress_k, stop, outer_it_k,
                               inner_it_j, lambda_ls, accum_step,
                               x, diff, f_val, lambda_ls * y,
                               method_loops)
            # End non-functional notification
            method_loops[0] += 1
    if stop and not divergent:
        progress_k = 100.0
    elif divergent:
        progress_k = 0.0
    # Non-functional status notification
    notify_status_func(progress_k, stop, outer_it_k,
                       inner_it_j, lambda_ls, accum_step,
                       x, diff, f_val, lambda_ls * y,
                       method_loops)
    # End non-functional notification
    return progress_k, stop, outer_it_k,\
        inner_it_j, lambda_ls, accum_step,\
        x, diff, f_val, lambda_ls * y,\
        method_loops
