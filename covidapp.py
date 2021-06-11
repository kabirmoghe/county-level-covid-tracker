import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup
from urllib.request import urlopen
import json
import plotly.express as px
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import chart_studio
import chart_studio.plotly as py
import chart_studio.tools as tls
import covidapp

def county_list():
    ctys = list(pd.read_csv('https://raw.githubusercontent.com/kabirmoghe/Demographic-Data/main/countynames.csv')['County Name'].values)
    return ctys

def county_stats(county_name):
    if county_name == '':
        return "Please enter a county name (i.e. Orange County, CA)."
    else:
        data = pd.read_csv('fulldataset.csv', index_col = 0)

        data['County FIPS'] = data['County FIPS'].apply(lambda value: '0' + str(value) if len(str(value)) == 4 else str(value))

        #infs = [column for column in data.columns if "Infection" in column.split() and "Cumulative" not in column.split() and "Predicted" not in column.split()]

        cols = data.columns

        inf_col = 0
        for col in cols:
            if "Cases" in col.split() and "per" in col.split():
                inf_col = col


        sorted_data = data.sort_values(by = inf_col, ascending = False)[['County Name', inf_col]].reset_index(drop = True)

        ctynum = len(sorted_data)

        high25pct = round(ctynum*0.25)
        low25pct = round(ctynum*0.75)

        #sets thresholds for different COVID risk levels

        green = 1 # low
        yellow = 10 # moder. low
        orange = 25 # moder. high

        #red is greater than 25, high

        if county_name in data['County Name'].values:
            '''county_df = data[data['County Name'] == county_name][infs].transpose().reset_index()
            county_df['Time'] = ["Jan '20", "Feb '20", "Mar '20", "Apr '20", "May '20", "Jun '20", "Jul '20", "Aug '20", "Sept '20", "Oct '20", "Nov '20", "Dec '20", "Jan '21", "Feb '21", "Mar '21", "Apr '21", "May '21"]
            county_df['Infection Rate per 100,000 for {county_name}'.format(county_name = county_name)] = county_df.iloc[:,1]
            
            sns.barplot(x = "Time", y = 'Infection Rate per 100,000 for {county_name}'.format(county_name = county_name), data = county_df, palette = 'plasma').get_figure()
            plt.savefig('/app/static/countyplot.png')
            '''
            des_row = data[data['County Name'] == str(county_name)]

            des_row.rename(index = {des_row.index.values[0]: county_name}, inplace = True)

            mask_info= [des_row[col].values[0] for col in des_row.columns if 'mask' in col.lower()]

            y_n_mask, mask_details = mask_info

            des_row.drop('Mask Mandate Details', axis = 1, inplace = True)

            otherinfo = pd.concat([des_row['Population'], des_row.iloc[:, -15:]], axis = 1)

            stat = des_row[inf_col].iloc[0]

            rank = sorted_data[sorted_data['County Name']==county_name].index[0]+1

            css_prop = stat/27

            if css_prop <= 1:
                css_prop = css_prop
            else:
                css_prop = 1.0

            #pct = round(prop*100,2)

            prop = (1-(rank/len(sorted_data)))

            pct = round(prop*100, 2)

            

            if stat == 0.0:
                rec = '{county_name} has a low risk of infection and is on track for containment. Regardless, precaution should be taken and social distancing guidelines should be followed.'.format(county_name = county_name)
                
                color = '#7cff02'

                info = "With a rank of {rank} out of {ctynum} included counties, {county_name} is one of the lowest counties in terms of {inf_col}.".format(rank = rank, ctynum = ctynum, county_name = county_name, pct = pct, inf_col = inf_col)
         
            elif round(pct) == 100.0:
                rec = 'There is a high risk of infection in {county_name}, so precaution should be taken and social distancing guidelines should be followed strictly:'.format(county_name = county_name)
                
                color = '#ff0600'

                info = "With a rank of {rank} out of {ctynum} included counties, {county_name} is the highest county in terms of {inf_col}.".format(rank = rank, ctynum = ctynum, county_name = county_name, pct = pct, inf_col = inf_col)
            else:
                if stat < green:
                    rec = '{county_name} has a low risk of infection and is on track for containment. Regardless, precaution should be taken and social distancing guidelines should be followed.'.format(county_name = county_name)

                    color = '#7cff02'

                elif green <= stat < yellow:
                    rec = '{county_name} has a moderately low risk of infection, and strategic choices must be made about which package of non-pharmaceutical interventions to use for control. Precaution should be taken and social distancing guidelines should be followed.'.format(county_name = county_name)
                    
                    color = '#fff800'

                elif yellow <= stat < orange:
                    rec = '{county_name} has a moderately high risk of infection, and strategic choices must be made about which package of non-pharmaceutical interventions to use for control. Stay-at-home orders are advised unless viral testing and contact tracing capacity are implementable at levels meeting surge indicator standards. Precaution should be taken and social distancing guidelines should be followed.'.format(county_name = county_name)

                    color = '#ffab00'

                else:
                    rec = '{county_name} has a high risk of infection, and stay-at-home orders may be necessary. Precaution should be taken and social distancing guidelines should be followed.'.format(county_name = county_name)

                    color = '#ff0600'

                info = "With a rank of {rank} out of {ctynum} included counties, {county_name} is higher than {pct}% of counties in terms of {inf_col}.".format(rank = rank, ctynum = ctynum, county_name = county_name, pct = pct, inf_col = inf_col)

            riskimg = 'riskchart.png'
            risk_pos = (round(182+(346*css_prop),2))
                
            return otherinfo, stat, info, rec, risk_pos, pct, y_n_mask, mask_details, color#, riskimg
        else:
            return "Please enter a valid county name (i.e. Orange County, CA). The county you entered, '{county_name}', may not have complete information.".format(county_name = county_name)

