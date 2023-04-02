# %%
import pandas as pd
import requests
import json
import re, string, timeit
import time
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# %%
pd.set_option('display.max_colwidth', -1)

# %%
df1 = pd.read_csv('output/Sold_Properties.csv')
df1.shape

# %%
df1.head()

# %%
df1["sold_price"].describe()

# %%
import plotly.express as px

fig = px.scatter_mapbox(df1, lat="latitude", lon="longitude", hover_name="id",size = "sold_price", hover_data=["propertyType", "bedrooms", "bathrooms", "landArea", "displayableAddress"],zoom=15, height=600)
fig.update_layout(mapbox_style="open-street-map")
fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
fig.show()

# %%
print("Median price: %f" % df1["sold_price"].median(),",","Mean price: %f" % df1["sold_price"].mean().round())
print("Skewness: %f" % df1["sold_price"].skew(),",", "Kurtosis: %f" % df1["sold_price"].kurt())

# %%
var = 'landArea'
df1.plot.scatter(x=var, y='sold_price', ylim=(0.800000))

# %%
# Remove outliers
df1 = df1.drop(df1[df1['landArea'] >= 2000].index)
df1.plot.scatter(x=var, y='sold_price', ylim=(0.800000))

# %%
from scipy import stats
from scipy.stats import norm, skew
sns.distplot(df1.sold_price, fit=norm)
(mu, sigma) = norm.fit(df1['sold_price'])
print( '\n mu = {:.2f} and sigma = {:.2f}\n'.format(mu, sigma))

#Now plot the distribution
plt.legend(['Normal dist. ($\mu=$ {:.2f} and $\sigma=$ {:.2f} )'.format(mu, sigma)],loc='upper center')
plt.ylabel('Frequency')
plt.title('SoldPrice distribution')

#Get also the QQ-plot
fig = plt.figure()
res = stats.probplot(df1['sold_price'], plot=plt)
plt.show()

# %%
data = df1.copy()

# %%
#applying log transformation
data['sold_price'] = np.log(data['sold_price'])
#transformed histogram and normal probability plot
sns.distplot(data['sold_price'], fit=norm);
fig = plt.figure()
res = stats.probplot(data['sold_price'], plot=plt)

# %%
from sklearn.linear_model import ElasticNet, Lasso,  BayesianRidge, LassoLarsIC
from sklearn.ensemble import RandomForestRegressor,  GradientBoostingRegressor
from sklearn.kernel_ridge import KernelRidge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import RobustScaler
from sklearn.base import BaseEstimator, TransformerMixin, RegressorMixin, clone
from sklearn.model_selection import KFold, cross_val_score, train_test_split
from sklearn.metrics import mean_squared_error
import xgboost as xgb
import lightgbm as lgb

# %%
#Validation function
n_folds = 5

def rmsle_cv(model):
    kf = KFold(n_folds, shuffle=True, random_state=42).get_n_splits(x_train.values)
    rmse= np.sqrt(-cross_val_score(model, x_train.values, y_train, scoring="neg_mean_squared_error", cv = kf))
    return(rmse)

# %%
x_train, x_test, y_train, y_test = train_test_split(data[['bedrooms','bathrooms','carspaces','landArea']], data['sold_price'])
print(x_train.shape, y_train.shape, x_test.shape, y_test.shape)

# %%
lasso = make_pipeline(RobustScaler(), Lasso(alpha =0.0005, random_state=1))
score = rmsle_cv(lasso)
print("\nLasso score: {:.4f} ({:.4f})\n".format(score.mean(), score.std()))

# %%
model_lasso = make_pipeline(RobustScaler(), Lasso(alpha =0.0005, random_state=1)).fit(x_train, y_train)
lasso_preds = np.expm1(model_lasso.predict(x_test))
z = pd.Series(lasso_preds)
print(z.unique)

# %%
ENet = make_pipeline(RobustScaler(), ElasticNet(alpha=0.0005, l1_ratio=.9, random_state=3))
score = rmsle_cv(ENet)
print("\nEnet score: {:.4f} ({:.4f})\n".format(score.mean(), score.std()))


# %%
KRR = KernelRidge(alpha=0.6, kernel='polynomial', degree=2, coef0=2.5)
score = rmsle_cv(KRR)
print("\nKRR score: {:.4f} ({:.4f})\n".format(score.mean(), score.std()))

# %%
GBoost = GradientBoostingRegressor(n_estimators=3000, learning_rate=0.05,
                                   max_depth=4, max_features='sqrt',
                                   min_samples_leaf=15, min_samples_split=10, 
                                   loss='huber', random_state =5)
score = rmsle_cv(GBoost)
print("\nGBoost score: {:.4f} ({:.4f})\n".format(score.mean(), score.std()))

# %%
model_xgb = xgb.XGBRegressor(colsample_bytree=0.4603, gamma=0.0468, 
                             learning_rate=0.05, max_depth=3, 
                             min_child_weight=1.7817, n_estimators=2200,
                             reg_alpha=0.4640, reg_lambda=0.8571,
                             subsample=0.5213, silent=1,
                             random_state =7, nthread = -1)
score = rmsle_cv(model_xgb)
print("\nmodel_xgb score: {:.4f} ({:.4f})\n".format(score.mean(), score.std()))

# %%
model_lgb = lgb.LGBMRegressor(objective='regression',num_leaves=5,
                              learning_rate=0.05, n_estimators=720,
                              max_bin = 55, bagging_fraction = 0.8,
                              bagging_freq = 5, feature_fraction = 0.2319,
                              feature_fraction_seed=9, bagging_seed=9,
                              min_data_in_leaf =6, min_sum_hessian_in_leaf = 11)
score = rmsle_cv(model_lgb)
print("\nmodel_lgb score: {:.4f} ({:.4f})\n".format(score.mean(), score.std()))

# %%
model_lgb = lgb.LGBMRegressor(objective='regression',num_leaves=5,
                              learning_rate=0.05, n_estimators=720,
                              max_bin = 55, bagging_fraction = 0.8,
                              bagging_freq = 5, feature_fraction = 0.2319,
                              feature_fraction_seed=9, bagging_seed=9,
                              min_data_in_leaf =6, min_sum_hessian_in_leaf = 11).fit(x_train, y_train)
lgb_preds = np.expm1(model_lgb.predict(x_test))
z = pd.Series(lgb_preds)
print(z.round(0).unique())

# %%
# Define R2
def adjustedR2(r2,n,k):
    return r2-(k-1)/(n-k)*(1-r2)

# %%
df2 = pd.read_csv("ForSale_Properties.csv")
df2.head()

# %%
df2.shape

# %%
X = df2[['bathrooms','bedrooms','carspaces','landArea']]
X.head()

# %%
df2['Price (estimated)'] = np.expm1(model_lasso.predict(X))
df2['Price (estimated)'] = df2['Price (estimated)'].astype(int)
len(df2['Price (estimated)'].round(0).unique())

# %%
df2.head()

# %%
import plotly.express as px

fig = px.scatter_mapbox(df2, lat="latitude", lon="longitude", hover_name="id", color = "Price (estimated)", size = "landArea", hover_data=["propertyType", "bedrooms", "bathrooms", "displayableAddress"],zoom=15, height=600)
fig.update_layout(mapbox_style="open-street-map")
fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
fig.show()

