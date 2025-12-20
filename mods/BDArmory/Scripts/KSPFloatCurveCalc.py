import numpy as np
import warnings

class FloatCurve:
    """
    Implements KSP FloatCurves in Python.
    Initialize via a list of keys in the form of numpy ndarrays (either 2 or 4 long).
    Evaluate(x) functions as in KSP
    EvaluateArray(arr) will take a list/ndarray of x values and return a ndarray.
    """
    def __init__(self, inKeys: list[np.ndarray]):
        self.numKeys = len(inKeys)
        for i in range(self.numKeys):
            # Deal with keys that aren't of size 4
            if (inKeys[i].shape[0] < 4):
                if (inKeys[i].shape[0] == 1):
                    # If only 1 value is given, then use that as the x and default to a value of 0
                    inKeys[i] = np.array([inKeys[i][0], 0, 0, 0])
                    warnings.warn(f'ERROR! Key: {i} is of length 1, defaulting to a value of 0!')
                if (inKeys[i].shape[0] == 3):
                    # If 3 values are given, default to 0, 0 slopes
                    warnings.warn(f'ERROR! Key: {i} is of length 3, defaulting to 0, 0 slopes')
                # Unity/KSP defaults keys of length 2 to 0, 0 slopes
                inKeys[i] = np.array([inKeys[i][0], inKeys[i][1], 0, 0])
        self.keys = np.array(inKeys)
        # Sort keys to enable binary search
        self.keys[self.keys[:,0].argsort()]
    
    def Evaluate(self, x):
        # Find index where the p1x < x
        indexL = np.searchsorted(self.keys[:,0], x, side='right') - 1
        if (indexL == self.numKeys - 1):
            # If we've reached the end, then just return the value at the end
            return self.keys[-1,1]
        return self.__Evaluate(x,
                               self.keys[indexL,0], self.keys[indexL,1], self.keys[indexL,3],
                               self.keys[indexL+1,0], self.keys[indexL+1,1], self.keys[indexL+1,2])
    
    def EvaluateArray(self, arr):
        results = []
        for x in arr:
            # Find index where the p1x < x
            indexL = np.searchsorted(self.keys[:,0], x, side='right') - 1
            if (indexL == self.numKeys - 1):
                # If we've reached the end, then just return the value at the end
                results.append(self.keys[-1,1])
            else:
                results.append(self.__Evaluate(x,
                                               self.keys[indexL,0], self.keys[indexL,1], self.keys[indexL,3],
                                               self.keys[indexL+1,0], self.keys[indexL+1,1], self.keys[indexL+1,2]))
        return np.array(results)
    
    @staticmethod
    def __Evaluate(x, p1x, p1y, tp1, p2x, p2y, tp2):
        # Taken from https://discussions.unity.com/t/what-is-the-math-behind-animationcurve-evaluate/72058/4 (because I'm lazy and someone already solved the system)
        a = (p1x * tp1 + p1x * tp2 - p2x * tp1 - p2x * tp2 - 2 * p1y + 2 * p2y) / (p1x * p1x * p1x - p2x * p2x * p2x + 3 * p1x * p2x * p2x - 3 * p1x * p1x * p2x)
        b = ((-p1x * p1x * tp1 - 2 * p1x * p1x * tp2 + 2 * p2x * p2x * tp1 + p2x * p2x * tp2 - p1x * p2x * tp1 + p1x * p2x * tp2 + 3 * p1x * p1y - 3 * p1x * p2y + 3 * p1y * p2x - 3 * p2x * p2y) / (p1x * p1x * p1x - p2x * p2x * p2x + 3 * p1x * p2x * p2x - 3 * p1x * p1x * p2x))
        c = ((p1x * p1x * p1x * tp2 - p2x * p2x * p2x * tp1 - p1x * p2x * p2x * tp1 - 2 * p1x * p2x * p2x * tp2 + 2 * p1x * p1x * p2x * tp1 + p1x * p1x * p2x * tp2 - 6 * p1x * p1y * p2x + 6 * p1x * p2x * p2y) / (p1x * p1x * p1x - p2x * p2x * p2x + 3 * p1x * p2x * p2x - 3 * p1x * p1x * p2x))
        d = ((p1x * p2x * p2x * p2x * tp1 - p1x * p1x * p2x * p2x * tp1 + p1x * p1x * p2x * p2x * tp2 - p1x * p1x * p1x * p2x * tp2 - p1y * p2x * p2x * p2x + p1x * p1x * p1x * p2y + 3 * p1x * p1y * p2x * p2x - 3 * p1x * p1x * p2x * p2y) / (p1x * p1x * p1x - p2x * p2x * p2x + 3 * p1x * p2x * p2x - 3 * p1x * p1x * p2x))
        return a * x * x * x + b * x * x + c * x + d