def usplot(c_or_d):
    with urlopen('https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json') as response:
        counties = json.load(response)
    
    data = pd.read_csv('fulldataset.csv', index_col = 0)

    data['County FIPS'] = data['County FIPS'].apply(lambda value: '0' + str(value) if len(str(value)) == 4 else str(value))
    if c_or_d == 'c':

        last_case_rate = [column for column in data.columns if "Cases" in column.split() and "per" in column.split()][0]

        date = last_case_rate.split('as of ')[1]

        def log_maker(value):
            if value != 0:
                if np.log(value) < 0:
                    return 0
                else:
                    return np.log(value)
            else:
                return value
                

        data['Log {name}'.format(name = last_case_rate)] = data[last_case_rate].apply(lambda value: log_maker(value))
        
        num0 = len(data[data[last_case_rate] == 0])

        fig = px.choropleth(data, geojson=counties, locations='County FIPS', color='Log {name}'.format(name = last_case_rate),
                               color_continuous_scale="Plasma",
                               hover_name = 'County Name',
                               hover_data=[last_case_rate, 'Population'],
                               scope="usa",
                               labels={'Log {name}'.format(name = last_case_rate):'Current Log. Daily Cases per 100k'}
                              )
        fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, font_family = "Raleway", hoverlabel_font_family = "Raleway")
        fig.update_traces(marker_line_width=0, marker_opacity=0.8, hoverlabel_bgcolor='#e3f1ff', hoverlabel_bordercolor = '#e3f1ff', hoverlabel_font_color='#000066')
        fig.update_geos(showsubunits=True, subunitcolor="black", subunitwidth = 1.4)
        fig.write_html("/app/templates/c_usplot.html", full_html = False)
        
        sorted_data = data.sort_values(by = last_case_rate, ascending = False)[['County Name', last_case_rate]].reset_index(drop = True)

        top10 = sorted_data.head(10)[['County Name', last_case_rate]].reset_index(drop = True)
        bot10 = sorted_data.tail(10)[['County Name', last_case_rate]].reset_index(drop = True)

    else:

        last_death_rate = [column for column in data.columns if "Deaths" in column.split() and "per" in column.split()][0]

        date = last_death_rate.split('as of ')[1]

        def log_maker(value):
            if value != 0:
                if np.log(value) < 0:
                    return 0
                else:
                    return np.log(value)
            else:
                return value

        data['Log {name}'.format(name = last_death_rate)] = data[last_death_rate].apply(lambda value: log_maker(value))

        num0 = len(data[data[last_death_rate] == 0])
        
        fig = px.choropleth(data, geojson=counties, locations='County FIPS', color='Log {name}'.format(name = last_death_rate),
                               color_continuous_scale="Plasma",
                               hover_name = 'County Name',
                               hover_data=[last_death_rate, 'Population'],
                               scope="usa",
                               labels={'Log {name}'.format(name = last_death_rate):'Current Log. Daily Deaths per 100k'}
                              )
        fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, font_family = "Raleway", hoverlabel_font_family = "Raleway")
        fig.update_traces(marker_line_width=0, marker_opacity=0.8, hoverlabel_bgcolor='#e3f1ff', hoverlabel_bordercolor = '#e3f1ff', hoverlabel_font_color='#000066')
        fig.update_geos(showsubunits=True, subunitcolor="black", subunitwidth = 1.4)
        fig.write_html("/app/templates/d_usplot.html", full_html = False)

        sorted_data = data.sort_values(by = last_death_rate, ascending = False)[['County Name', last_death_rate]].reset_index(drop = True)

        top10 = sorted_data.head(10)[['County Name', last_death_rate]].reset_index(drop = True)
        bot10 = sorted_data.tail(10)[['County Name', last_death_rate]].reset_index(drop = True)

    #top10lst = []
    
    #for i in range(10):
    #    top10lst.append('{cty}: {stat}'.format(cty = top10['County Name'].iloc[i], stat = round(float(top10[inf_col].iloc[i]),2)))

    return top10, bot10, date, num0

