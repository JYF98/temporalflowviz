import re
import numpy as np

class Embedding:
    def __init__(self, emb, fname):
        self.emb = emb
        self.fname = fname
        self.case = '_'.join(fname.split('_')[0:-2])
        self.variable = re.search(r'_([a-zA-Z]+)_', fname).group(1)
        self.time = int(re.search(r'([0-9.]+)ms', fname).group(1))
        self.label = -1
        self.xy = np.array((0,2))
        self.p, self.t, self.h2o = self.findValues()
        self.description = None
        self.iscentroid = False
        
    def findValues(self):
        # find the value after letter 'f' and before another non-digit character
        p_search = re.search(r'f([0-9.]+)', self.case)
        if p_search is None:
            p = 0.8
        else:
            p = float(p_search.group(1))
        
        # find the value after 't' and before another non-digit character
        t_search = re.search(r't([0-9.]+)', self.case)
        if t_search is None:
            t = 565.48
        else:
            t = float(t_search.group(1))
        
        # find the value after 'h2o' and before another non-digit character
        h2o_search = re.search(r'h2o([0-9.]+)', self.case)
        if h2o_search is None:
            h2o = 0.078
        else:
            h2o = float(h2o_search.group(1))

        return p, t, h2o