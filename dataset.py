import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup
from urllib.request import urlopen

# Creates COVID-19 County Level Dataset

# Basic Stats Relating to the Virus *download "stat_data.csv", attached, and insert the path of the file*

# "stat_data.csv" comes from the census website and has been cut down to only a few important attributes; download the full file here: https://www2.census.gov/programs-surveys/popest/datasets/2010-2019/counties/cc-est2019-alldata.csv

def create_race_data():
    
    stat_data = pd.read_csv('https://raw.githubusercontent.com/kabirmoghe/Demographic-Data/main/stat_data.csv', index_col = 0)
    
    pop_url = 'https://usafactsstatic.blob.core.windows.net/public/data/covid-19/covid_county_population_usafacts.csv'

    pop = pd.read_csv(pop_url)
    pop['countyFIPS'] = pop['countyFIPS'].apply(lambda value: '0' + str(value) if len(str(value)) == 4 else str(value))
    pop = pop[pop['County Name'] != 'Statewide Unallocated'].reset_index(drop = True)[['County Name', 'State','population']].rename(columns = {'population':'Population'})
    pop['County Name'] = pop['County Name']  + ', ' + pop['State']
    
    race_data = pd.merge(pop, stat_data)
    
    race_cols = ['African American', 'Hispanic', 'Asian American', 'White American', 'Native American or Alaska Native', 'Native Hawaiian or Pacific Islander']

    for col in race_cols:
        race_data['% ' + str(col)] = round(race_data[col + ' Population'] / race_data['Population'] * 100,2)
        race_data = race_data.drop(col + ' Population', axis = 1)    
    
    race_data = race_data.drop(['Population','State'], axis = 1)
    
    race_data['Approximate Population Density'] = round(race_data['Approximate Population Density'], 2)
    
    return race_data

# Income / Unemployment Data

def create_inc_unemp_data():
    
    income_data = pd.read_excel('https://www.ers.usda.gov/webdocs/DataFiles/48747/Unemployment.xls?v=2512', skiprows = 4)[['area_name','Unemployment_rate_2019', 'Median_Household_Income_2019']].reset_index(drop = True).rename(columns = {'area_name': 'County Name', 'Unemployment_rate_2019': '% Unemployed', 'Median_Household_Income_2019':'Median Household Income'})
    
    income_data['% Unemployed'] = income_data['% Unemployed'].round(2)
    
    ### Broken down below
    
    # income_data = pd.read_excel('https://www.ers.usda.gov/webdocs/DataFiles/48747/Unemployment.xls?v=2512', skiprows = 7)
    
    #income_data = income_data[['area_name','Unemployment_rate_2019', 'Median_Household_Income_2018']] # Includes the unemployment rate in 2019 and the median household income as of 2018 (per county)

    #income_data = income_data.reset_index(drop = True)

    #income_data = income_data.rename(columns = {'area_name': 'County Name', 'Unemployment_rate_2019': '% Unemployed', 'Median_Household_Income_2018':'Median Household Income'})
    
    return income_data

# Education Data

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
    
    #pop data
    
    pop_url = 'https://usafactsstatic.blob.core.windows.net/public/data/covid-19/covid_county_population_usafacts.csv'

    pop = pd.read_csv(pop_url)
    pop['countyFIPS'] = pop['countyFIPS'].apply(lambda value: '0' + str(value) if len(str(value)) == 4 else str(value))
    pop = pop[pop['County Name'] != 'Statewide Unallocated'].reset_index(drop = True)[['County Name', 'State','population']].rename(columns = {'population':'Population'})
    pop['County Name'] = pop['County Name']  + ', ' + pop['State']
    
    edu_data = pd.merge(pop, edu_data, on = 'County Name')
    
    edu_data.drop(['State', 'Population'], axis = 1, inplace = True)
    
    edu_data.rename(columns = {'Percent of adults completing some college or associate\'s degree, 2015-19': '% Adults With Degree 2015-19'}, inplace = True)

    return edu_data

