import pandas as pd
import requests
from bs4 import BeautifulSoup
import io
from io import StringIO
import os
import boto3
from urllib.request import Request, urlopen
import readbucketdata

# Automated script for producing county-level COVID-19 data; scrapes data from a series of sources, outlined in detail in the README and on the app's about page
# Ultimately puts together 2 datasets, 1 on aggregate info from every source and a more comprehensive vaccination progress dataset
# Data used from the census website and has been cut down to only a few important attributes; download the full file here: https://www2.census.gov/programs-surveys/popest/datasets/2010-2019/counties/cc-est2019-alldata.csv

# Function to get .csv from private GH repo
def get_private_data(token, owner, repo, path):
    r = requests.get(
        'https://api.github.com/repos/{owner}/{repo}/contents/{path}'.format(
    owner=owner, repo=repo, path=path),
    headers={
        'accept': 'application/vnd.github.v3.raw',
        'authorization': 'token {}'.format(token)
            }
    )

    string_io_obj = StringIO(r.text)
    df = pd.read_csv(string_io_obj, sep=",", index_col=0)
    
    return df

# Produces info on race demographics
def create_race_data():
    
    # Gets demographic data
    stat_data = get_private_data('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','kabirmoghe','Demographic-Data','stat_data.csv')
    
    # Population data source
    pop_url = 'https://usafactsstatic.blob.core.windows.net/public/data/covid-19/covid_county_population_usafacts.csv'

    # Cleans up population data
    pop = pd.read_csv(pop_url)
    pop['countyFIPS'] = pop['countyFIPS'].apply(lambda value: '0' + str(value) if len(str(value)) == 4 else str(value))
    pop = pop[pop['County Name'] != 'Statewide Unallocated'].reset_index(drop = True)[['County Name', 'State','population']].rename(columns = {'population':'Population'})
    pop['County Name'] = pop['County Name']  + ', ' + pop['State']
    
    # Merges data into single df
    race_data = pd.merge(pop, stat_data)
    
    race_cols = ['African American', 'Hispanic', 'Asian American', 'White American', 'Native American or Alaska Native', 'Native Hawaiian or Pacific Islander']

    # Creates columns for e/ demographic
    for col in race_cols:
        race_data['% ' + str(col)] = round(race_data[col + ' Population'] / race_data['Population'] * 100,2)
        race_data = race_data.drop(col + ' Population', axis = 1)    
    
    race_data = race_data.drop(['Population','State'], axis = 1)
    
    race_data['Approximate Population Density'] = round(race_data['Approximate Population Density'], 2)
    
    return race_data

# Produces income + unemployment data
def create_inc_unemp_data():
    
    income_data = pd.read_excel('https://www.ers.usda.gov/webdocs/DataFiles/48747/Unemployment.xls?v=2512', skiprows = 4)[['area_name','Unemployment_rate_2019', 'Median_Household_Income_2019']].reset_index(drop = True).rename(columns = {'area_name': 'County Name', 'Unemployment_rate_2019': '% Unemployed', 'Median_Household_Income_2019':'Median Household Income'})
    income_data['% Unemployed'] = income_data['% Unemployed'].round(2)
    
    return income_data

