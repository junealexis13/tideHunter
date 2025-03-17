from enum import Enum
import numpy as np
import pandas as pd

class Lists(Enum):
    ACCEPTED_UPLOAD_FORMATS = ['LEV','COR','RAW','DEC']

class Keys(Enum):
    SINGLE = "SN"
    MULTIPLE = 'MT'

class Tools:
    @staticmethod
    def get_linear_regression(x, y):
        '''Get the linear regression of the given x and y values'''

        x = np.array(x, dtype=np.float64)
        y = np.array(y, dtype=np.float64)
        m, b = np.polyfit(x, y, 1)

        # return y_pred
        y_pred = m * x + b
        return y_pred,m, b