# Creates a dataframe of statewide data about mask reqs

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
    
    mandates = [val for val in ps if val.split(':')[0] == 'Statewide order' or val.split(':')[0] == 'Citywide order'or val.split(':')[0] == 'Territory-wide order']
    
    sps = []

    for span in mask_html.find_all('span'):
    
        txt = span.text.strip()
    
        if txt != '' and txt != '|':
            sps.append(txt)

    date_txt = sps[15].split()
        
    date_updated = date_txt[5] + ' ' + date_txt[6] + ' ' + date_txt[7]
    
    def clean_mandates(ls):
    
        clean_mandates = []
    
        for string in mandates:
        
            s_str = string.split()
        
            if len(s_str) == 3:
                new_str = '{}'.format(s_str[2])
                clean_mandates.append(new_str)
        
            else:
                new_str = '{} ({} {})'.format(s_str[2][:3], s_str[4].title(), s_str[5].title())
                clean_mandates.append(new_str)
            
        return clean_mandates

    cm = clean_mandates(mandates)
    
    state_list = []

    for heading in mask_html.find_all('h4'):
        if len(state_list) == 52:
            break
        else:
            state_list.append(heading.text.strip())
    
    st = pd.DataFrame(state_list, columns=['State'])
    st['State'] = st['State'].map(states)

    md = pd.DataFrame(cm, columns = ['Statewide Mask Mandate (Updated {})'.format(date_updated)])
    
    loc = 0

    for i in range(len(ps)):
        if 'Here’s where each state stands on the use of face masks' in ps[i].split(','):
            loc = i+2
        
    newps = ps[loc:]

    mask_info = pd.DataFrame([val for val in newps if len(val) >150 and 'you' not in val.lower()], columns = ['Mask Mandate Details'])
            
    mask_data = pd.concat([st,md, mask_info], axis = 1)
    
    return mask_data

# Data from usafacts.org (https://usafacts.org/visualizations/coronavirus-covid-19-spread-map/)
# URLs for cases, deaths, and population data from the above website