# Produces education data
def create_edu_data():
    sts = ["Alabama","Alaska","Arizona","Arkansas","California","Colorado",
           "Connecticut","Delaware","Florida","Georgia","Hawaii","Idaho","Illinois",
           "Indiana","Iowa","Kansas","Kentucky","Louisiana","Maine","Maryland",
           "Massachusetts","Michigan","Minnesota","Mississippi","Missouri","Montana",
           "Nebraska","Nevada","New Hampshire","New Jersey","New Mexico","New York",
           "North Carolina","North Dakota","Ohio","Oklahoma","Oregon","Pennsylvania",
           "Rhode Island","South Carolina","South Dakota","Tennessee","Texas","Utah",
           "Vermont","Virginia","Washington","West Virginia","Wisconsin","Wyoming","Puerto Rico"]
    
    edu_link = 'https://www.ers.usda.gov/webdocs/DataFiles/48747/Education.xls?v=6188.1'

    # Forms metrics for education (degree-related)
    edu_data = pd.read_excel(edu_link).drop([0,1,2,4])
    edu_data.columns = edu_data.loc[3].values
    edu_data = edu_data.drop(3).reset_index(drop = True)

    for value in edu_data['Area name']:
        if value in sts:
            edu_data.drop(edu_data[edu_data['Area name'] == value].index[0], inplace = True)
        
    edu_data['Area name'] = edu_data['Area name'] + ', ' + edu_data['State']
    edu_data = edu_data.rename(columns = {'Area name': 'County Name'})
    edu_data = edu_data[['County Name', "Percent of adults completing some college or associate's degree, 2015-19"]]
    edu_data['Percent of adults completing some college or associate\'s degree, 2015-19'] = edu_data['Percent of adults completing some college or associate\'s degree, 2015-19'].apply(lambda value: round(value, 1))
    
    # Gets population data agin for %-based calculations
    pop_url = 'https://usafactsstatic.blob.core.windows.net/public/data/covid-19/covid_county_population_usafacts.csv'

    pop = pd.read_csv(pop_url)
    pop['countyFIPS'] = pop['countyFIPS'].apply(lambda value: '0' + str(value) if len(str(value)) == 4 else str(value))
    pop = pop[pop['County Name'] != 'Statewide Unallocated'].reset_index(drop = True)[['County Name', 'State','population']].rename(columns = {'population':'Population'})
    pop['County Name'] = pop['County Name']  + ', ' + pop['State']
    
    edu_data = pd.merge(pop, edu_data, on = 'County Name')
    edu_data.drop(['State', 'Population'], axis = 1, inplace = True)
    edu_data.rename(columns = {'Percent of adults completing some college or associate\'s degree, 2015-19': '% Adults With Degree 2015-19'}, inplace = True)

    return edu_data

# Produces statewide data about mask reqs + distancing mandates
def create_mask_data():
    states = {
        'District of Columbia': 'DC',
        'Puerto Rico': 'PR',
        'Alabama': 'AL',
        'Montana': 'MT',
        'Alaska': 'AK',
        'Nebraska': 'NE',
        'Arizona': 'AZ',
        'Nevada': 'NV',
        'Arkansas': 'AR',
        'New Hampshire': 'NH',
        'California': 'CA',
        'New Jersey': 'NJ',
        'Colorado': 'CO',
        'New Mexico': 'NM',
        'Connecticut': 'CT',
        'New York': 'NY',
        'Delaware': 'DE',
        'North Carolina': 'NC',
        'Florida': 'FL',
        'North Dakota': 'ND',
        'Georgia': 'GA',
        'Ohio': 'OH',
        'Hawaii': 'HI',
        'Oklahoma': 'OK',
        'Idaho': 'ID',
        'Oregon': 'OR',
        'Illinois': 'IL',
        'Pennsylvania': 'PA',
        'Indiana': 'IN',
        'Rhode Island': 'RI',
        'Iowa': 'IA',
        'South Carolina': 'SC',
        'Kansas': 'KS',
        'South Dakota': 'SD',
        'Kentucky': 'KY',
        'Tennessee': 'TN',
        'Louisiana': 'LA',
        'Texas': 'TX',
        'Maine': 'ME',
        'Utah': 'UT',
        'Maryland': 'MD',
        'Vermont': 'VT',
        'Massachusetts': 'MA',
        'Virginia': 'VA',
        'Michigan': 'MI',
        'Washington': 'WA',
        'Minnesota': 'MN',
        'West Virginia': 'WV',
        'Mississippi': 'MS',
        'Wisconsin': 'WI',
        'Missouri': 'MO',
        'Wyoming': 'WY',
    }
    
    mainContent = requests.get("https://www.aarp.org/health/healthy-living/info-2020/states-mask-mandates-coronavirus.html")
    
    mask_html = BeautifulSoup(mainContent.text,'lxml')
    
    ps = []

    for paragraph in mask_html.find_all('p'):
        ps.append(paragraph.text.strip())
        
    sps = []
    
    for span in mask_html.find_all('span'):
        txt = span.text.strip()
        if txt != '' and txt != '|':
            sps.append(txt)

    date_updated = ""
    
    for i in range(len(sps)):
        if "Published" in sps[i]:
            date_updated = sps[i+1]
            break

    state_list = []

    for heading in mask_html.find_all('h4'):
        if len(state_list) == 52:
            break
        else:
            heading = heading.text.strip()
            if len(heading.split()) <= 4:   
                state_list.append(heading)
    
    st = pd.DataFrame(state_list, columns=['State'])
    st['State'] = st['State'].map(states)
    
    loc = 0
    for i in range(len(ps)):
        if "Alabama" in ps[i]:
            loc = i
            break
    
    # Gets links for more info
    
    full_ps = []

    for p in mask_html.find_all("p"):
        full_ps.append(p)
    
    moreInfo = [p for p in full_ps if "learn more:" in p.text.strip().lower()]
    
    links = []

    for val in moreInfo:
        state_links = ""
        for link in val.find_all('a', href = True):
            if len(state_links) > 0:
                state_links += ", " + link.text.strip().title() + " - " + link["href"] 
            else:
                state_links = link.text.strip().title() + " - " + link["href"]
        links.append(state_links)
            
    links = pd.DataFrame(links, columns = ["Learn More"])
        
    # Begins putting together information about each state's guidelines     
    mask_info = pd.DataFrame([h4.find_next_sibling('p').text for h4 in mask_html.find_all('h4')], columns = ['Mask Mandate Details as of {}'.format(date_updated)])            
    mask_data = pd.concat([st, mask_info, links], axis = 1)
    
    return mask_data # Current aggregate guidelines + links for more info
    
