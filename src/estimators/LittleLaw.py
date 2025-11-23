##################################################################################################################################################################################

from . import *

####################################################################################################################################################################################

# Little's Law Estimator
class LittleLawEstimator:
    """
    **INTUITION** : \n
    Estimator based on Little Law: L = λ W
    with:\n
    L = Average number of items in the system (average number of detected particles)
    λ = Average arrival rate (detection rate)
    W = Average time an item spends in the system (average time a particle is detectable)
    """

    def __init__(self):
        """
        Initialize the LittleLawEstimator with static analysis data.

        Parameters:
        static_analysis : StaticAnalysisExtraction
            The static analysis data containing detection records.
        """

    def mean_occupation(self , occupation_array : np.ndarray ) -> float:
        """
        Estimate the mean occupation from an occupation array.
        """
        return np.mean(occupation_array)
    
    def residence_time(self , residence_times : np.ndarray ) -> float:
        """
        Estimate the average residence time from an array of residence times.
        """
        return 1/np.mean(1/residence_times)

    def __call__(self, occupation_array: np.ndarray, residence_times: np.ndarray) -> float:
        """
        Estimate the average number of items in the system (L).
        """
        return self.mean_occupation(occupation_array) / self.residence_time(residence_times)