'''
def create_vaxx_data():
    vaxx_url = 'https://usafactsstatic.blob.core.windows.net/public/data/covid-19/COVID19_Vaccination_Demographics.csv'
    vaxx_data = pd.read_csv(vaxx_url)
    
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
    
    raw_date = vaxx_data[vaxx_data['DEMOGRAPHIC_CATEGORY'] == 'TOTAL']['DATE'].values[0]
    
    year, month, day = [int(val) for val in raw_date.split('-')]
    date = '{month} {day}, {year}'.format(month = no_mo[month], day = day, year = year)
    
    states = ["Alabama","Alaska","Arizona","Arkansas","California","Colorado",
      "Connecticut","Delaware","Florida","Georgia","Hawaii","Idaho","Illinois",
      "Indiana","Iowa","Kansas","Kentucky","Louisiana","Maine","Maryland",
      "Massachusetts","Michigan","Minnesota","Mississippi","Missouri","Montana",
      "Nebraska","Nevada","New Hampshire","New Jersey","New Mexico","New York",
      "North Carolina","North Dakota","Ohio","Oklahoma","Oregon","Pennsylvania",
      "Rhode Island","South Carolina","South Dakota","Tennessee","Texas","Utah",
      "Vermont","Virginia","Washington","West Virginia","Wisconsin","Wyoming"]
    
    abbrev = {
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
    
    #CLEANING
    
    vaxx_data.drop('GEOGRAPHY_TYPE', axis = 1, inplace = True)
    vaxx_data = vaxx_data.drop_duplicates()
    
    # FIX TEXAS DATA (APPROX. TOTAL FROM MALE AND FEMALE AVG)
    tx = vaxx_data[vaxx_data['STATE_NAME'] == 'Texas'].reset_index(drop = True)
    partial_avg = (float(tx[tx['DEMOGRAPHIC_GROUP'] == 'FEMALE']['Full_or_Partial_Vaccinated_Percent'].iloc[0]) + float(tx[tx['DEMOGRAPHIC_GROUP'] == 'MALE']['Full_or_Partial_Vaccinated_Percent'].iloc[0]))/2
    full_avg = (float(tx[tx['DEMOGRAPHIC_GROUP'] == 'FEMALE']['Fully_Vaccinated_Percent'].iloc[0]) + float(tx[tx['DEMOGRAPHIC_GROUP'] == 'MALE']['Fully_Vaccinated_Percent'].iloc[0]))/2

    add_tx = pd.DataFrame(tx.iloc[-2].values).transpose()
    add_tx.columns = vaxx_data.columns

    add_tx['DEMOGRAPHIC_CATEGORY'] = ["TOTAL"]
    add_tx['DEMOGRAPHIC_GROUP'] = ["TOTAL"]
    add_tx['ACS_Population'] = [""]
    add_tx['Administered_Dose1_recip'] = [""]
    add_tx['Administered_Dose2_recip'] = [""]
    add_tx['Full_or_Partial_Vaccinated_Percent'] = [partial_avg]
    add_tx['Fully_Vaccinated'] = [""]
    add_tx['Fully_Vaccinated_Percent'] = [full_avg]

    vaxx_data = pd.concat([vaxx_data, add_tx]).reset_index(drop = True)
    
    vaxx_breakdown = vaxx_data[vaxx_data['DEMOGRAPHIC_CATEGORY'] == 'TOTAL'][['STATE_NAME','Full_or_Partial_Vaccinated_Percent', 'Fully_Vaccinated_Percent']].reset_index(drop = True).rename(columns = {'STATE_NAME': 'State', 'Full_or_Partial_Vaccinated_Percent': '% ≥ 1 Dose', 'Fully_Vaccinated_Percent': '% Fully Vaccinated'})
    
    vaxx_breakdown['% ≥ 1 Dose'] = pd.to_numeric(vaxx_breakdown['% ≥ 1 Dose'], errors='coerce')
    vaxx_breakdown = vaxx_breakdown.replace(np.nan, 0, regex=True)

    vaxx_breakdown['% ≥ 1 Dose'] = round(vaxx_breakdown['% ≥ 1 Dose']*100, 2)

    vaxx_breakdown['% Fully Vaccinated'] = pd.to_numeric(vaxx_breakdown['% Fully Vaccinated'], errors='coerce')
    vaxx_breakdown = vaxx_breakdown.replace(np.nan, 0, regex=True)

    vaxx_breakdown['% Fully Vaccinated'] = round(vaxx_breakdown['% Fully Vaccinated']*100, 2)
    
    race_df = pd.concat([pd.DataFrame(states), pd.DataFrame(list(range(0,50))), pd.DataFrame(list(range(0,50))), pd.DataFrame(list(range(0,50))), pd.DataFrame(list(range(0,50))), pd.DataFrame(list(range(0,50))), pd.DataFrame(list(range(0,50)))], axis = 1)
    race_df.columns = ['State','WHITE','BLACK','HISPANIC OR LATINO', 'ASIAN', 'NATIVE HAWAIIAN OR OTHER PACIFIC ISLANDER', 'AMERICAN INDIAN OR ALASKA NATIVE']
    
    race_breakdown = vaxx_data[vaxx_data['DEMOGRAPHIC_CATEGORY'] == 'RACE/ETHNICITY']

    race_breakdown = race_breakdown[race_breakdown['DEMOGRAPHIC_GROUP'] != 'TWO OR MORE RACES']
    race_breakdown = race_breakdown[race_breakdown['DEMOGRAPHIC_GROUP'] != 'OTHER']
    race_breakdown = race_breakdown[race_breakdown['DEMOGRAPHIC_GROUP'] != 'NON-HISPANIC']

    race_breakdown = race_breakdown[['STATE_NAME', 'DEMOGRAPHIC_GROUP', 'Full_or_Partial_Vaccinated_Percent', 'Fully_Vaccinated_Percent']]

    race_breakdown['Full_or_Partial_Vaccinated_Percent'] = pd.to_numeric(race_breakdown['Full_or_Partial_Vaccinated_Percent'], errors='coerce')
    race_breakdown = race_breakdown.replace(np.nan, 0, regex=True)

    race_breakdown['Full_or_Partial_Vaccinated_Percent'] = race_breakdown['Full_or_Partial_Vaccinated_Percent']*100

    race_breakdown['Fully_Vaccinated_Percent'] = pd.to_numeric(race_breakdown['Fully_Vaccinated_Percent'], errors='coerce')
    race_breakdown = race_breakdown.replace(np.nan, 0, regex=True)

    race_breakdown['Fully_Vaccinated_Percent'] = race_breakdown['Fully_Vaccinated_Percent']*100
    
    groups = ['WHITE','BLACK','HISPANIC OR LATINO', 'ASIAN', 'NATIVE HAWAIIAN OR OTHER PACIFIC ISLANDER', 'AMERICAN INDIAN OR ALASKA NATIVE']
    
    # Partial/Full Vaccination % By Race in Each State

    for group in groups:
        group_df = race_breakdown[race_breakdown['DEMOGRAPHIC_GROUP'] == group].reset_index(drop = True)
        group_df = group_df.rename(columns = {'STATE_NAME': 'State','Full_or_Partial_Vaccinated_Percent': group})
        group_df.drop(['DEMOGRAPHIC_GROUP', 'Fully_Vaccinated_Percent'], axis = 1, inplace = True)
        for i in range(len(race_df.index)):
            state = race_df['State'].iloc[i]
            if state in group_df['State'].values:
                value = group_df[group_df['State'] == state][group].iloc[0]
                if value > 100:
                    race_df[group].iloc[i] = 100
                else: 
                    value = round(value)
                    race_df[group].iloc[i] = group_df[group_df['State'] == state][group].iloc[0]     
            else:
                race_df[group].iloc[i] = 'N/A'
    
    # Adding new columns and changing names

    race_df = pd.concat([race_df, pd.DataFrame(list(range(0,50))), pd.DataFrame(list(range(0,50))), pd.DataFrame(list(range(0,50))), pd.DataFrame(list(range(0,50))), pd.DataFrame(list(range(0,50))), pd.DataFrame(list(range(0,50)))], axis = 1)

    race_df.columns = ['State','% White ≥ 1 Dose', '% Black ≥ 1 Dose', '% Hispanic or Latino ≥ 1 Dose','% Asian ≥ 1 Dose', '% Native Hawaiian/Other Pacific Islander ≥ 1 Dose', '% Native American/Alaska Native ≥ 1 Dose', 'WHITE','BLACK','HISPANIC OR LATINO', 'ASIAN', 'NATIVE HAWAIIAN OR OTHER PACIFIC ISLANDER', 'AMERICAN INDIAN OR ALASKA NATIVE']
    
    # Full Vaccination % By Race in Each State

    for group in groups:
        group_df = race_breakdown[race_breakdown['DEMOGRAPHIC_GROUP'] == group].reset_index(drop = True)
        group_df = group_df.rename(columns = {'STATE_NAME': 'State','Fully_Vaccinated_Percent': group})
        group_df.drop(['DEMOGRAPHIC_GROUP', 'Full_or_Partial_Vaccinated_Percent'], axis = 1, inplace = True)
        for i in range(len(race_df.index)):
            state = race_df['State'].iloc[i]
            if state in group_df['State'].values:
                value = group_df[group_df['State'] == state][group].iloc[0]
                if value > 100:
                    race_df[group].iloc[i] = 100.00
                else: 
                    value = round(value)
                    race_df[group].iloc[i] = group_df[group_df['State'] == state][group].iloc[0]     
            else:
                race_df[group].iloc[i] = 'N/A'
                
    race_df.columns = ['State','% White ≥ 1 Dose', '% Black ≥ 1 Dose', '% Hispanic or Latino ≥ 1 Dose','% Asian ≥ 1 Dose', '% Native Hawaiian/Other Pacific Islander ≥ 1 Dose', '% Native American/Alaska Native ≥ 1 Dose','% White Fully Vaccinated', '% Black Fully Vaccinated', '% Hispanic or Latino Fully Vaccinated','% Asian Fully Vaccinated', '% Native Hawaiian/Other Pacific Islander Fully Vaccinated', '% Native American/Alaska Native Fully Vaccinated']
    
    vaxx_info = pd.merge(vaxx_breakdown, race_df, on = 'State')
    
    vaxx_info['State'] = vaxx_info['State'].map(abbrev)
    
    return date, vaxx_info
'''
def vaxx_plot(cty):
    
    data = pd.read_csv('fulldataset.csv', index_col = 0)
    
    date = [col for col in data.columns if 'Fully' in col][-1].split('as of ')[1]

    df = data[data['County Name'] == cty]
    
    fig = go.Figure()    

    fig.add_trace(go.Bar(
    y=df['County Name'],
    x=df['% Fully Vaccinated as of {}'.format(date)],
    width=[0.1],
    name='% Fully Vaxx.',
    orientation='h',
    marker=dict(
        color='#69F68C'
        )
    ))

    fig.add_trace(go.Bar(
    y=df['County Name'],
    x=df['% ≥ 12 Fully Vaccinated as of {}'.format(date)],
    width=[0.1],
    name='% 12+ Fully Vaxx.',
    orientation='h',
    marker=dict(
        color='#81B8FF',
        )
    ))

    fig.add_trace(go.Bar(
    y=df['County Name'],
    x=df['% ≥ 18 Fully Vaccinated as of {}'.format(date)],
    width=[0.1],
    name='% 18+ Fully Vaxx.',
    orientation='h',
    marker=dict(
        color='#FF8195',
        )
    ))

    fig.add_trace(go.Bar(
    y=df['County Name'],
    x=df['% ≥ 65 Fully Vaccinated as of {}'.format(date)],
    width=[0.1],
    name='% 65+ Fully Vaxx.',
    orientation='h',
    marker=dict(
        color='#FFC300',
        )
    ))

    fig.update_layout(xaxis_range=[0,100], title ={'text':'Vaccination Progress in % People Vaccinated as of {}'.format(date) ,'xanchor': 'center',
        'yanchor': 'top'}, xaxis_title="% People Vaccinated", font_family="Raleway", hoverlabel_font_family = 'Raleway', title_x=0.5)

    fig.write_html('/app/templates/{cty}_vaxxplot.html'.format(cty = cty), full_html = False)

