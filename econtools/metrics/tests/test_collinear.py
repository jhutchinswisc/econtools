import pandas as pd
import numpy as np
from econtools.metrics import reg

X = pd.DataFrame(np.stack([np.array([1]*10),np.array([0,1]*5),np.array([1,0]*5)]).T)
beta = np.array([1,2,3])
y = X@beta

data = pd.DataFrame(X)
data.columns = ['cons','x1','x2']
data['y'] = y

# This is fine
reg(data,'y',['cons','x1'])

# This should not be fine
reg(data,'y',['cons','x1','x2'])