# %%
import pandas as pd
import requests
import json
import re, string, timeit
import time
import matplotlib.pyplot as plt
import seaborn as sns

# %%
pd.options.display.max_columns = None # show all columns in display

# %%
def get_api_key(api_key_id = "Domain"):
  """
  Get the api key for website accessing.

  Table of key type and key value for privacy.

  Parameters
  ----------
  @api_key_id [string]: Key value in dataframe

  Returns
  -------
  [string]: client_id & client_secret

  """
  # load api keys file
  df_api_keys = pd.read_csv('../../api_keys.csv', header = 'infer')
  
  # return api key if in dataset
  try:
    # get api key from id
    client_id = df_api_keys.loc[df_api_keys['Id'] == api_key_id]['Client'].iloc[0] # get client by id
    client_secret = df_api_keys.loc[df_api_keys['Id'] == api_key_id]['Secret'].iloc[0] # get secret by id
    # return api key
    return client_id, client_secret
  except IndexError:
    # get api key id list
    api_key_id_list = df_api_keys['Id'].unique().tolist()
    # print error message
    print('Cannot map key. Api key id must be one of the following options {0}'.format(api_key_id_list))

# %%
# POST request for token
client_id, client_secret = get_api_key(api_key_id="Domain")
response = requests.post('https://auth.domain.com.au/v1/connect/token', data = {'client_id':client_id,"client_secret":client_secret,"grant_type":"client_credentials","scope":"api_listings_read","Content-Type":"text/json"})
token=response.json()
access_token=token["access_token"]

# %%
property_id="2011575023"
#domain_api_key = get_api_key(api_key_id = "Domain")
# GET Request for ID
url = "https://api.domain.com.au/v1/listings/"+property_id
auth = {"Authorization":"Bearer "+access_token}
request = requests.get(url,headers=auth)
r=request.json()
print(r)
# %%
#get details
da=r['addressParts']
postcode=da['postcode']
suburb=da['suburb']
bathrooms=r['bathrooms']
bedrooms=r['bedrooms']
carspaces=r['carspaces']
property_type=r['propertyTypes']
##area=r['landAreaSqm']
geolocation=r['geoLocation']
print(property_type, postcode, suburb, bedrooms, bathrooms, carspaces, geolocation)

# the below puts all relevant property types into a single string. eg. a property listing can be a 'house' and a 'townhouse'
n=0
property_type_str=""
for p in r['propertyTypes']:
  property_type_str=property_type_str+(r['propertyTypes'][int(n)])
  n=n+1
print(property_type_str) 

# %%
def api_property_list_sold(auth, property_type, bedrooms, bathrooms, suburb, postcode):
  # url for api
  url = "https://api.domain.com.au/v1/listings/residential/_search"

  # enter parameters
  post_fields ={
      "listingType":"Sold",
        "maxPrice":"",
        "pageSize":200,
      "propertyTypes":property_type,
      "minBedrooms":"",
        "maxBedrooms":"",
      "minBathrooms":"",
        "maxBathrooms":"",
      "locations":[
        {
          "state":"",
          "region":"",
          "area":"",
          "suburb":suburb,
          "postCode":postcode,
          "includeSurroundingSuburbs":False
        }
      ]
    }

  # response
  response = requests.post(url,headers=auth,json=post_fields)
  #response = requests.request("GET", url, headers=headers, params=querystring)
  return response.json()

# %%
def process_list_sold_response(response_json):
    """
    Process the list for sale API response.

    Convert each listing to a dataframe, append to a list, and concatenate to one dataframe.

    Parameters
    ----------
    @response_json [dictionary]: API response for list for sale

    Returns
    -------
    [dataframe] Dataframe of all list for sale responses

    """

    # empty dataframe
    dataframe_list = []

    # iterate through each for sale listing
    
    for j in range(len(response_json)):
        response_json[j]['listing']['propertyDetails']
        k = response_json[j]['listing']['propertyDetails'].copy()
        k['id']  = response_json[j]['listing']['id']
        if "soldPrice" in response_json[j]['listing']['soldData']:
            k['sold_price']  = response_json[j]['listing']['soldData']['soldPrice']
        else:
            k['sold_price']  = "NA"
        #k['sold_price'] = response.json[j]['listing']['hasVideo']
        # convert each listing to dataframe 
        _temp_df = pd.DataFrame.from_dict(k, orient='index').T

        # append to dataframe list for all listings
        dataframe_list.append(_temp_df)
    
        # concatenate all dataframes, for missing col values enter null value
    return pd.concat(dataframe_list, axis=0, ignore_index=True, sort=False)

# %%
property_list_sold_response = api_property_list_sold(auth, property_type, bedrooms, bathrooms, suburb, postcode)
property_list_sold_response[0:3]

# %%
df_properties_sold_raw = process_list_sold_response(response_json=property_list_sold_response)
df_properties_sold_raw = df_properties_sold_raw.drop(['allPropertyTypes','buildingArea'], axis = 1)
df_properties_sold_raw = df_properties_sold_raw[df_properties_sold_raw.sold_price !="NA"]
df_properties_sold_raw = df_properties_sold_raw.dropna()
df_properties_sold_raw.landArea = df_properties_sold_raw.landArea.astype(int)
df_properties_sold_raw.sold_price = df_properties_sold_raw.sold_price.astype(int)
df_properties_sold_raw.bathrooms = df_properties_sold_raw.bathrooms.astype(int)
df_properties_sold_raw.bedrooms = df_properties_sold_raw.bedrooms.astype(int)
df_properties_sold_raw.carspaces = df_properties_sold_raw.carspaces.astype(int)
df_properties_sold_raw['URL'] = 'http://www.domain.com.au/' + df_properties_sold_raw.id.apply(str)

# %%

df_properties_sold_raw.to_csv("output/Sold_Properties.csv", index = False)

# %%
def make_clickable(val):
    # target _blank to open new window
    return '<a target="_blank" href="{}"">{}</a>'.format(val, val)

# %%
df_properties_sold = df_properties_sold_raw.style.format({'URL': make_clickable})
df_properties_sold

# %%
df_properties_sold_raw.sold_price.describe()

# %%
import matplotlib.pyplot as plt

corrmat = df_properties_sold_raw.corr()
f, ax = plt.subplots(figsize=(12, 9))
sns.heatmap(corrmat, vmax=.8, square=True);

# %%
import plotly.express as px

fig = px.scatter_mapbox(df_properties_sold_raw, lat="latitude", lon="longitude", hover_name="id",size = "sold_price", hover_data=["propertyType", "bedrooms", "bathrooms", "landArea"],zoom=15, height=600)
fig.update_layout(mapbox_style="open-street-map")
fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
fig.show()