def multivaxx_plot():
    
    data = pd.read_csv('fulldataset.csv', index_col = 0)

    date = [col for col in data.columns if 'Fully' in col][-1].split('as of ')[1]

    data = data[data['% Fully Vaccinated as of {}'.format(date)] != 0].reset_index(drop = True)

    data['County FIPS'] = data['County FIPS'].apply(lambda value: '0' + str(value) if len(str(value)) == 4 else str(value))

    df_top = data.sort_values(by = '% Fully Vaccinated as of {}'.format(date)).tail(10)[['County Name', '% Fully Vaccinated as of {}'.format(date)]].reset_index(drop = True)
    df_bottom = data.sort_values(by = '% Fully Vaccinated as of {}'.format(date), ascending = False).tail(10)[['County Name', '% Fully Vaccinated as of {}'.format(date)]].reset_index(drop = True)
    
    with urlopen('https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json') as response:
        counties = json.load(response)

    #TOP 10

    fig_top = go.Figure()    
    '''
    fig_top.add_trace(go.Bar(
    y=df_top['County Name'],
    x=df_top['% Vaccinated ≥ 65'],
    width=[0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8],
    name='% 65+ Fully Vaxx.',
    orientation='h',
    marker=dict(
        color='#FFC300',
        )
    ))

    fig_top.add_trace(go.Bar(
    y=df_top['County Name'],
    x=df_top['% Vaccinated ≥ 18'],
    width=[0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8],
    name='% 18+ Fully Vaxx.',
    orientation='h',
    marker=dict(
        color='#FF8195',
        )
    ))

    fig_top.add_trace(go.Bar(
    y=df_top['County Name'],
    x=df_top['% Vaccinated ≥ 12'],
    width=[0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8],
    name='% 12+ Fully Vaxx.',
    orientation='h',
    marker=dict(
        color='#81B8FF',
        )
    ))
    '''
    
    fig_top.add_trace(go.Bar(
    y=df_top['County Name'],
    x=df_top['% Fully Vaccinated as of {}'.format(date)],
    width=[0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8],
    name='% Fully Vaxx.',
    orientation='h',
    marker=dict(
        color='#69F68C'
        )
    ))
    
    fig_top.update_layout(
    title={
        'text': "Plot Title",
        'y':0.9,
        'x':0.5,
        'xanchor': 'center',
        'yanchor': 'top'})
    
    
    fig_top.update_layout(xaxis_range=[0,100], title = {'text':'Counties with Highest Vaxx. Progress','xanchor': 'center',
        'yanchor': 'top'}, hovermode='y', xaxis_title="% People Fully Vaccinated", font_family = "Raleway", hoverlabel_font_family = "Raleway")
    
    fig_top.write_html('/app/templates/multivaxxplot_top.html', full_html = False)

    #BOTTOM 10
    fig_bottom = go.Figure()    
    '''
    fig_bottom.add_trace(go.Bar(
    y=df_bottom['County Name'],
    x=df_bottom['% Vaccinated ≥ 65'],
    width=[0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8],
    name='% 65+ Fully Vaxx.',
    orientation='h',
    marker=dict(
        color='#FFC300',
        )
    ))
    
    fig_bottom.add_trace(go.Bar(
    y=df_bottom['County Name'],
    x=df_bottom['% Vaccinated ≥ 18'],
    width=[0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8],
    name='% 18+ Fully Vaxx.',
    orientation='h',
    marker=dict(
        color='#FF8195',
        )
    ))

    fig_bottom.add_trace(go.Bar(
    y=df_bottom['County Name'],
    x=df_bottom['% Vaccinated ≥ 12'],
    width=[0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8],
    name='% 12+ Fully Vaxx.',
    orientation='h',
    marker=dict(
        color='#81B8FF',
        )
    ))
    '''
    fig_bottom.add_trace(go.Bar(
    y=df_bottom['County Name'],
    x=df_bottom['% Fully Vaccinated as of {}'.format(date)],
    width=[0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8],
    name='% Fully Vaxx.',
    orientation='h',
    marker=dict(
        color='#EC7063'
        )
    ))
    
    fig_bottom.update_layout(
    title={
        'text': "Plot Title",
        'y':0.9,
        'x':0.5,
        'xanchor': 'center',
        'yanchor': 'top'})
    
    
    fig_bottom.update_layout(xaxis_range=[0,100], title = {'text':'Counties with Lowest Vaxx. Progress','xanchor': 'center',
        'yanchor': 'top'}, hovermode='y', xaxis_title="% People Fully Vaccinated", font_family = "Raleway", hoverlabel_font_family = "Raleway")
    
    fig_bottom.write_html('/app/templates/multivaxxplot_bottom.html', full_html = False)
    
    fig_map = px.choropleth(data, geojson=counties, locations='County FIPS', color='% Fully Vaccinated as of {}'.format(date),
                           color_continuous_scale=['#FF3C33', '#FBF30B', '#41B26A'],
                           hover_name = 'County Name',
                           hover_data=['Population','% ≥ 12 Fully Vaccinated as of {}'.format(date), '% ≥ 18 Fully Vaccinated as of {}'.format(date), '% ≥ 65 Fully Vaccinated as of {}'.format(date)],
                           scope="usa",
                           labels={'% Fully Vaccinated as of {}'.format(date):'Current % Fully Vaccinated', '% ≥ 12 Fully Vaccinated as of {}'.format(date):'Current % 12+ Fully Vaccinated', '% ≥ 18 Fully Vaccinated as of {}'.format(date):'Current % 18+ Fully Vaccinated', '% ≥ 65 Fully Vaccinated as of {}'.format(date):'Current % 65+ Fully Vaccinated'}
                          )
    fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, font_family = "Raleway", hoverlabel_font_family = "Raleway")
    fig_map.update_traces(marker_line_width=0, marker_opacity=0.8, hoverlabel_bgcolor='#e3f1ff', hoverlabel_bordercolor = '#e3f1ff', hoverlabel_font_color='#000066')
    fig_map.update_geos(showsubunits=True, subunitcolor="black", subunitwidth = 1.4)

    fig_map.write_html('/app/templates/us_vaxxmap.html', full_html = False)

    return date

