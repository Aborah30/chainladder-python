import chainladder as cl
import pandas as pd
import numpy as np
from numpy.testing import assert_equal
import copy

tri = cl.load_dataset('clrd')
qtr = cl.load_dataset('quarterly')

# Test Triangle slicing
def test_slice_by_boolean():
    assert tri[tri['LOB'] == 'ppauto'].loc['Wolverine Mut Ins Co']['CumPaidLoss'] == \
                            tri.loc['Wolverine Mut Ins Co'].loc['ppauto']['CumPaidLoss']


def test_slice_by_loc():
    assert tri.loc['Aegis Grp'].loc['comauto'].index.iloc[0, 0] == 'comauto'


def test_slice_origin():
    assert cl.load_dataset('raa')[cl.load_dataset('raa').origin>'1985'].shape == \
        (1, 1, 5, 10)


def test_slice_development():
    assert cl.load_dataset('raa')[cl.load_dataset('raa').development<72].shape == \
        (1, 1, 10, 5)


def test_slice_by_loc_iloc():
    assert tri.groupby('LOB').sum().loc['comauto'].index.iloc[0, 0] == 'comauto'


def test_repr():
    np.testing.assert_equal(pd.read_html(cl.load_dataset('raa')._repr_html_())[0].set_index('Origin').values,
                            cl.load_dataset('raa').to_frame().values)


def test_arithmetic_intersection():
    raa = cl.load_dataset('raa')
    assert raa[raa.valuation<'1987'].shape == (raa-raa[raa.valuation<'1987']).shape


def test_to_frame_unusual():
    a = cl.load_dataset('clrd').groupby(['LOB']).sum().latest_diagonal['CumPaidLoss'].to_frame().values
    b = cl.load_dataset('clrd').latest_diagonal['CumPaidLoss'].groupby(['LOB']).sum().to_frame().values
    np.testing.assert_equal(a, b)


def test_link_ratio():
    np.testing.assert_allclose(cl.load_dataset('RAA').link_ratio.values*cl.load_dataset('RAA').values[:,:,:-1,:-1],
                               cl.load_dataset('RAA').values[:,:,:-1,1:], atol=1e-5)


def test_incr_to_cum():
    np.testing.assert_equal(tri.cum_to_incr().incr_to_cum().values, tri.values)


def test_create_new_value():
    tri2 = copy.deepcopy(tri)
    tri2['lr'] = (tri2['CumPaidLoss']/tri2['EarnedPremDIR'])
    assert (tri.shape[0], tri.shape[1]+1, tri.shape[2], tri.shape[3]) == tri2.shape


def test_multilevel_index_groupby_sum1():
    assert tri.groupby('LOB').sum().sum() == tri.sum()


def test_multilevel_index_groupby_sum2():
    a = tri.groupby('GRNAME').sum().sum()
    b = tri.groupby('LOB').sum().sum()
    assert a == b


def test_boolean_groupby_eq_groupby_loc():
    np.testing.assert_equal(tri[tri['LOB']=='ppauto'].sum().values,
                        tri.groupby('LOB').sum().loc['ppauto'].values)


def test_latest_diagonal_two_routes():
    assert tri.latest_diagonal.sum()['BulkLoss'] == tri.sum().latest_diagonal['BulkLoss']


def test_sum_of_diff_eq_diff_of_sum():
    assert (tri['BulkLoss']-tri['CumPaidLoss']).latest_diagonal == \
           (tri.latest_diagonal['BulkLoss'] - tri.latest_diagonal['CumPaidLoss'])


def test_append():
    assert cl.load_dataset('raa').append(cl.load_dataset('raa'), index='raa2').sum() == 2*cl.load_dataset('raa')


def test_assign_existing_col():
    tri = cl.load_dataset('quarterly')
    before = tri.shape
    tri['paid'] = 1/tri['paid']
    assert tri.shape == before


def test_arithmetic_across_keys():
    x = cl.load_dataset('auto')
    np.testing.assert_equal((x.sum()-x.iloc[0]).values, x.iloc[1].values)

def test_grain():
    actual = qtr.iloc[0,0].grain('OYDY').values[0,0,:,:]
    expected = np.array([[  44.,  621.,  950., 1020., 1070., 1069., 1089., 1094., 1097.,
        1099., 1100., 1100.],
       [  42.,  541., 1052., 1169., 1238., 1249., 1266., 1269., 1296.,
        1300., 1300.,   np.nan],
       [  17.,  530.,  966., 1064., 1100., 1128., 1155., 1196., 1201.,
        1200.,   np.nan,   np.nan],
       [  10.,  393.,  935., 1062., 1126., 1209., 1243., 1286., 1298.,
          np.nan,   np.nan,   np.nan],
       [  13.,  481., 1021., 1267., 1400., 1476., 1550., 1583.,   np.nan,
          np.nan,   np.nan,   np.nan],
       [   2.,  380.,  788.,  953., 1001., 1030., 1066.,   np.nan,   np.nan,
          np.nan,   np.nan,   np.nan],
       [   4.,  777., 1063., 1307., 1362., 1411.,   np.nan,   np.nan,   np.nan,
          np.nan,   np.nan,   np.nan],
       [   2.,  472., 1617., 1818., 1820.,   np.nan,   np.nan,   np.nan,   np.nan,
          np.nan,   np.nan,   np.nan],
       [   3.,  597., 1092., 1221.,   np.nan,   np.nan,   np.nan,   np.nan,   np.nan,
          np.nan,   np.nan,   np.nan],
       [   4.,  583., 1212.,   np.nan,   np.nan,   np.nan,   np.nan,   np.nan,   np.nan,
          np.nan,   np.nan,   np.nan],
       [  21.,  422.,   np.nan,   np.nan,   np.nan,   np.nan,   np.nan,   np.nan,   np.nan,
          np.nan,   np.nan,   np.nan],
       [  13.,   np.nan,   np.nan,   np.nan,   np.nan,   np.nan,   np.nan,   np.nan,   np.nan,
          np.nan,   np.nan,   np.nan]])
    np.testing.assert_equal(actual, expected)

