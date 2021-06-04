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

def county_list():
    ctys = list(pd.read_csv('https://raw.githubusercontent.com/kabirmoghe/Demographic-Data/main/countynames.csv')['County Name'].values)
    return ctys

def county_stats(county_name):
    if county_name == '':
        return "Please enter a county name (i.e. Orange County, CA)."
    else:
        data = pd.read_csv('fulldataset.csv', index_col = 0)

        data['County FIPS'] = data['County FIPS'].apply(lambda value: '0' + str(value) if len(str(value)) == 4 else str(value))

        infs = [column for column in data.columns if "Infection" in column.split() and "Cumulative" not in column.split() and "Predicted" not in column.split()]

        cols = data.columns

        inf_col = 0
        for col in cols:
            if "Infection" in col.split() and "as" in col.split():
                inf_col = col

        sorted_data = data.sort_values(by = inf_col, ascending = False)[['County Name', inf_col]].reset_index(drop = True)

        ctynum = len(sorted_data)

        high25pct = round(ctynum*0.25)
        low25pct = round(ctynum*0.75)

        if county_name in data['County Name'].values:
            '''county_df = data[data['County Name'] == county_name][infs].transpose().reset_index()
            county_df['Time'] = ["Jan '20", "Feb '20", "Mar '20", "Apr '20", "May '20", "Jun '20", "Jul '20", "Aug '20", "Sept '20", "Oct '20", "Nov '20", "Dec '20", "Jan '21", "Feb '21", "Mar '21", "Apr '21", "May '21"]
            county_df['Infection Rate per 100,000 for {county_name}'.format(county_name = county_name)] = county_df.iloc[:,1]
            
            sns.barplot(x = "Time", y = 'Infection Rate per 100,000 for {county_name}'.format(county_name = county_name), data = county_df, palette = 'plasma').get_figure()
            plt.savefig('../covidapp/static/countyplot.png')
            '''
            des_row = data[data['County Name'] == str(county_name)]

            des_row.rename(index = {des_row.index.values[0]: county_name}, inplace = True)

            otherinfo = des_row.iloc[:, -11:]
            
            stat = des_row[inf_col].iloc[0]

            rank = sorted_data[sorted_data['County Name']==county_name].index[0]+1

            pct = round((1-(rank/len(sorted_data)))*100, 2)

            if pct == 0.0:
                rec = 'Though there is a relatively low risk of infection in {county_name}, precaution should still be taken, and following social distancing guidelines is important in preventing a rise in spread:'.format(county_name = county_name)
                riskimg = 'riskchartbot.png'
                info = "With a rank of {rank} out of {ctynum} included counties, {county_name} is the lowest county in terms of {inf_col}.".format(rank = rank, ctynum = ctynum, county_name = county_name, pct = pct, inf_col = inf_col)
            elif round(pct) == 100.0:
                rec = 'There is a relatively high risk of infection in {county_name}, so precaution should be taken and social distancing guidelines should be followed strictly:'.format(county_name = county_name)    
                riskimg = 'riskcharttop.png'
                info = "With a rank of {rank} out of {ctynum} included counties, {county_name} is the highest county in terms of {inf_col}.".format(rank = rank, ctynum = ctynum, county_name = county_name, pct = pct, inf_col = inf_col)
            else:
                if rank < high25pct:
                    rec = 'There is a relatively high risk of infection in {county_name}, so precaution should be taken and social distancing guidelines should be followed strictly:'.format(county_name = county_name)
                    #rateimg = 'topratechart.png'
                    riskimg = 'riskcharttop.png'
                elif high25pct < rank < low25pct:
                    rec = 'There is a relatively moderate risk of infection in {county_name}, so precaution should still be taken and social distancing guidelines should still be followed:'.format(county_name = county_name)
                    #rateimg = 'midratechart.png'
                    riskimg = 'riskchartmid.png'
                else:
                    rec = 'Though there is a relatively low risk of infection in {county_name}, precaution should still be taken, and following social distancing guidelines is important in preventing a rise in spread:'.format(county_name = county_name)
                    #rateimg = 'botratechart.png'
                    riskimg = 'riskchartbot.png'
                
                info = "With a rank of {rank} out of {ctynum} included counties, {county_name} is higher than {pct}% of counties in terms of {inf_col}.".format(rank = rank, ctynum = ctynum, county_name = county_name, pct = pct, inf_col = inf_col)

            return otherinfo, stat, info, rec, riskimg
        else:
            return "Please enter a valid county name (i.e. Orange County, CA). The county you entered, '{county_name}', may not have complete information.".format(county_name = county_name)

def usplot():
    with urlopen('https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json') as response:
        counties = json.load(response)
    
    data = pd.read_csv('fulldataset.csv', index_col = 0)

    data['County FIPS'] = data['County FIPS'].apply(lambda value: '0' + str(value) if len(str(value)) == 4 else str(value))
    
    last_inf_rate = [column for column in data.columns if "Infection" in column.split() and "Cumulative" not in column.split() and "Predicted" not in column.split()][-1]

    data['Log {name}'.format(name = last_inf_rate)] = data[last_inf_rate].apply(lambda value: np.log(value) if value != 0 else value)
    
    fig = px.choropleth(data, geojson=counties, locations='County FIPS', color='Log {name}'.format(name = last_inf_rate),
                           color_continuous_scale="Plasma",
                           hover_name = 'County Name',
                           hover_data=[last_inf_rate],
                           scope="usa",
                           labels={'Log {name}'.format(name = last_inf_rate):'Current Log Infection Rate'}
                          )
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, font_family = "Raleway", hoverlabel_font_family = "Raleway")
    fig.update_traces(marker_line_width=0, hoverlabel_bgcolor='#e3f1ff', hoverlabel_bordercolor = '#e3f1ff', hoverlabel_font_color='#000066')
    fig.write_html("/app/templates/usplot.html", full_html = False)
    
    cols = data.columns

    inf_col = 0
    for col in cols:
        if "Infection" in col.split() and "as" in col.split() and "Log" not in col.split():
            inf_col = col

    sorted_data = data.sort_values(by = inf_col, ascending = False)[['County Name', inf_col]].reset_index(drop = True)

    top10 = sorted_data.head(10)[['County Name', inf_col]].reset_index(drop = True)
    bot10 = sorted_data.tail(10)[['County Name', inf_col]].reset_index(drop = True)

    #top10lst = []
    
    #for i in range(10):
    #    top10lst.append('{cty}: {stat}'.format(cty = top10['County Name'].iloc[i], stat = round(float(top10[inf_col].iloc[i]),2)))

    return top10, bot10

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

