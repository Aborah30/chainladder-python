"""
The Munich Adjustment Method
============================
"""

from sklearn.base import BaseEstimator, TransformerMixin
from chainladder.utils.weighted_regression import WeightedRegression
from chainladder.development import Development
from chainladder.core import IO
import numpy as np
import copy


class MunichAdjustment(BaseEstimator, TransformerMixin, IO):
    """Applies the Munich Chainladder adjustment to a set of paid/incurred
       ldfs.

    Parameters
    ----------
    paid_to_incurred : dict
        A dictionary representing the ``values`` of paid and incurred triangles
        where ``values`` are an appropriate selection from :class:`Triangle`
        ``.values``, such as ``{'paid':'incurred'}``


    """
    def __init__(self, paid_to_incurred):
        self.paid_to_incurred = paid_to_incurred

    def fit(self, X, y=None, sample_weight=None):
        """Fit the model with X.

        Parameters
        ----------
        X : Triangle-like
            Set of LDFs to which the munich adjustment will be applied.
        y : Ignored
        sample_weight : Ignored

        Returns
        -------
        self : object
            Returns the instance itself.
        """
        if (type(X.ddims) != np.ndarray):
            raise ValueError('Triangle must be expressed with development lags')
        obj = copy.copy(X)
        if 'ldf_' not in obj:
            obj = Development().fit_transform(obj)
        self.p_to_i_X_ = self._get_p_to_i_object(obj)
        self.p_to_i_ldf_ = self._get_p_to_i_object(obj.ldf_)
        self.p_to_i_sigma_ = self._get_p_to_i_object(obj.sigma_)
        self.q_f_, self.rho_sigma_ = self._get_MCL_model(obj)
        self.residual_, self.q_resid_ = self._get_MCL_residuals(obj)
        self.lambda_coef_ = self._get_MCL_lambda()
        self.cdf_ = self._get_cdf(obj)
        return self

    def transform(self, X):
        """ If X and self are of different shapes, align self to X, else
        return self.

        Parameters
        ----------
        X : Triangle
            The triangle to be transformed

        Returns
        -------
            X_new : New triangle with transformed attributes.
        """
        X.cdf_ = self.cdf_
        X.ldf_ = self.ldf_
        return X

    def _get_p_to_i_object(self, obj):
        paid = obj[list(self.paid_to_incurred.keys())[0]]
        for item in list(self.paid_to_incurred.keys())[1:]:
            paid[item] = obj[item]
        incurred = obj[list(self.paid_to_incurred.values())[0]]
        for item in list(self.paid_to_incurred.values())[1:]:
            incurred[item] = obj[item]
        paid = paid.values[np.newaxis]
        incurred = incurred.values[np.newaxis]
        return np.concatenate((paid, incurred), axis=0)

    def _p_to_i_concate(self, obj_p, obj_i):
        return np.concatenate((obj_p[np.newaxis], obj_i[np.newaxis]), 0)

    def _get_MCL_model(self, X):
        p, i = self.p_to_i_X_[0], self.p_to_i_X_[1]
        modelsP = WeightedRegression(axis=2, thru_orig=True)
        modelsP = modelsP.fit(p, i, 1/p).sigma_fill(X.sigma_interpolation)
        modelsI = WeightedRegression(axis=2, thru_orig=True)
        modelsI = modelsI.fit(i, p, 1/i).sigma_fill(X.sigma_interpolation)
        q_f = self._p_to_i_concate(modelsP.slope_, modelsI.slope_)
        rho_sigma = self._p_to_i_concate(modelsP.sigma_, modelsI.sigma_)
        return np.swapaxes(q_f, -1, -2), np.swapaxes(rho_sigma, -1, -2)

    def _get_MCL_residuals(self, X):
        p_to_i_ata = self._get_p_to_i_object(X.link_ratio)
        p_to_i_ldf = self.p_to_i_ldf_
        p_to_i_sigma = self.p_to_i_sigma_
        paid, incurred = self.p_to_i_X_[0], self.p_to_i_X_[1]
        p_to_i_ldf = np.unique(p_to_i_ldf, axis=-2)  # May cause issues later
        p_to_i_sigma = np.unique(p_to_i_sigma, axis=-2)  # May cause issues
        residualP = (p_to_i_ata[0]-p_to_i_ldf[0]) / \
            p_to_i_sigma[0]*np.sqrt(paid[..., :-1, :-1])
        residualI = (p_to_i_ata[1]-p_to_i_ldf[1]) / \
            p_to_i_sigma[1]*np.sqrt(incurred[..., :-1, :-1])
        nans = (X-X[X.valuation == X.valuation_date]).values[0, 0]*0+1
        q_resid = (paid/incurred - self.q_f_[1]) / \
            self.rho_sigma_[1]*np.sqrt(incurred)*nans
        q_inv_resid = (incurred/paid - 1/self.q_f_[1]) / \
            self.rho_sigma_[0]*np.sqrt(paid)*nans
        residual = self._p_to_i_concate(residualP, residualI)
        q_resid = self._p_to_i_concate(q_inv_resid, q_resid)
        return residual, q_resid

    def _get_MCL_lambda(self):
        k, v, o, d = self.residual_[1].shape
        w = np.reshape(self.residual_[1], (k, v, o*d))
        w[w == 0] = np.nan
        w = w*0+1
        lambdaI = WeightedRegression(thru_orig=True, axis=-1).fit(
            np.reshape(self.q_resid_[1][..., :-1, :-1], (k, v, o*d)),
            np.reshape(self.residual_[1], (k, v, o*d)), w).slope_
        lambdaP = WeightedRegression(thru_orig=True, axis=-1).fit(
            np.reshape(self.q_resid_[0][..., :-1, :-1], (k, v, o*d)),
            np.reshape(self.residual_[0], (k, v, o*d)), w).slope_
        return self._p_to_i_concate(lambdaP, lambdaI)[..., np.newaxis]

    @property
    def munich_full_triangle_(self):
        full_paid = self.p_to_i_X_[0][..., 0:1]
        full_incurred = self.p_to_i_X_[1][..., 0:1]
        for i in range(self.p_to_i_X_[0].shape[-1]-1):
            paid = (self.p_to_i_ldf_[0][..., i:i+1] +
                    self.lambda_coef_[0] *
                    self.p_to_i_sigma_[0][..., i:i+1] /
                    self.rho_sigma_[0][..., i:i+1] *
                    (full_incurred[..., -1:]/full_paid[..., -1:] -
                     self.q_f_[0][..., i:i+1]))*full_paid[..., -1:]
            inc = (self.p_to_i_ldf_[1][..., i:i+1] + self.lambda_coef_[1] *
                   self.p_to_i_sigma_[1][..., i:i+1] /
                   self.rho_sigma_[1][..., i:i+1] *
                   (full_paid[..., -1:]/full_incurred[..., -1:] -
                   self.q_f_[1][..., i:i+1]))*full_incurred[..., -1:]
            full_incurred = np.concatenate(
                (full_incurred,
                 np.nan_to_num(self.p_to_i_X_[1][..., i+1:i+2]) +
                 (1-np.nan_to_num(self.p_to_i_X_[1][..., i+1:i+2]*0+1)) *
                 inc), axis=3)
            full_paid = np.concatenate(
                (full_paid,
                 np.nan_to_num(self.p_to_i_X_[0][..., i+1:i+2]) +
                 (1-np.nan_to_num(self.p_to_i_X_[0][..., i+1:i+2]*0+1)) *
                 paid), axis=3)
        return self._p_to_i_concate(full_paid, full_incurred)

    def _get_cdf(self, X):
        ''' needs to be an attribute that gets assigned.  requires we overwrite
            the cdf and ldf methods with
        '''
        obj = copy.copy(X.cdf_)
        cdf_triangle = self.munich_full_triangle_
        cdf_triangle = cdf_triangle[..., -1:]/cdf_triangle[..., :-1]
        paid = list(self.paid_to_incurred.keys())
        for n, item in enumerate(paid):
            idx = np.where(X.cdf_.vdims == item)[0][0]
            obj.values[:, idx:idx+1, ...] = cdf_triangle[0, :, n:n+1, ...]
        incurred = list(self.paid_to_incurred.values())
        for n, item in enumerate(incurred):
            idx = np.where(X.cdf_.vdims == item)[0][0]
            obj.values[:, idx:idx+1, ...] = cdf_triangle[1, :, n:n+1, ...]
        obj.nan_override = True
        obj.set_slicers()
        return obj

    @property
    def ldf_(self):
        ldf_tri = self.cdf_.values.copy()
        ldf_tri = np.concatenate((ldf_tri, np.ones(ldf_tri.shape)[..., -1:]), -1)
        ldf_tri = ldf_tri[..., :-1]/ldf_tri[..., 1:]
        obj = copy.copy(self.cdf_)
        obj.values = ldf_tri
        obj.set_slicers
        return obj
