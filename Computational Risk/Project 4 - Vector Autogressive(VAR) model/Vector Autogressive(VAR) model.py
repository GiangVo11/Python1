#
# ================================================
# Computational Risk and Asset Management WS 17/18
# Problem Set 4, Week 4 TEMPLATE
# Vector Autoregressive (VAR) Models
# ================================================
#
# Prepared by Elmar Jakobs
#
# by Hang Do Thi Giang and Lotta Rüter







# Vector Autoregressive (VAR) Models
# ==================================


# Setup
# -----

# Import packages for econometric analysis
#
import numpy as np
import pandas as pd

from scipy.linalg import cholesky

import statsmodels.api as sm
import statsmodels.formula.api as smf
import statsmodels.tsa.api as tsa


# Plotting library
#
import matplotlib
import matplotlib.pyplot as plt
matplotlib.style.use('ggplot')



# Import and configure the testing framework
#
from test_suite import Test
# For submission, please change the status to 'SOLN'
status = 'SOLN'

if status == 'SOLN':
    checker_results = pd.read_csv('results_ps4.csv').set_index('Task')







# Vector Autoregressive (VAR) Models
# ==================================


# Question 1a: Treasury Yields
# ----------------------------


# TODO: Read-in provided text-file with daily Treasury yields
#   Hint: Set the sep = '\s*' attribute of the read_table function
#
yields = pd.read_table('treasury_yields.txt', sep = '\s*')
yields[0:5]



# TODO: Plot time series of yields
#
yields_df         = pd.DataFrame(yields)
yields_df['Date'] = pd.to_datetime(yields_df['Date'], format = '%m/%d/%y')       # Convert the dates
yields_df         = yields_df.set_index('Date')     # Set dates as index
yields_df

yields_df.plot(figsize=(15,6))                 # Plot yields




# TODO: Choose a subset of yields for short/ intermediate and long maturity from 1995 onwards
#
yields_sub = yields_df.iloc[1250:4714, [3,6,8]]
yields_sub.head()
yields_sub.tail()

yields_sub.plot(figsize=(15,6))



# For further analysis: Take monthly values of yields
#
yields_sub_eom = yields_sub.resample('M').bfill()
yields_sub_eom.head()
yields_sub_eom.tail()


yields_sub_eom.plot(figsize=(15,6))




# Check of intermediate result (1):
#
Test.assertEquals(np.round(yields_sub_eom.iloc[0][0],2), 6.84, 'incorrect result')
Test.assertEquals(np.round(yields_sub_eom.iloc[0][1],2), 7.54, 'incorrect result')
if status == 'SOLN':
    Test.assertEquals(np.round(yields_sub_eom.iloc[0][2], 2), checker_results.loc[1][0], 'incorrect result')
    Test.assertEquals(np.round(yields_sub_eom.iloc[1][2], 2), checker_results.loc[2][0], 'incorrect result')








# Question 1b: Macroeconomic Data
# -------------------------------


# FRED Database
#   Unemployment: https://fred.stlouisfed.org/series/UNRATE
#   Inflation   : https://fred.stlouisfed.org/series/CPIAUCSL
#


# TODO: First, read-in unemployment rate
#
unempl         = pd.read_csv('UNRATE.csv')      # Read-in file
unempl['DATE'] = pd.to_datetime(unempl['DATE'], format = '%Y-%m-%d')      # Format date
unempl         = unempl.set_index('DATE')      # Set index
unempl.head()


# TODO: Second, read-in inflation rate
#
infl         = pd.read_csv('CPIAUCSL.csv')        # Read-in file
infl['DATE'] = pd.to_datetime(infl['DATE'], format = '%Y-%m-%d')        # Format date
infl         = infl.set_index('DATE')        # Set index
infl.head()


# TODO: Join macro data
#   Hint: '.join' the unempl data frame with the inflation data frame
#
macro_all = unempl.join(infl)
macro_all


# Set end of month day
#
macro_all_eom = macro_all.resample('M').ffill()
macro_all_eom.head()


# TODO: Plot macro data
#
macro_all_eom.plot(figsize=(15,6))



# TODO: Join macro data with yields
#   Hint: Take the resampled data
#
data_all = macro_all_eom.join(yields_sub_eom)
data_all = data_all.dropna( axis = 0 )
data_all





