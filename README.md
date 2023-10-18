# Live County-Level COVID-19 Tracker [2020 - ]
A tool for users across the United States (everyone from school faculty, to state officials, to everyday users and more) to track the local effects of and measures against COVID-19, integrating real-world and self-updating data with intuitive metrics & displays.

1) Learn more about the application on my [blog post]([url](https://kabirmoghe.medium.com/live-covid-19-county-level-web-app-dbd6db3cc6bf)).
2) Take a look at some analysis I performed in early 2020 on another [blog post](https://kabirmoghe.medium.com/county-based-covid-19-dataset-and-analytical-trends-ff1617030ba8).

Check out the app [here](https://livecovidapp.herokuapp.com)!

## Purpose & Takeaways
* The story behind this app began with the need for granular information on COVID-19, prompting the development of county-level data (described more in depth in post (2)). Ultimately, I hoped to democratize the data and interpret it in a parsable way for others that needed the data. This ultimately evolved into the app you see today, before other sites like [covidactnow](https://covidactnow.org/?s=48033551) and the New York Times' COVID-19 tracker popped up. I shared the data with faculty at my school and some officials at WHO to get feedback and ultimately improved the data and metrics over time.
* Overall, this project gave me a great understanding for a certain approach to development and many technical skills (with UI/UX design, storage efficiency, AWS, and more). Beyond this, I got a real feel for applying data analysis to the real world. Since the development of this project, I've picked up many new technical skills, but this early project gave me a great sense for the power data holds in real-world contexts, which is something I've become truly passionate about!
* 
## Content & Architecture
This repository contains the core parts of the webapp, namely the python files that make up the backend, the HTML + JS files that make up the frontend, static images, as well as deployment-related files. The app uses Flask as its framework, with a python backend and HTML frontent and is deployed on Heroku. 

### In-depth Structure
The app is built on top of a self-updated dataset, compiled specifically using <b>dataset.py</b>, which is run on an hourly schedule to scrape data from various sources, aggregate the information, and place the data in an S3 bucket for the app itself to use. 

The app itself, with its routes/pages outlined in <b>app.py</b>, then accesses the data from the bucket and uses it to produce county-level metrics. This two-sided architecture developed as a result of the heavy load the data-compilation processed placed on the app. Initially, I began by having the app compile the data for each query users made, but as the data became more complicated and required pulling from a growing number of sources, the memory and time loads placed on the app became impractical for users. Having the data stored allowed for much faster response times, and given that data was being updated relatively infrequently, having a cron schedule to produce the data proved much more effective.

## Sources
The data is compiled from an array of sources each time the data self-updates, each providing certain attributes:
* [USAFacts](https://usafacts.org/visualizations/coronavirus-covid-19-spread-map/): cumulative COVID-19 case & death tallies: 
* [CDC](https://usafacts.org/visualizations/coronavirus-covid-19-spread-map/): vaccinations
* [AARP](https://www.aarp.org/health/healthy-living/info-2020/states-mask-mandates-coronavirus.html): mask/social distancing policies: 
* [US Census Bureau](https://www2.census.gov/programs-surveys/popest/datasets/2010-2020/counties/totals/): race demographics: 
* [USDA](https://www.ers.usda.gov/data-products/county-level-data-sets/download-data/): unemployment, income, and education:
* [USAFacts](https://usafacts.org/visualizations/coronavirus-covid-19-spread-map/) and [ArcGIS](https://hub.arcgis.com/datasets/esri::usa-counties/about): calculated population density: 