def vaxx_plot(cty):
    
    state = cty.split(', ')[-1]
    
    date, data = create_vaxx_data()
    
    df = data[data['State'] == state]
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
    y=df['State'],
    x=df['% ≥ 1 Dose'],
    width=[0.1],
    name='% ≥1 Dose',
    orientation='h',
    marker=dict(
        color='#B8D4FE'
        )
    ))
    
    fig.add_trace(go.Bar(
    y=df['State'],
    x=df['% Fully Vaccinated'],
    width=[0.1],
    name='% Fully Vaxx.',
    orientation='h',
    marker=dict(
        color='#69F68C',
        )
    ))
    
    fig.update_layout(xaxis_range=[0,100], barmode='overlay', title ={'text':'{state} Vaccination Progress in % People Vaccinated as of {date}'.format(state = state, date = date)}, xaxis_title="% People Vaccinated", font_family="Raleway", hovermode = 'y', hoverlabel_font_family = 'Raleway')

    fig.write_html('/app/templates/{state}_vaxxplot.html'.format(state = state), full_html = False) 

    #fig.write_html('../covidapp/templates/vaxxplot.html', full_html = False)

def multivaxx_plot():
    
    date, df = create_vaxx_data()
    df_top = df.sort_values(by = '% ≥ 1 Dose').tail(10)[['State', '% ≥ 1 Dose', '% Fully Vaccinated']].reset_index(drop = True)
    df_bottom = df.sort_values(by = '% ≥ 1 Dose', ascending = False).tail(10)[['State', '% ≥ 1 Dose', '% Fully Vaccinated']].reset_index(drop = True)
    
    #TOP 10

    fig_top = go.Figure()
    fig_top.add_trace(go.Bar(
    y=df_top['State'],
    x=df_top['% ≥ 1 Dose'],
    name='% ≥1 Dose',
    orientation='h',
    marker=dict(
        color='#B8D4FE'
        )
    ))
    
    fig_top.add_trace(go.Bar(
    y=df_top['State'],
    x=df_top['% Fully Vaccinated'],
    name='% Fully Vaxx.',
    orientation='h',
    marker=dict(
        color='#69F68C',
        )
    ))
    
    fig_top.update_layout(
    title={
        'text': "Plot Title",
        'y':0.9,
        'x':0.5,
        'xanchor': 'center',
        'yanchor': 'top'})
    
    fig_top.update_layout(xaxis_range=[0,100], barmode='overlay', title = {'text':'States with Highest Vaxx. Progress','xanchor': 'center',
        'yanchor': 'top'}, hovermode='y', xaxis_title="% People Vaccinated", font_family = "Raleway", hoverlabel_font_family = "Raleway")
    
    fig_top.write_html('/app/templates/multivaxxplot_top.html', full_html = False)

    #BOTTOM 10

    fig_bottom = go.Figure()
    fig_bottom.add_trace(go.Bar(
    y=df_bottom['State'],
    x=df_bottom['% ≥ 1 Dose'],
    name='% ≥1 Dose',
    orientation='h',
    marker=dict(
        color='#B8D4FE'
        )
    ))
    
    fig_bottom.add_trace(go.Bar(
    y=df_bottom['State'],
    x=df_bottom['% Fully Vaccinated'],
    name='% Fully Vaxx.',
    orientation='h',
    marker=dict(
        color='#F04629',
        )
    ))
    
    fig_bottom.update_layout(
    title={
        'text': "Plot Title",
        'y':0.9,
        'x':0.5,
        'xanchor': 'center',
        'yanchor': 'top'})
    
    fig_bottom.update_layout(xaxis_range=[0,100], barmode='overlay', title = {'text':'States with Lowest Vaxx. Progress'.format(date = date),'xanchor': 'center',
        'yanchor': 'top'}, hovermode='y', xaxis_title="% People Vaccinated", font_family = "Raleway", hoverlabel_font_family = "Raleway")
    
    fig_bottom.write_html('/app/templates/multivaxxplot_bottom.html', full_html = False)

    fig_map = px.choropleth(locations=df['State'], locationmode="USA-states", color=df['% ≥ 1 Dose'], scope="usa", color_continuous_scale='Bluered_r', hover_name = df['State'],
                           hover_data=[df['% Fully Vaccinated']],
                           labels={'locations': 'State', 'hover_data_0': '% Fully Vaccinated', 'color':'% At Least 1 Dose'})
    fig_map.update_layout(font_family = "Raleway", hoverlabel_font_family = "Raleway")
    fig_map.update_traces(marker_line_width=0, hoverlabel_bgcolor='#e3f1ff', hoverlabel_bordercolor = '#e3f1ff', hoverlabel_font_color='#000066')

    fig_map.write_html('/app/templates/us_vaxxmap.html', full_html = False)

    return date