# Data from usafacts.org (https://usafacts.org/visualizations/coronavirus-covid-19-spread-map/)
# URLs for cases, deaths, and population data from the above website
def create_covid_pop_data():

    no_mo = {1:'January',
                2:'February',
                 3:'March',
                 4:'April',
                 5:'May',
                 6:'June',
                 7:'July',
                 8:'August',
                 9:'September',
                 10:'October',
                 11:'November',
                 12:'December'
                }
    
    cases_url = 'https://static.usafacts.org/public/data/covid-19/covid_confirmed_usafacts.csv'
    deaths_url = 'https://static.usafacts.org/public/data/covid-19/covid_deaths_usafacts.csv'
    pop_url = 'https://static.usafacts.org/public/data/covid-19/covid_county_population_usafacts.csv'
    
    # Removes space in county names
    def county_cleaner(cty):
        if cty.split(',')[0][-1] == ' ':
            cty = '{County},{Abbr}'.format(County = cty.split(' ,')[0], Abbr = cty.split(' ,')[1])
        return cty
    
    # Creates the cumulative cases dataframe
    cases_req = Request(cases_url)
    cases_req.add_header('User-Agent', 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:77.0) Gecko/20100101 Firefox/77.0')
    cases_content = urlopen(cases_req)

    cases = pd.read_csv(cases_content)
    cases['countyFIPS'] = cases['countyFIPS'].apply(lambda value: '0' + str(value) if len(str(value)) == 4 else str(value))
    cases = cases[cases['County Name'] != 'Statewide Unallocated'].reset_index(drop = True)
    cases['County Name'] = cases['County Name']  + ', ' + cases['State']
    cases['County Name'] = cases['County Name'].apply(county_cleaner)
    
    
    # Gets county names
    ctynames = cases['County Name']
    
    # Creates the cumulative deaths dataframe
    deaths_req = Request(deaths_url)
    deaths_req.add_header('User-Agent', 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:77.0) Gecko/20100101 Firefox/77.0')
    deaths_content = urlopen(deaths_req)

    deaths = pd.read_csv(deaths_content)
    deaths['countyFIPS'] = deaths['countyFIPS'].apply(lambda value: '0' + str(value) if len(str(value)) == 4 else str(value))
    deaths = deaths[deaths['County Name'] != 'Statewide Unallocated'].reset_index(drop = True)
    deaths['County Name'] = deaths['County Name']  + ', ' + deaths['State']
    deaths['County Name'] = deaths['County Name'].apply(county_cleaner)

    def str_int(val):
        if type(val) == str:
            return int(val)
        else:
            return val

    # Creates the population dataframe
    pop_req = Request(pop_url)
    pop_req.add_header('User-Agent', 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:77.0) Gecko/20100101 Firefox/77.0')
    pop_content = urlopen(pop_req)

    pop = pd.read_csv(pop_content)
    pop['countyFIPS'] = pop['countyFIPS'].apply(lambda value: '0' + str(value) if len(str(value)) == 4 else str(value))
    pop = pop[pop['County Name'] != 'Statewide Unallocated'].reset_index(drop = True)
    pop['County Name'] = pop['County Name']  + ', ' + pop['State']
    pop = pd.DataFrame(pop).rename(columns = {'population':'Population'})
    pop['County Name'] = pop['County Name'].apply(county_cleaner)

    # Helper function for compiling weekly
    def week_compiler(df, c_or_d):
        week = pd.concat([df[df.columns[:3]], df[df.columns[-8:]]], axis = 1)

        rawdate = df.columns[-1] 
        year, month, day = [int(value) for value in rawdate.split('-')]
        
        date = '{month} {day}, {year}'.format(month = no_mo[month], day = day, year = year)
        
        cols = df[df.columns[-36:]].columns
        
        g_dates = []

        for i in range(1,len(cols)):
            if i == 1:
                g_dates.append(i)
            else:
                if (i-1)%7 == 0:
                    g_dates.append(i)
                            
        for g_date in g_dates:
            f_date, p_date = g_date+6, g_date-1
            week['{}, Week of {}'.format(c_or_d, cols[g_date])] = df[cols[f_date]] - df[cols[p_date]]
            week['{}, Week of {}'.format(c_or_d, cols[g_date])] = week['{}, Week of {}'.format(c_or_d, cols[g_date])].apply(lambda value: 0 if value < 0 else value)
        
        week['Weekly New {c_or_d} as of {date}'.format(c_or_d = c_or_d, date = date)] = week[week.columns[-6]] - week[week.columns[-13]]
        week.drop(week.columns[3:11], axis = 1, inplace = True)
        week.drop(['countyFIPS', 'State'], axis = 1, inplace = True)
        week = pd.merge(pop, week, on = 'County Name')
        
        case_cols = [col for col in week.columns if c_or_d in col and 'Weekly' not in col]
        
        for col in case_cols:
            raw_date = col.split()[-1]
            year, month, day = raw_date.split('-')
            c_date = '{} {}, {}'.format(no_mo[int(month)], int(day), year)
            
            week['{} Moving Avg. {}'.format(c_or_d, c_date)] = round((((week[col]/7)/week['Population'])*100000),2)
            
            week.drop(col, axis = 1, inplace = True)
        
        week['7-Day Daily {c_or_d} per 100,000 as of {date}'.format(c_or_d = c_or_d, date = date)] = round(((week['Weekly New {c_or_d} as of {date}'.format(c_or_d = c_or_d, date = date)]/7)/ week['Population'])*100000, 2)
        week.drop(week[week['7-Day Daily {c_or_d} per 100,000 as of {date}'.format(c_or_d = c_or_d, date = date)] < 0].index, inplace = True)
        week = week.reset_index(drop = True)
        
        return week
    
    # Gets weekly compiled cases and deaths as moving averages (more normalized and comparable form)
    cs = week_compiler(cases, 'Cases')
    ds = week_compiler(deaths, 'Deaths')
    
    covid_data = cs[cs.columns[:4]]
       
    cs.drop(ds.columns[[0,2,3]], axis = 1, inplace = True)
    ds.drop(ds.columns[[0,2,3]], axis = 1, inplace = True)
        
    for i in range(1,8):
        covid_data = pd.merge(covid_data, cs[cs.columns[[0,i]]], on = 'County Name')
        covid_data = pd.merge(covid_data, ds[ds.columns[[0,i]]], on = 'County Name')
        
    covid_data = covid_data.rename(columns = {'countyFIPS': 'County FIPS'})

    covid_data = covid_data[covid_data['County Name'] != 'Chattahoochee County, GA']

    return covid_data

