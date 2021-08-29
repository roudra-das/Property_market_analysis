#  Extracting data on Sold properties with Domain api
# Just the code

# %%
import pandas as pd
import requests
import json
import re, string, timeit
import time

pd.options.display.max_columns = None # show all columns in display

# %%
## Functions
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
  df_api_keys = pd.read_csv('~/Documents/Python/api_keys.csv', header = 'infer')
  
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
def api_property_list_for_sale(auth, property_type, bedrooms, bathrooms, suburb, postcode):
  # url for api
  url = "https://api.domain.com.au/v1/listings/residential/_search"

  # enter parameters
  post_fields ={
      "listingType":"Sale",
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
def process_list_for_sale_response(response_json):
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
        #response_json[j]['listing']['propertyDetails'].pop('features')
        k = response_json[j]['listing']['propertyDetails'].copy()
        k['id']  = response_json[j]['listing']['id']
        print(k)
        # convert each listing to dataframe 
        _temp_df = pd.DataFrame.from_dict(k, orient='index').T

        # append to dataframe list for all listings
        dataframe_list.append(_temp_df)
    
        # concatenate all dataframes, for missing col values enter null value
    return pd.concat(dataframe_list, axis=0, ignore_index=True, sort=False)

# %%
# setup
property_id="2016858650"
starting_max_price=100000
increment=50000
# when starting min price is zero we'll just use the lower bound plus 400k later on
starting_min_price=0
# POST request for token
client_id, client_secret = get_api_key(api_key_id="Domain")
response = requests.post('https://auth.domain.com.au/v1/connect/token', data = {'client_id':client_id,"client_secret":client_secret,"grant_type":"client_credentials","scope":"api_listings_read","Content-Type":"text/json"})
token=response.json()
access_token=token["access_token"]
#domain_api_key = get_api_key(api_key_id = "Domain")
# GET Request for ID
url = "https://api.domain.com.au/v1/listings/"+property_id
auth = {"Authorization":"Bearer "+access_token}
request = requests.get(url,headers=auth)
r=request.json()
#get details
da=r['addressParts']
postcode=da['postcode']
suburb=da['suburb']
bathrooms=r['bathrooms']
bedrooms=r['bedrooms']
carspaces=r['carspaces']
property_type=r['propertyTypes']
area=r['landAreaSqm']
geolocation=r['geoLocation']

print(property_type, postcode, suburb, bedrooms, bathrooms,  carspaces, area, geolocation)

# the below puts all relevant property types into a single string. eg. a property listing can be a 'house' and a 'townhouse'
# %%
n=0
property_type_str=""
for p in r['propertyTypes']:
  property_type_str=property_type_str+(r['propertyTypes'][int(n)])
  n=n+1
print(property_type_str) 

property_list_for_sale_response = api_property_list_for_sale(auth, property_type, bedrooms, bathrooms, suburb, postcode)
property_list_for_sale_response[:5]
df_properties_for_sale_raw = process_list_for_sale_response(response_json=property_list_for_sale_response)

df_properties_for_sale_raw
def make_clickable(val):
    # target _blank to open new window
    return '<a target="_blank" href="{}"">{}</a>'.format(val, val)
df_properties_for_sale_raw.shape
df_properties_for_sale_raw.to_csv("output/ForSale_Properties.csv", index = False)
from sklearn.cluster import DBSCAN


df_properties_for_sale_raw["labels"] = DBSCAN(eps=0.01, min_samples=3).fit(df_properties_for_sale_raw[["latitude","longitude"]].values).labels_
df_properties_for_sale_raw = df_properties_for_sale_raw.drop(['allPropertyTypes','buildingArea'], axis = 1)
df_properties_for_sale_raw = df_properties_for_sale_raw.dropna()
df_properties_for_sale_raw.landArea = df_properties_for_sale_raw.landArea.astype(int)
df_properties_for_sale_raw.bathrooms = df_properties_for_sale_raw.bathrooms.astype(int)
df_properties_for_sale_raw.bedrooms = df_properties_for_sale_raw.bedrooms.astype(int)
df_properties_for_sale_raw.carspaces = df_properties_for_sale_raw.carspaces.astype(int)
df_properties_for_sale_raw['URL'] = 'http://www.domain.com.au/' + df_properties_for_sale_raw.id.apply(str)
df_properties_for_sale_raw = df_properties_for_sale_raw.drop(df_properties_for_sale_raw[df_properties_for_sale_raw["landArea"] > 2000].index)
df_properties_for_sale = df_properties_for_sale_raw.style.format({'URL': make_clickable})
df_properties_for_sale
def search_for_price(data, starting_min_price, starting_max_price, increment):
    
    url = "https://api.domain.com.au/v1/listings/residential/_search" # Set destination URL here

    max_price=starting_max_price

    searching_for_price_l = True
    while searching_for_price_l:
        post_fields ={
        "listingType":"Sale",
            "maxPrice":max_price,
            "pageSize":100,
        "propertyTypes":['house'],
        "minBedrooms":data['bedrooms'],
            "maxBedrooms":data['bedrooms'],
        "minBathrooms":data['bathrooms'],
            "maxBathrooms":data['bathrooms'],
        "locations":[
            {
            "state":"",
            "region":"",
            "area":"",
            "suburb":data['suburb'],
            "postCode":data['postcode'],
            "includeSurroundingSuburbs":False
            }
        ]
        }

        request = requests.post(url,headers=auth,json=post_fields)

        l=request.json()
        listings = []
        for listing in l:
            listings.append(listing["listing"]["id"])
        listings

        if int(property_id) in listings:
                max_price=max_price-increment
                print("Lower bound found: ", max_price)
                searching_for_price_l=False
        else:
            max_price=max_price+increment
            print("Not found. Increasing max price to ",max_price)
            time.sleep(0.1)  # sleep a bit so you don't make too many API calls too quickly )


    if starting_min_price>0:
            min_price=starting_min_price
            
    else:  
            min_price=max_price+400000


    searching_for_price_u = True
    while searching_for_price_u:
        post_fields ={
        "listingType":"Sale",
            "minPrice":min_price,
            "pageSize":100,
        "propertyTypes":['house'],
        "minBedrooms":data['bedrooms'],
            "maxBedrooms":data['bedrooms'],
        "minBathrooms":data['bathrooms'],
            "maxBathrooms":data['bathrooms'],
        "locations":[
            {
            "state":"",
            "region":"",
            "area":"",
            "suburb":data['suburb'],
            "postCode":data['postcode'],
            "includeSurroundingSuburbs":False
            }
        ]
        }

        request = requests.post(url,headers=auth,json=post_fields)

        l=request.json()
        listings = []
        for listing in l:
            listings.append(listing["listing"]["id"])
        listings

        if int(property_id) in listings:
                min_price=min_price+increment
                print("Upper bound found: ", min_price)
                searching_for_price_u=False
        else:
            min_price=min_price-increment
            print("Not found. Decreasing min price to ",min_price)
            time.sleep(0.1)  # sleep a bit so you don't make too many API calls too quickly )

        if max_price<1000000:
            lower=max_price/1000
            upper=min_price/1000
            denom="k"
        else: 
            lower=max_price/1000000
            upper=min_price/1000000
            denom="m"
    

    return print("Price range:","$",lower,"-","$",upper,denom)

# %% 
# Plots
import plotly.express as px

fig = px.scatter_mapbox(df_properties_for_sale_raw, lat="latitude", lon="longitude", size = "landArea", hover_name="URL", hover_data=["propertyType", "bedrooms", "bathrooms", "landArea", "displayableAddress"],zoom=15, height=600)
fig.update_layout(mapbox_style="open-street-map")
fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
fig.show()
# End of Notebook