# Check of intermediate result (2):
#
Test.assertEquals(np.round(data_all.iloc[0][0],2), 5.60, 'incorrect result')
Test.assertEquals(np.round(data_all.iloc[0][1],2), 2.87, 'incorrect result')
if status == 'SOLN':
    Test.assertEquals(np.round(data_all.iloc[0][2], 2), checker_results.loc[3][0], 'incorrect result')
    Test.assertEquals(np.round(data_all.iloc[0][3], 2), checker_results.loc[4][0], 'incorrect result')






# Question 1c+e: Class VAR
# ------------------------


# Helper Function
#   Goal: Produce a matrix with lagged data: (Xt-1 Yt-1 ... Xt-2 Yt-2 ...)
#
def mat_lag(data, lags, drop_nan = True):

    for i in range(1, lags+1):

        lag = data.shift(i)


        if i == 1:

            all = lag

        else:

            lsuff = '_l' + str(i-1)
            rsuff = '_r' + str(i)

            all = all.join(lag, lsuffix = lsuff, rsuffix = rsuff )


    if drop_nan == True:

        all = all.dropna(axis = 0)

    return all



# Test function
#
print(mat_lag(yields_sub, 2).head())
print(yields_sub.head())




# Object-oriented
#
class VAR(object):


    def __init__(self, data, lags, const = True):

        self.Y = np.matrix(data.ix[lags:])

        self.X = np.matrix(mat_lag(data, lags))

        self.i = int(self.X.shape[1])


        if (const == True):

             self.X = np.insert(self.X, obj = 0, values = 1, axis = 1)


        self.nobs       = int(self.X.shape[0])
        self.nvar       = int(self.X.shape[1])

        self.betas      = np.empty(self.i*self.nvar).reshape(self.i, self.nvar)
        self.tstats     = np.empty(self.i*self.nvar).reshape(self.i, self.nvar)

        self.resid      = np.empty(self.i*self.nobs).reshape(self.nobs, self.i)

        self.adj_rsqr   = np.empty(self.i)




    def estimate_VAR(self, summary = True):


        # TODO: Run OLS estimation row by row

        for i in range(0, self.i):
            model = sm.OLS(self.Y[:, i], self.X)
            results = model.fit()

            betas = results.params
            tstats = results.tvalues
            epsilon = results.resid
            adj_rsqr = results.rsquared_adj


            # Set object variables
            #
            self.betas[i, :]  = betas.reshape(self.nvar,)
            self.tstats[i, :] = tstats.reshape(self.nvar,)
            self.resid[:, i]  = epsilon.reshape(self.nobs,)
            self.adj_rsqr[i]  = adj_rsqr



        # TODO: Calculate covariance (correlation) matrix of the error terms
        #
        self.Cov  = np.cov(np.matrix(self.resid).getT(), rowvar = True)
        self.Corr = np.corrcoef(np.matrix(self.resid).getT())


        # Print results
        #
        if (summary == True):

            for i in range(self.i):

                print('Betas:             ', np.round(self.betas[i,:], 3))
                print('t-stats:           ', np.round(self.tstats[i,:], 2))
                print('')

            print('Corr of residuals: ', np.round(self.Corr, 3) )


        return self.betas, self.tstats, self.resid, self.Cov, self.Corr





    def calc_IRF(self, nPe):

        # First, estimate the VAR
        #
        self.estimate_VAR( summary = False )


        # TODO: Create 'np.matrix' of autoregressive coefficients A (betas)
        #
        A = np.matrix(self.betas)


        # TODO: Calculate Cholesky decomposition of covariance matrix
        #  -> C
        #  Hint: Use the 'cholesky' function of the scipy package (set 'lower = True')
        #
        C = cholesky(self.Cov, lower=True)


        # TODO: Assign dimension (number of variables)
        #  Hint: Use the '.shape' function 
        #
        nvar = A.shape[1]


        # Initialize variable to store result
        #
        IRF = np.zeros( (nvar, nvar, nPe) )


        # TODO: Assign the first response
        #
        IRF[:,:,0] = C


        # TODO: Iterate over all periods A^t * C
        #
        for h in range(1, nPe):
            IRF[:, :, h] = (A ** h) * C

        return IRF






# Question 1d: VAR Estimation
# ---------------------------


# TODO: Demean data
#
data_all['UNRATE_dm']   = data_all['UNRATE'] - data_all['UNRATE'].mean()
data_all['CPIAUCSL_dm'] = data_all['CPIAUCSL'] - data_all['CPIAUCSL'].mean()
data_all['1yr_dm']      = data_all['1yr'] - data_all['1yr'].mean()
data_all['5yr_dm']      = data_all['5yr'] - data_all['5yr'].mean()
data_all['10yr_dm']     = data_all['10yr'] - data_all['10yr'].mean()
data_all