# Produces data on vaccinations and progress
def create_vaxx_data():
    def data():
        data = pd.read_csv('https://data.cdc.gov/api/views/8xkx-amqh/rows.csv?accessType=DOWNLOAD')

        no_mo = {1:'January',
                 2:'February',
                 3:'March',
                 4:'April',
                 5:'May',
                 6:'June',
                 7:'July',
                 8:'August',
                 9:'September',
                 10:'October',
                 11:'November',
                 12:'December'
             }

        latest_date = data['Date'][0]

        def word_name(date):
            month, day, year = [int(value) for value in date.split('/')]
            date = '{month} {day}, {year}'.format(month = no_mo[month], day = day, year = year)

            return date

        date = word_name(latest_date)
        data['Recip_County'] = data['Recip_County'] + ', ' + data['Recip_State']
        dates = list(data['Date'])

        def get_months():
            m_dates = []
            l_month = 0

            for date in dates:
                month = int(date.split('/')[0])
                if month != l_month:
                    m_dates.append(date)
                l_month = month

            return m_dates

        data = data[data['Date'].isin(get_months())]

        data = data[['Date', 'Recip_County', 'Series_Complete_Pop_Pct',
           'Series_Complete_12PlusPop_Pct', 'Series_Complete_18PlusPop_Pct',
           'Series_Complete_65PlusPop_Pct', 'Administered_Dose1_Pop_Pct',
           'Booster_Doses_Vax_Pct', 'Booster_Doses_18Plus_Vax_Pct', 
           'Booster_Doses_50Plus_Vax_Pct', 'Booster_Doses_65Plus_Vax_Pct']]

        data.columns = ['Date', 'County Name', '% Fully Vaccinated as of {}'.format(date),'% ≥ 12 Fully Vaccinated as of {}'.format(date), '% ≥ 18 Fully Vaccinated as of {}'.format(date), '% ≥ 65 Fully Vaccinated as of {}'.format(date), '% At Least Partially Vaccinated as of {}'.format(date), 
                        '% with Vaxx. and Booster as of {}'.format(date), '% ≥ 18 with Vaxx. and Booster as of {}'.format(date), '% ≥ 50 with Vaxx. and Booster as of {}'.format(date), '% ≥ 65 with Vaxx. and Booster as of {}'.format(date)]

        dates = list(data['Date'])

        data = data.iloc[::-1]

        data.reset_index(drop = True, inplace = True)

        data['Date'] = data['Date'].apply(lambda date: word_name(date))
        
        # Dec 15 first day for boosters
        
        return data
        
    data = data()
    data = data[data['County Name'] != 'Chattahoochee County, GA'] # Weird data for this specific county
    
    # Places data in bucket
    filename = 'vaxxdataset.csv'
    bucketname = 'coviddatakm'
    
    csv_buffer = StringIO()
    data.to_csv(csv_buffer)
    
    client = boto3.client('s3')
    
    response = client.put_object(Body = csv_buffer.getvalue(), Bucket = bucketname, Key = filename)