def scatter(x, y, trendline):

    data = pd.read_csv('fulldataset.csv')
    vaxx_col = [col for col in data.columns if "Fully" in col and "≥" not in col][0]
    data = data[data[vaxx_col] != 0]

    if trendline == 'y': 
        fig = px.scatter(x=data[x], y=data[y], trendline="ols", labels={
                     "x": x,
                     "y": y}, title="Scatterplot of {} and {}".format(x, y))
    else:
        fig = px.scatter(x=data[x], y=data[y], labels={
                     "x": x,
                     "y": y}, title="Scatterplot of {} and {}".format(x, y))
    fig.update_layout(font_family = "Raleway", hoverlabel_font_family = "Raleway", title_x = 0.5)
    
    fig.write_html('/app/templates/{}_{}_{}.html'.format(trendline, x, y), full_html = False)
'''
def violinplot(x, y, points):

    data = pd.read_csv('fulldataset.csv')
    vaxx_col = [col for col in data.columns if "Fully" in col and "≥" not in col][0]
    data = data[data[vaxx_col] != 0]

    if trendline == 'y': 
        fig = px.scatter(x=data[x], y=data[y], trendline="ols", labels={
                     "x": x,
                     "y": y}, title="Scatterplot of {} and {}".format(x, y))
    else:
        fig = px.scatter(x=data[x], y=data[y], labels={
                     "x": x,
                     "y": y}, title="Scatterplot of {} and {}".format(x, y))
    fig.update_layout(font_family = "Raleway", hoverlabel_font_family = "Raleway", title_x = 0.5)
    
    fig.write_html('/app/templates/{}_{}_{}.html'.format(trendline, x, y), full_html = False)
'''