'''

def create_covid_pop_data():

    cases_url = 'https://usafactsstatic.blob.core.windows.net/public/data/covid-19/covid_confirmed_usafacts.csv'
    deaths_url = 'https://usafactsstatic.blob.core.windows.net/public/data/covid-19/covid_deaths_usafacts.csv'
    pop_url = 'https://usafactsstatic.blob.core.windows.net/public/data/covid-19/covid_county_population_usafacts.csv'
    
    # Removes space in county names
    
    def county_cleaner(cty):
        if cty.split(',')[0][-1] == ' ':
            cty = '{County},{Abbr}'.format(County = cty.split(' ,')[0], Abbr = cty.split(' ,')[1])
        return cty
    
    # Creates the cumulative cases dataframe
    cases = pd.read_csv(cases_url)
    cases['countyFIPS'] = cases['countyFIPS'].apply(lambda value: '0' + str(value) if len(str(value)) == 4 else str(value))
    cases = cases[cases['County Name'] != 'Statewide Unallocated'].reset_index(drop = True)
    cases['County Name'] = cases['County Name']  + ', ' + cases['State']
    cases['County Name'] = cases['County Name'].apply(county_cleaner)
    cases.drop(cases.columns[-3:], axis = 1, inplace = True)
    
    cases2020 = cases.iloc[:,:349]
    cases2021 = cases.iloc[:,349:]
    
    # Gets county names
    
    ctynames = cases['County Name']
    
    # Creates the cumulative deaths dataframe
    deaths = pd.read_csv(deaths_url)
    deaths['countyFIPS'] = deaths['countyFIPS'].apply(lambda value: '0' + str(value) if len(str(value)) == 4 else str(value))
    deaths = deaths[deaths['County Name'] != 'Statewide Unallocated'].reset_index(drop = True)
    deaths['County Name'] = deaths['County Name']  + ', ' + deaths['State']
    deaths['County Name'] = deaths['County Name'].apply(county_cleaner)
    deaths.drop(deaths.columns[-3:], axis = 1, inplace = True)

    deaths2020 = deaths.iloc[:,:349]
    deaths2021 = deaths.iloc[:,349:]
    # Converts '\n' value for McDowell County, NC to the same as November and converts random string values to integers in Deaths dataset

    def str_int(val):
        if type(val) == str:
            return int(val)
        else:
            return val

    #deaths.iloc[:, -1] = deaths.iloc[:, -1].apply(str_int)

    # Creates the population dataframe
    
    pop = pd.read_csv(pop_url)
    pop['countyFIPS'] = pop['countyFIPS'].apply(lambda value: '0' + str(value) if len(str(value)) == 4 else str(value))
    pop = pop[pop['County Name'] != 'Statewide Unallocated'].reset_index(drop = True)
    pop['County Name'] = pop['County Name']  + ', ' + pop['State']
    pop = pd.DataFrame(pop).rename(columns = {'population':'Population'})
    pop['County Name'] = pop['County Name'].apply(county_cleaner)

    # Creates 'dates' as a list of all of the days past in 2020

    c_dates2020 = cases2020.iloc[:,4:].columns.values
    
    c_dates2021 = cases2021.columns.values

    d_dates2020 = deaths2020.iloc[:,4:].columns.values

    d_dates2021 = deaths2021.columns.values
    
    # Defines the function to compile the daily data into monthly data
    
    
    def m_compiler(df, c_or_d):
        
        year = df.columns[-1].split('-')[0]
        
        c_df = df.copy(deep = True)
        
        c_mos_2020 = {1:'January Cases (2020)', 2:'February Cases (2020)', 3:'March Cases (2020)', 4:'April Cases (2020)', 5:'May Cases (2020)', 6:'June Cases (2020)', 7:'July Cases (2020)', 8:'August Cases (2020)', 9:'September Cases (2020)', 10:'October Cases (2020)', 11:'November Cases (2020)', 12:'December Cases (2020)'}
        c_mos_2021 = {1:'January Cases (2021)', 2:'February Cases (2021)', 3:'March Cases (2021)', 4:'April Cases (2021)', 5:'May Cases (2021)', 6:'June Cases (2021)', 7:'July Cases (2021)', 8:'August Cases (2021)', 9:'September Cases (2021)', 10:'October Cases (2021)', 11:'November Cases (2021)', 12:'December Cases (2021)'}
        
        d_mos_2020 = {1:'January Deaths (2020)', 2:'February Deaths (2020)', 3:'March Deaths (2020)', 4:'April Deaths (2020)', 5:'May Deaths (2020)', 6:'June Deaths (2020)', 7:'July Deaths (2020)', 8:'August Deaths (2020)', 9:'September Deaths (2020)', 10:'October Deaths (2020)', 11:'November Deaths (2020)', 12:'December Deaths (2020)'}
        d_mos_2021 = {1:'January Deaths (2021)', 2:'February Deaths (2021)', 3:'March Deaths (2021)', 4:'April Deaths (2021)', 5:'May Deaths (2021)', 6:'June Deaths (2021)', 7:'July Deaths (2021)', 8:'August Deaths (2021)', 9:'September Deaths (2021)', 10:'October Deaths (2021)', 11:'November Deaths (2021)', 12:'December Deaths (2021)'}
        
        c_mo_ls2020 = list(range(int(c_dates2020[-1].split('-')[1])))
        c_mo_ls2021 = list(range(int(c_dates2021[-1].split('-')[1])))
        
        d_mo_ls2020 = list(range(int(d_dates2020[-1].split('-')[1])))
        d_mo_ls2021 = list(range(int(d_dates2021[-1].split('-')[1])))
        
        if c_or_d == 'c':
            if year == '2020':
                for i in range(int(c_dates2020[-1].split('-')[1])):
                    for date in c_dates2020:
                        while int(date.split('-')[1]) < i + 2:
                            c_mo_ls2020.pop(i)
                            c_mo_ls2020.insert(i,date)
                            break
        
                monthly_df = c_df[c_mo_ls2020]
        
                c_df.drop(c_df.iloc[:,4:], axis = 1, inplace = True)
                
            else:
                for i in range(int(c_dates2021[-1].split('-')[1])):
                    for date in c_dates2021:
                        while int(date.split('-')[1]) < i + 2:
                            c_mo_ls2021.pop(i)
                            c_mo_ls2021.insert(i,date)
                            break
        
                monthly_df = c_df[c_mo_ls2021]
                
        elif c_or_d == 'd':
            if year == '2020':
                for i in range(int(d_dates2020[-1].split('-')[1])):
                    for date in d_dates2020:
                        while int(date.split('-')[1]) < i + 2:
                            d_mo_ls2020.pop(i)
                            d_mo_ls2020.insert(i,date)
                            break
        
                monthly_df = c_df[d_mo_ls2020]
        
                c_df.drop(c_df.iloc[:,4:], axis = 1, inplace = True)
            
            else:
                for i in range(int(d_dates2021[-1].split('-')[1])):
                    for date in d_dates2021:
                        while int(date.split('-')[1]) < i + 2:
                            d_mo_ls2021.pop(i)
                            d_mo_ls2021.insert(i,date)
                            break
        
                monthly_df = c_df[d_mo_ls2021]
        
        def num_to_mo(cols):
            sing_nums = cols.map(lambda col: int(col.split('-')[1]))
            return sing_nums
            
        monthly_df.columns = num_to_mo(monthly_df.columns)
            
        if c_or_d == 'c':
            if year == '2020':
                monthly_df.columns = monthly_df.columns.map(c_mos_2020)
            else:
                monthly_df.columns = monthly_df.columns.map(c_mos_2021)
        
        elif c_or_d == 'd':
            if year == '2020':
                monthly_df.columns = monthly_df.columns.map(d_mos_2020)
            else:
                monthly_df.columns = monthly_df.columns.map(d_mos_2021) 
        
        monthly_df = pd.concat([ctynames, monthly_df], axis = 1)
        
        prob_ctys = []

        for i in range(1, len(monthly_df.columns)-1):
            locs = list(monthly_df[monthly_df[monthly_df.columns[i]] > monthly_df[monthly_df.columns[i+1]]].index)
            if locs not in prob_ctys:
                monthly_df.drop(locs, inplace = True)
            prob_ctys.append(locs)
    
        monthly_df.reset_index(drop = True, inplace = True)
    
        if year == '2020':
            
            c_df = pd.merge(c_df, monthly_df, on = 'County Name')
              
            split1 = c_df.iloc[:,:4]
            split2 = c_df.iloc[:,4:]
        
            for i in range(1,len(split2.columns)):
                split2.iloc[:,-i] = split2.iloc[:,-i] - split2.iloc[:,-i-1]

            c_df = pd.concat([split1, split2], axis = 1)
        
        else:
            c_df = monthly_df
            
            if c_or_d == 'c':
                dec_jan = pd.merge(cases[['County Name','2020-12-31']], c_df, on = "County Name")
            else:
                dec_jan = pd.merge(deaths[['County Name','2020-12-31']], c_df, on = "County Name")
            
            split1 = dec_jan.iloc[:,:1]
            split2 = dec_jan.iloc[:,1:]
        
            if len(split2.columns) == 2:
                split2.iloc[:,1] = split2.iloc[:,1] - split2.iloc[:,0]
            
            else:
                for i in range(1,len(split2.columns)):
                    split2.iloc[:,-i] = split2.iloc[:, -i] - split2.iloc[:,-i-1]
            c_df = pd.concat([split1, split2], axis = 1)
            c_df.drop(c_df.columns[1], axis = 1, inplace = True)
    
        return c_df
    
    c_mo_us = pd.merge(m_compiler(cases2020, 'c'), m_compiler(cases2021, 'c'), on = 'County Name').drop(['countyFIPS', 'State', 'StateFIPS'], axis = 1)
    d_mo_us = pd.merge(m_compiler(deaths2020, 'd').drop(['countyFIPS', 'State', 'StateFIPS'], axis = 1), m_compiler(deaths2021, 'd'), on = 'County Name')
    
    covid_data = m_compiler(cases2020, 'c').iloc[:, :4]
    
    pop.drop(['countyFIPS', 'State'], axis = 1, inplace = True)
    covid_data = pd.merge(covid_data, pop, on = 'County Name')        
    
    cd = covid_data.copy(deep = True)
    
    for i in range(1, len(c_mo_us.columns)):
        cd = pd.merge(cd, pd.concat([c_mo_us['County Name'], c_mo_us.iloc[:,i:i+1]], axis = 1), on = 'County Name')
        cd = pd.merge(cd, pd.concat([d_mo_us['County Name'], d_mo_us.iloc[:,i:i+1]], axis = 1), on = 'County Name')
    
    c_cols = []
    d_cols = []

    for col in cd.columns: 
        col_cont = col.split()
        if len(col_cont) == 3:
            if col_cont[1] == 'Cases':
                c_cols.append(col)
            elif col_cont[1] == 'Deaths': 
                d_cols.append(col)
        
    c_rates = pd.DataFrame()
    d_rates = pd.DataFrame()
    
    for c_mo in c_cols:
        c_rates[c_mo.split()[0] + ' ' + c_mo.split()[2] + ' Infection Rate (per 100,000)'] = round(cd[c_mo]/cd['Population'] * 100000, 2)
    
    for d_mo in d_cols:
        d_rates[d_mo.split()[0] + ' ' + d_mo.split()[2] + ' Mortality Rate (per 100,000)'] = round(cd[d_mo]/cd['Population'] * 100000, 2)
        
    for i in range(0, len(c_rates.columns)):
        covid_data = pd.merge(covid_data, pd.concat([cd['County Name'], c_rates.iloc[:,i:i+1]], axis = 1), on = 'County Name')
        covid_data = pd.merge(covid_data, pd.concat([cd['County Name'], d_rates.iloc[:,i:i+1]], axis = 1), on = 'County Name')
    
    def projector(df, df2, c_or_d):
        mo_days = {1 : 31,
                   2 : (28,29),
                   3 : 31,
                   4 : 30,
                   5 : 31,
                   6: 30,
                   7 : 31,
                   8 : 31,
                   9 : 30,
                   10 : 31,
                   11 : 30,
                   12 : 31
                  }
    
        latest_date = df.columns[-1].split('-')
    
        latest_day = int(latest_date[2])

        latest_month = int(latest_date[1])

        latest_year = int(latest_date[0])
        
        if latest_month != 2:
            tot_days = [mo_days[val] for val in [latest_month]][0]
        else:
            if latest_year % 4 == 0:
                tot_days = 29
            else:
                tot_days = 28
    
        perc_done = latest_day/tot_days
    
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
        la_mo = [no_mo[val] for val in [latest_month]][0]
        
        if c_or_d == 'c':
            latest_col = df2['{mo} Cases (2021)'.format(mo = la_mo)]
            predicted_cases = (latest_col / perc_done).apply(lambda value: int(value))
            predicted_i_r = pd.DataFrame(round(predicted_cases/df2['Population'] * 100000, 2))
            predicted_i_r.columns = ['Predicted {mo} {yr} Infection Rate (per 100,000)'.format(mo = la_mo, yr = '(2021)')]

            return predicted_i_r
    
        else:
            latest_col = df2['{mo} Deaths (2021)'.format(mo = la_mo)]
            predicted_deaths = (latest_col / perc_done).apply(lambda value: int(value))
            predicted_m_r = pd.DataFrame(round(predicted_deaths/df2['Population'] * 100000, 2))
            predicted_m_r.columns = ['Predicted {mo} {yr} Mortality Rate (per 100,000)'.format(mo = la_mo, yr = '(2021)')]    
        
            return predicted_m_r
    
    pred_inf = projector(cases2021, cd, 'c')
    pred_dth = projector(deaths2021, cd, 'd')
    
    covid_data = pd.concat([covid_data, pred_inf, pred_dth], axis = 1)
    
    covid_data['Cumulative Infection Rate (per 100,000)'] = round(c_rates.mean(axis = 1), 2)
    covid_data['Cumulative Mortality Rate (per 100,000)'] = round(d_rates.mean(axis = 1), 2)
    
    months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']

    no_to_mo = {1:'January',
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
    
    latest_date = cases2021.columns[-1].split('-')
    
    latest_day = int(latest_date[2])

    latest_month = int(latest_date[1])

    latest_year = int(latest_date[0])
    
    latest_month_name = no_to_mo[latest_month]

    column_map = {'countyFIPS': 'County FIPS', 
                  'StateFIPS': 'State FIPS', 
                  '{} (2021) Infection Rate (per 100,000)'.format(latest_month_name): '{} (2021) Infection Rate (per 100,000 as of {}/{}/{})'.format(latest_month_name, latest_month, latest_day, latest_year),
                  '{} (2021) Mortality Rate (per 100,000)'.format(latest_month_name): '{} (2021) Mortality Rate (per 100,000, as of {}/{}/{})'.format(latest_month_name, latest_month, latest_day, latest_year)
                 }
    
    covid_data = covid_data.rename(columns = column_map)
    
    return covid_data

    '''

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
    
    cases_url = 'https://usafactsstatic.blob.core.windows.net/public/data/covid-19/covid_confirmed_usafacts.csv'
    deaths_url = 'https://usafactsstatic.blob.core.windows.net/public/data/covid-19/covid_deaths_usafacts.csv'
    pop_url = 'https://usafactsstatic.blob.core.windows.net/public/data/covid-19/covid_county_population_usafacts.csv'
    
    # Removes space in county names
    
    def county_cleaner(cty):
        if cty.split(',')[0][-1] == ' ':
            cty = '{County},{Abbr}'.format(County = cty.split(' ,')[0], Abbr = cty.split(' ,')[1])
        return cty
    
    # Creates the cumulative cases dataframe
    cases = pd.read_csv(cases_url)
    cases['countyFIPS'] = cases['countyFIPS'].apply(lambda value: '0' + str(value) if len(str(value)) == 4 else str(value))
    cases = cases[cases['County Name'] != 'Statewide Unallocated'].reset_index(drop = True)
    cases['County Name'] = cases['County Name']  + ', ' + cases['State']
    cases['County Name'] = cases['County Name'].apply(county_cleaner)
    
    
    # Gets county names
    
    ctynames = cases['County Name']
    
    # Creates the cumulative deaths dataframe
    deaths = pd.read_csv(deaths_url)
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
    
    pop = pd.read_csv(pop_url)
    pop['countyFIPS'] = pop['countyFIPS'].apply(lambda value: '0' + str(value) if len(str(value)) == 4 else str(value))
    pop = pop[pop['County Name'] != 'Statewide Unallocated'].reset_index(drop = True)
    pop['County Name'] = pop['County Name']  + ', ' + pop['State']
    pop = pd.DataFrame(pop).rename(columns = {'population':'Population'})
    pop['County Name'] = pop['County Name'].apply(county_cleaner)
    
    def week_compiler(df, c_or_d):

        week = pd.concat([df[df.columns[:3]], df[df.columns[-8:]]], axis = 1)

        rawdate = df.columns[-1] 
        year, month, day = [int(value) for value in rawdate.split('-')]
        
        date = '{month} {day}, {year}'.format(month = no_mo[month], day = day, year = year)
        
        week['Weekly {c_or_d} as of {date}'.format(c_or_d = c_or_d, date = date)] = week[week.columns[-1]] - week[week.columns[-8]]
        week.drop(week.columns[3:11], axis = 1, inplace = True)
        week.drop(['countyFIPS', 'State'], axis = 1, inplace = True)
        week = pd.merge(pop, week, on = 'County Name')
        week['7-Day Daily {c_or_d} per 100,000 as of {date}'.format(c_or_d = c_or_d, date = date)] = round(((week['Weekly {c_or_d} as of {date}'.format(c_or_d = c_or_d, date = date)]/7)/ week['Population'])*100000, 2)
        week.drop(week[week['7-Day Daily {c_or_d} per 100,000 as of {date}'.format(c_or_d = c_or_d, date = date)] < 0].index, inplace = True)
        week = week.reset_index(drop = True)

        return week
    
    cs = week_compiler(cases, 'Cases')
    ds = week_compiler(deaths, 'Deaths')
    
    covid_data = cs[cs.columns[:4]]
    
    cs.drop(ds.columns[[0,2,3]], axis = 1, inplace = True)
    ds.drop(ds.columns[[0,2,3]], axis = 1, inplace = True)
    
    for i in range(1,3):
        covid_data = pd.merge(covid_data, cs[cs.columns[[0,i]]], on = 'County Name')
        covid_data = pd.merge(covid_data, ds[ds.columns[[0,i]]], on = 'County Name')
        
    covid_data = covid_data.rename(columns = {'countyFIPS': 'County FIPS'})

    return covid_data

def main_function():
    
    race_data = create_race_data()
    inc_unemp_data = create_inc_unemp_data()
    edu_data = create_edu_data()
    mask_data = create_mask_data()
    covid_data = create_covid_pop_data()
    vaxx_data = pd.read_csv('vaxxdataset.csv', index_col = 0)
    
    county_data = pd.merge(covid_data, inc_unemp_data, on = 'County Name')
    county_data = pd.merge(county_data, race_data, on = 'County Name')
    county_data = pd.merge(county_data, edu_data, on = 'County Name')
    county_data = pd.merge(county_data, mask_data, on = 'State')
    county_data = pd.merge(county_data, vaxx_data, on = 'County Name')
    
    return county_data
