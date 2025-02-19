import numpy as np
import pandas as pd
import copy
from chainladder.methods import MethodBase


class CapeCod(MethodBase):
    """Applies the CapeCod technique to triangle **X**

    Parameters
    ----------
    trend : float (default=0.0)
        The cape cod trend assumption
    decay : float (defaut=1.0)
        The cape cod decay assumption

    Attributes
    ----------
    triangle :
        returns **X**
    ultimate_ :
        The ultimate losses per the method
    ibnr_ :
        The IBNR per the method
    apriori_ :
        The trended apriori vector developed by the Cape Cod Method
    detrended_apriori_ :
        The detrended apriori vector developed by the Cape Cod Method
    """

    def __init__(self, trend=0, decay=1):
        self.trend = trend
        self.decay = decay

    def fit(self, X, y=None, sample_weight=None):
        """Fit the model with X.

        Parameters
        ----------
        X : Triangle-like
            Loss data to which the model will be applied.
        y : Ignored
        sample_weight : Triangle-like
            The exposure to be used in the method.
        Returns
        -------
        self : object
            Returns the instance itself.
        """
        if sample_weight is None:
            raise ValueError('sample_weight is required.')
        super().fit(X, y, sample_weight)
        obj = copy.deepcopy(self)
        self.sample_weight_ = sample_weight
        self.ultimate_, self.apriori_, self.detrended_ultimate_ = \
            self._get_ultimate_(X, sample_weight, obj)
        self.full_triangle_ = self._get_full_triangle_()
        return self

    def _get_ultimate_(self, X, sample_weight, obj):
        origin, development, len_orig = -2, -1, sample_weight.shape[-2]
        ult = obj.X_
        latest = X.latest_diagonal.values
        ult.values = \
            obj.cdf_.values[..., :ult.shape[development]]*(ult.values*0+1)
        cdf = ult.latest_diagonal.values
        exposure = sample_weight.values
        reported_exposure = exposure/cdf
        trend_exponent = len_orig-np.arange(len_orig)-1
        trend_array = (1+self.trend)**(trend_exponent)
        trend_array = X.expand_dims(trend_array[..., np.newaxis])
        decay_matrix = self.decay ** np.abs(
            np.arange(len_orig)[np.newaxis].T -
            np.arange(len_orig)[np.newaxis])
        decay_matrix = X.expand_dims(decay_matrix)
        weighted_exposure = \
            np.swapaxes(reported_exposure, development, origin)*decay_matrix
        trended_ultimate = (latest*trend_array)/reported_exposure
        trended_ultimate = np.swapaxes(trended_ultimate, development, origin)
        apriori = np.sum(weighted_exposure*trended_ultimate, development) / \
            np.sum(weighted_exposure, development)
        ult.values = apriori[..., np.newaxis]
        ult.ddims = np.array(['Apriori'])
        apriori_ = copy.copy(ult)
        detrended_ultimate = apriori_.values/trend_array
        detrended_apriori_ = copy.copy(obj)
        detrended_apriori_.values = detrended_ultimate
        ibnr = detrended_ultimate*(1-1/cdf)*exposure
        ult.values = latest + ibnr
        ult.ddims = np.array(['Ultimate'])
        ult.valuation = pd.DatetimeIndex([pd.to_datetime('2262-04-11')] *
                                         len_orig)
        apriori_.set_slicers()
        return ult, apriori_, detrended_apriori_

    def predict(self, X, sample_weight):
        obj = super().predict(X, sample_weight)
        obj.ultimate_, obj.apriori_, obj.detrended_ultimate_ = \
            obj._get_ultimate_(X, sample_weight, obj)
        obj.full_triangle_ = obj._get_full_triangle_()
        return obj
