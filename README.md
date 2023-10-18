# Live County-Level COVID-19 Tracker [2020 - ]
A tool for users across the United States (everyone from school faculty, to state officials, to everyday users and more) to track the local effects of and measures against COVID-19, integrating real-world and self-updating data with intuitive metrics & displays.

1) Learn more about the application on my [blog post](https://kabirmoghe.medium.com/live-covid-19-county-level-web-app-dbd6db3cc6bf).
2) Take a look at some analysis I performed in early 2020 on another [blog post](https://kabirmoghe.medium.com/county-based-covid-19-dataset-and-analytical-trends-ff1617030ba8).

Check out the app [here](https://livecovidapp.herokuapp.com)!

_<b>Note</b>: many data providers like the CDC have stopped regularly collecting/publishing county-level data given that 3+ years have passed since the pandemic's onset, so information provided will be as recent as possible (based on the recency of source data) but may not be up-to-date. As a result, please also excuse issues with the app and sudden breakdowns._

## Purpose & Takeaways
* The story behind this app began with the need for granular information on COVID-19, prompting the development of county-level data on infections, mortality, mandates, county demographics, and a whole series of evolving attributes (with the initial motivation described in more detail [here](https://kabirmoghe.medium.com/county-based-covid-19-dataset-and-analytical-trends-ff1617030ba8)). Ultimately, I hoped to democratize the data and interpret it in a parsable way for others who were also in the dark. This ultimately evolved into the app you see today, before other sites like [CovidActNow](https://covidactnow.org/?s=48033551) and the New York Times' COVID-19 tracker popped up. I shared the app and its data with faculty at my school and some officials at WHO, whose feedback helped improve the data and metrics over time.
* Overall, this project gave me a great understanding for a certain approach to full-stack development and many technical skills (UI/UX, storage efficiency, AWS, and more). Beyond this, I got a hands-on feel for applying data analysis to the real world. Since the development of this project, I've picked up many new technical skills, but this early experience gave me a great sense for the power data holds in real-world contexts, which is something I've become truly passionate about!
  
## Content & Architecture
This repository contains the core parts of the webapp, namely the python files that make up the backend, the HTML + JS files that make up the frontend, static images, as well as deployment-related files. The app uses Flask as its framework, with a python backend and HTML frontent and is deployed on Heroku. 

### Files/Code + Significance:
* <b>Static</b>: images, graphics, etc.
* <b>Templates</b>: HTML files (frontend) used in conjunction with the python backend
* <b>Procfile</b>: outlines procedure for running app on Heroku
* <b>app.py</b>: implements routes for the app and defines what happens at each page, passes variables to the frontend, etc.
* <b>covidapp.py</b>: creates many functions for calculating metrics on the data
* <b>dataset.py</b>: automated script for producing county-level COVID-19 dataset & place in S3
* <b>readbucketdata.py</b>: used to retrieve stored data in S3
* <b>requirements.txt</b>: pip libraries needed for this project

### In-depth Structure
The app is built on top of a self-updated dataset, compiled specifically using <b>dataset.py</b>, which is run on an hourly schedule to scrape data from various sources (outlined below), aggregate the information, and place the data in an S3 bucket for the app (and others) to use. 

The app itself, with its routes/pages implemented in <b>app.py</b>, then accesses the data from the bucket and uses it to produce county-level metrics. This two-sided architecture developed as a result of the heavy load the data-compilation processed placed on the app. Initially, I began by having the app compile the data for each query users made, but as the data became more complicated and required pulling from a growing number of sources, the memory and time loads placed on the app became impractical. Having the data stored allowed for much faster response times, and given that data was being updated relatively infrequently, having a cron schedule to produce the data proved much more efficient.

## Sources
The data is compiled from an array of sources each time the data self-updates, each providing certain attributes:
* [USAFacts](https://usafacts.org/visualizations/coronavirus-covid-19-spread-map/): cumulative COVID-19 case & death tallies: 
* [CDC](https://usafacts.org/visualizations/coronavirus-covid-19-spread-map/): vaccinations
* [AARP](https://www.aarp.org/health/healthy-living/info-2020/states-mask-mandates-coronavirus.html): mask/social distancing policies: 
* [US Census Bureau](https://www2.census.gov/programs-surveys/popest/datasets/2010-2020/counties/totals/): race demographics: 
* [USDA](https://www.ers.usda.gov/data-products/county-level-data-sets/download-data/): unemployment, income, and education:
* [USAFacts](https://usafacts.org/visualizations/coronavirus-covid-19-spread-map/) and [ArcGIS](https://hub.arcgis.com/datasets/esri::usa-counties/about): calculated population density

## Methodology
![image](https://github.com/kabirmoghe/county-level-covid-tracker/assets/64380076/cc5f4964-0c76-40a5-bfe3-9f84b4bba562)

In order to determine the risk of infection in a certain county, the 7-Day [moving average](https://www.georgiaruralhealth.org/blog/what-is-a-moving-average-and-why-is-it-useful/) was used, which is the average number of new cases each day over the past week per 100,000 people (calculation shown above). Since county-wide population varies, 100,000 is a commonly used number to have normalized rates across all counties, so simple percentages are scaled to a number of cases out of 100,000.

To calculate risk from the moving average, the methods from the [Harvard Global Health Institute](https://ethics.harvard.edu/files/center-for-ethics/files/key_metrics_and_indicators_v4.pdf) were used. Specifically, as shown by the key above, low risk (green) is determined as less than 1 new case per day, moderately low risk (yellow) as 1 or more but less than 10 new cases per day, moderately high risk (orange) as 10 or more but less than 25 new cases per day, and high risk (red) as 25 or more new cases per day (all according to the 7-day moving average).

