##################################################################################################################################################################################

from . import *
import numpy as np

####################################################################################################################################################################################


class GaussianMLE:
    """
    Maximum Likelihood Estimator for the scale parameter of a Gaussian distribution.
    """

    def __init__(self):
        """
        Initialize the GaussianMLE.
        """

    def __call__(self, data: np.ndarray) -> float:
        """
        Estimate the scale parameter (standard deviation) of the Gaussian distribution from the data.

        Parameters:
        data : np.ndarray
            The observed data samples.

        Returns:
        float
            The estimated scale parameter (standard deviation).
        """
        data = np.asarray(data, float)
        n = len(data)
        if n == 0:
            raise ValueError("Data array is empty; cannot perform estimation.")
        mean = np.mean(data)
        variance = np.sum((data - mean) ** 2) / n
        return np.sqrt(variance)