"""
Using Industry Patterns
=======================

This example demonstrates how you can create development patterns at a
particular `key` grain and apply them to another.
"""
import chainladder as cl

clrd = cl.load_dataset('clrd')['CumPaidLoss']
clrd = clrd[clrd['LOB'] == 'wkcomp']

industry = clrd.sum()
allstate_industry_cl = cl.Chainladder().fit(industry).predict(clrd).ultimate_.loc['Allstate Ins Co Grp']
allstate_company_cl = cl.Chainladder().fit(clrd.loc['Allstate Ins Co Grp']).ultimate_
diff = (allstate_industry_cl - allstate_company_cl)

print(diff.rename(development='Industry to Company LDF Diff'))

import numpy as np
import matplotlib.pyplot as plt
import sphinx_gallery

np.random.seed(32)


def layers(n, m):
    """
    Return *n* random Gaussian mixtures, each of length *m*.
    """
    def bump(a):
        x = 1 / (.1 + np.random.random())
        y = 2 * np.random.random() - .3
        z = 13 / (.1 + np.random.random())
        for i in range(m):
            w = (i / float(m) - y) * z
            a[i] += x * np.exp(-w * w)
    a = np.zeros((m, n))
    for i in range(n):
        for j in range(12):
            bump(a[:, i])
    return np.abs(a)


fig = plt.figure()
d = layers(3, 100)
x = range(100)
for mixture in d.T:
    mixture[[0, -1]] = 0.
    plt.fill(x, mixture, alpha=0.9)

plt.annotate('Introducing Sphinx-Gallery ' + sphinx_gallery.__version__,
             xy=(12, 4), arrowprops=dict(arrowstyle='->'), xytext=(22, 6))

plt.xticks([])
plt.yticks([])


plt.show()
