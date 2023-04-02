# %%
import json
import requests # this library is awesome: http://docs.python-requests.org/en/master/
import re, string, timeit
import time
import pandas as pd
import sys

# %%
# setup
property_id="2016836733"
starting_max_price=100000
increment=50000
# when starting min price is zero we'll just use the lower bound plus 400k later on
starting_min_price=0
# Max price you are willing to pay
budget = 1000000


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

def json_to_dataframe(response):
    """
    Convert response to dataframe
    """
    return pd.DataFrame(response.json()[1:], columns=response.json()[0])

# %%
# POST request for token
client_id, client_secret = get_api_key(api_key_id="Domain")
response = requests.post('https://auth.domain.com.au/v1/connect/token', data = {'client_id':client_id,"client_secret":client_secret,"grant_type":"client_credentials","scope":"api_listings_read","Content-Type":"text/json"})
token=response.json()
access_token=token["access_token"]

# GET Request for ID
url = "https://api.domain.com.au/v1/listings/"+property_id
auth = {"Authorization":"Bearer "+access_token}
request = requests.get(url,headers=auth)
r=request.json()
#print(r)

# %%
## Get details
da=r['addressParts']
postcode=da['postcode']
suburb=da['suburb']
bathrooms=r['bathrooms']
bedrooms=r['bedrooms']
carspaces=r['carspaces']
property_type=r['propertyTypes']
area=r['landAreaSqm']
geolocation=r['geoLocation']
# the below puts all relevant property types into a single string. eg. a property listing can be a 'house' and a 'townhouse'
n=0
property_type_str=""
for p in r['propertyTypes']:
  property_type_str=property_type_str+(r['propertyTypes'][int(n)])
  n=n+1

print(property_type_str,postcode, suburb, "Beds:", bedrooms, "Baths:", bathrooms, "Car spaces:", carspaces, area, geolocation)

# %%
max_price=starting_max_price
searching_for_price=True
# Start your loop
while searching_for_price:
    
    url = "https://api.domain.com.au/v1/listings/residential/_search" # Set destination URL here
    post_fields ={
      "listingType":"Sale",
        "maxPrice":max_price,
        "pageSize":100,
      "propertyTypes":property_type,
      "minBedrooms":bedrooms,
        "maxBedrooms":bedrooms,
      "minBathrooms":bathrooms,
        "maxBathrooms":bathrooms,
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

    request = requests.post(url,headers=auth,json=post_fields)

    l=request.json()
    listings = []
    for listing in l:
        listings.append(listing["listing"]["id"])
    listings

    if int(property_id) in listings:
            max_price=max_price-increment
            print("Lower bound found: ", max_price)
            searching_for_price=False
    elif max_price >= 1000000:
      sys.exit("Uh Oh! You are priced out in this area!")
      break
    else:
        max_price=max_price+increment
        print("Not found. Increasing max price to ",max_price)
        time.sleep(0.1)  # sleep a bit so you don't make too many API calls too quickly 

# %%
searching_for_price=True
if starting_min_price>0:
  min_price=starting_min_price
else:  
  min_price=max_price+400000 

while searching_for_price:
    
    url = "https://api.domain.com.au/v1/listings/residential/_search" # Set destination URL here
    post_fields ={
      "listingType":"Sale",
        "minPrice":min_price,
        "pageSize":100,
      "propertyTypes":property_type,
      "minBedrooms":bedrooms,
        "maxBedrooms":bedrooms,
      "minBathrooms":bathrooms,
        "maxBathrooms":bathrooms,
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

    request = requests.post(url,headers=auth,json=post_fields)

    l=request.json()
    listings = []

    for listing in l:
        listings.append(listing["listing"]["id"])
    listings

    if int(property_id) in listings:
            min_price=min_price+increment
            print("Upper bound found: ", min_price)
            searching_for_price=False
    else:
        min_price=min_price-increment
        print("Not found. Decreasing min price to ",min_price)
        time.sleep(0.1)  # sleep a bit so you don't make too many API calls too quickly

# %%
if max_price<1000000:
  lower=max_price/1000
  upper=min_price/1000
  denom="k"
else: 
  lower=max_price/1000000
  upper=min_price/1000000
  denom="m"

# %%
# Print the results
print(da['displayAddress'])
print(r['headline'])
print("Property Type:",property_type_str)
print("Details: ",int(bedrooms),"bedroom,",int(bathrooms),"bathroom,",int(carspaces),"carspace", int(area),"sqm")
print("Geocode: ", geolocation)
print("Display price:",r['priceDetails']['displayPrice'])      
if max_price==min_price:
  print("Price guide:","$",lower,denom)
else:
  print("Price range:","$",lower,"-","$",upper,denom)
print("URL:",r['seoUrl'])

# %%
min_price = 0
def search_for_price(property_type, bedrooms, bathrooms, suburb, postcode, starting_min_price, starting_max_price, increment):
    
    url = "https://api.domain.com.au/v1/listings/residential/_search" # Set destination URL here

    max_price=starting_max_price

    searching_for_price_l = True
    while searching_for_price_l:
        post_fields ={
        "listingType":"Sale",
            "maxPrice":max_price,
            "pageSize":100,
        "propertyTypes":property_type,
        "minBedrooms":bedrooms,
            "maxBedrooms":bedrooms,
        "minBathrooms":bathrooms,
            "maxBathrooms":bathrooms,
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
        elif max_price >= 1000000:
            print("Too expensive!")
            break
        else:
            max_price=max_price+increment
            print("Not found. Decreasing min price to ",max_price)
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
        "propertyTypes":property_type,
        "minBedrooms":bedrooms,
            "maxBedrooms":bedrooms,
        "minBathrooms":bathrooms,
            "maxBathrooms":bathrooms,
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
#search_for_price(property_type, bedrooms, bathrooms, suburb, postcode, 0, 100000, 50000)