# TODO: Select demeaned data for VAR estimation
#
data_all_dm = data_all[ ['UNRATE_dm', 'CPIAUCSL_dm', '10yr_dm', '5yr_dm', '10yr_dm'] ].copy()
data_all_dm.head()



# TODO: Run VAR estimation (without constant)
#
var1     = VAR(data_all_dm, 1, const = False)       # Initialize object
var1_est = var1.estimate_VAR()      # Run estimation method

var1_betas  = var1.betas
var1_tstats = var1.tstats


# Double check with statsmodels package
#
model   = tsa.VAR(np.matrix( data_all_dm) )
results = model.fit(1, trend = 'nc')
results.summary()





# Check of intermediate result (3/4):
#
Test.assertEquals(np.round(var1_betas[0,0],2), 0.92, 'incorrect result')
Test.assertEquals(np.round(var1_tstats[0,0],2), 33.24, 'incorrect result')
if status == 'SOLN':
    Test.assertEquals(np.round(var1_betas[2,0], 2),  checker_results.loc[5][0], 'incorrect result')
    Test.assertEquals(np.round(var1_tstats[2,0], 2), checker_results.loc[6][0], 'incorrect result')






# Question 1f: Impulse Response Function
# --------------------------------------


# TODO: Calculate IRF for 60 periods (5 years)
#
var_1f     = VAR( data_all_dm, 1, False )
var_1f_irf = var_1f.calc_IRF(60)      # Run 'calc_IRF' function



# TODO: Plot IRF - Unempl -> Unempl
#
plt.figure()
plt.ylim(-0.05, 0.15)
plt.hlines(0, 0, 60 )
plt.plot(var_1f_irf[0, 0, :])


# TODO: Plot IRF - Unempl -> 1 yr Yield
#
plt.figure()
plt.ylim(-0.10, 0.10)
plt.hlines(0, 0, 60 )
plt.plot(var_1f_irf[0, 2, :])


# TODO: Plot IRF - Unempl -> 5 yr Yield
#
plt.figure()
plt.ylim(-0.10, 0.10)
plt.hlines(0, 0, 60 )
plt.plot(var_1f_irf[0, 3, :])


# TODO: Plot IRF - Unempl -> 10 yr Yield
#
plt.figure()
plt.ylim(-0.10, 0.10)
plt.hlines(0, 0, 60 )
plt.plot(var_1f_irf[0, 4, :])




# Double check with statsmodels package
#
model_   = tsa.VAR( np.matrix(data_all_dm) )
results = model.fit(1, trend = 'nc')

irf = results.irf(60)


irf.plot(impulse = 'y1', response = 'y1', orth = True)
irf.plot(impulse = 'y1', response = 'y3', orth = True)
irf.plot(impulse = 'y1', response = 'y4', orth = True)
irf.plot(impulse = 'y1', response = 'y5', orth = True)




# TODO: Set variable to 1 (True) or 0 (False)
#
unempl_affects_unempl            = 1
unempl_affects_short_term_yield  = 0
unempl_affects_medium_term_yield = 0
unempl_affects_longterm_yield    = 0




# Check of intermediate result (5/6):
#
Test.assertEquals(np.round(var_1f_irf[0,0,0],4), 0.1323, 'incorrect result')
Test.assertEquals(np.round(var_1f_irf[0,0,1],4), 0.1234, 'incorrect result')
Test.assertEquals(np.round(var_1f_irf[0,0,2],4), 0.1153, 'incorrect result')
Test.assertEquals(np.round(var_1f_irf[0,0,3],4), 0.1080, 'incorrect result')
if status == 'SOLN':
    Test.assertEquals(unempl_affects_unempl,            checker_results.loc[7][0], 'incorrect result')
    Test.assertEquals(unempl_affects_short_term_yield,  checker_results.loc[8][0], 'incorrect result')
    Test.assertEquals(unempl_affects_medium_term_yield, checker_results.loc[9][0], 'incorrect result')
    Test.assertEquals(unempl_affects_longterm_yield,    checker_results.loc[10][0], 'incorrect result')








print(Test.passed, "tests passed of", Test.numTests,  "(", 100*Test.passed/Test.numTests, "%)")