def test_off_cycle_val_date():
    assert cl.load_dataset('quarterly').valuation_date == pd.to_datetime('2006-03-31')

def test_printer():
    print(cl.load_dataset('abc'))


def test_value_order():
    a = tri[['CumPaidLoss','BulkLoss']]
    b = tri[['BulkLoss', 'CumPaidLoss']]
    assert_equal(a.values[:,-1], b.values[:, 0])


def test_trend():
    assert abs((cl.load_dataset('abc').trend(0.05).trend((1/1.05)-1) -
                cl.load_dataset('abc')).sum().sum()) < 1e-5


def test_arithmetic_1():
    x = cl.load_dataset('mortgage')
    np.testing.assert_equal(-(((x/x)+0)*x), -(+x))


def test_arithmetic_2():
    x = cl.load_dataset('mortgage')
    np.testing.assert_equal(1-(x/x), 0*x*0)


def test_rtruediv():
    assert np.nansum(abs(((1/cl.load_dataset('raa'))*cl.load_dataset('raa')).values[0,0] - cl.load_dataset('raa').nan_triangle()))< .00001


def test_shift():
    x = cl.load_dataset('quarterly').iloc[0,0]
    np.testing.assert_equal(x[x.valuation<=x.valuation_date].values, x.values)

def test_quantile_vs_median():
    clrd = cl.load_dataset('clrd')
    np.testing.assert_equal(clrd.quantile(.5)['CumPaidLoss'].values,
                            clrd.median()['CumPaidLoss'].values)


def test_grain_returns_valid_tri():
    tri = cl.load_dataset('quarterly')
    assert tri.grain('OYDY').latest_diagonal == tri.latest_diagonal


def test_base_minimum_exposure_triangle():
    raa = (cl.load_dataset('raa').latest_diagonal*0+50000).to_frame().reset_index()
    raa['index'] = raa['index'].astype(str)
    cl.Triangle(raa, origin='index', columns='Latest')


def test_origin_and_value_setters():
    raa = cl.load_dataset('raa')
    raa2 = cl.load_dataset('raa')
    raa.columns = list(raa.columns)
    raa.origin = list(raa.origin)
    assert np.all((np.all(raa2.origin == raa.origin),
                   np.all(raa2.development == raa.development),
                   np.all(raa2.odims == raa.odims),
                   np.all(raa2.vdims == raa.vdims)))

def test_grain_increm_arg():
    tri = cl.load_dataset('quarterly')['incurred']
    tri_i = tri.cum_to_incr()
    np.testing.assert_equal(tri_i.grain('OYDY', incremental=True).incr_to_cum(),
                            tri.grain('OYDY'))


def test_valdev1():
    a = cl.load_dataset('quarterly').dev_to_val().val_to_dev().values
    b = cl.load_dataset('quarterly').values
    np.testing.assert_equal(a,b)


def test_valdev2():
    a = cl.load_dataset('quarterly').dev_to_val().grain('OYDY').val_to_dev().values
    b = cl.load_dataset('quarterly').grain('OYDY').values
    np.testing.assert_equal(a,b)


def test_valdev3():
    a = cl.load_dataset('quarterly').grain('OYDY').dev_to_val().val_to_dev().values
    b = cl.load_dataset('quarterly').grain('OYDY').values
    np.testing.assert_equal(a,b)


#def test_valdev4():
#    # Does not work with pandas 0.23, consider requiring only pandas>=0.24
#    raa = cl.load_dataset('raa')
#    np.testing.assert_equal(raa.dev_to_val()[raa.dev_to_val().development>='1989'].values,
#        raa[raa.valuation>='1989'].dev_to_val().values)


def test_valdev5():
    raa = cl.load_dataset('raa')
    np.testing.assert_equal(raa[raa.valuation>='1989'].latest_diagonal.values,
                            raa.latest_diagonal.values)

def test_valdev6():
    np.testing.assert_equal(cl.load_dataset('raa').grain('OYDY').latest_diagonal.values,
                            cl.load_dataset('raa').latest_diagonal.grain('OYDY').values)

def test_reassignment():
    raa = cl.load_dataset('clrd')
    raa['values'] = raa['CumPaidLoss']
    raa['values'] = raa['values'] + raa['CumPaidLoss']