# Combines the above data together
def combiner():
    # Produces all data with above methods
    race_data = create_race_data()
    inc_unemp_data = create_inc_unemp_data()
    edu_data = create_edu_data()
    mask_data = create_mask_data()
    covid_data = create_covid_pop_data()
    
    # Places vaxx. data into bucket
    create_vaxx_data()

    # Reads vaxx data
    vaxx_data = readbucketdata.readbucketdata('vaxx')
    date = list(vaxx_data['Date'])[-1]
    vaxx_data = vaxx_data[vaxx_data['Date'] == date].drop('Date', axis = 1).reset_index(drop = True)
    
    # Combines data into single dataframe
    county_data = pd.merge(covid_data, inc_unemp_data, on = 'County Name')
    county_data = pd.merge(county_data, race_data, on = 'County Name')
    county_data = pd.merge(county_data, edu_data, on = 'County Name')
    county_data = pd.merge(county_data, mask_data, on = 'State')
    county_data = pd.merge(county_data, vaxx_data, on = 'County Name')

    return county_data

# Produces final vaxx. and aggregate dataset and places them into bucket
def main():
    data = combiner()
    
    filename = 'fulldataset.csv'
    bucketname = 'coviddatakm'
    
    csv_buffer = StringIO()
    data.to_csv(csv_buffer)
    
    client = boto3.client('s3')
    
    response = client.put_object(Body = csv_buffer.getvalue(), Bucket = bucketname, Key = filename)

if __name__ == '__main__':
    main()