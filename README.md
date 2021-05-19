# Analysis of Australian Property Markets

## Overview
This project aim to analyse properties provided by the Domain.com.au API, which is a website that aggregrates property listing across various real-estate agencies in Australia.

- EDA.ipynb:

This notebook explores data available for properties that have been sold and training machine learning models to predict property prices in the area. 

- Domain_for-sale.ipynb/Domain_sold.ipynb:

These notebooks extracts important features (and price) of for-sale/sold properties to better guage the market in a given area.

- Domain_price_guide.ipynb:

Some for-sale properties will not have an asking price on the listing but often there is a hiiden value. 
This notebook attempts estimate it using the Mean Value Theorem. 
Beware! There is a ratelimiting cap of 500 calls on the free tier.