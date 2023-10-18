import numpy as np
import pandas as pd
import requests
import json
from urllib.request import urlopen
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import matplotlib
import seaborn as sns

# Gets list of counties (v. helpful for select fields with 'data' page)
def county_list():

    ctys = list(pd.read_csv('fulldataset.csv')['County Name'].values)
    return ctys

# Gets nationwide average PLT plot
def nationwideavg():

    matplotlib.use('agg')

    data = pd.read_csv('fulldataset.csv', index_col = 0)
    
    nationdata = pd.DataFrame(data[[col for col in data.columns if 'Cases' in col and 'Moving' in col]].mean()).reset_index()
    nationdata.columns = ['Week','Approx. Moving Avg.']
    nationdata['Week'] = nationdata['Week'].apply(lambda value: value.split('Avg. ')[-1].split(',')[0])
    
    nationdata.plot(x = 'Week', y = 'Approx. Moving Avg.', linewidth=25, color = '#3258a8', legend = False)
    plt.axis('off')
    plt.savefig('/app/static/nationwideavg.png', bbox_inches='tight')

# Gets nationwide vaccination progress graphic
def nationwidevaxx():

    matplotlib.use('agg')
    sns.set(style = 'dark')

    data = pd.read_csv('https://data.cdc.gov/api/views/unsk-b7fc/rows.csv?accessType=DOWNLOAD')
    
    fully_vaxx, pct_partial = round((data[data['Location'] == 'US'].iloc[0][['Series_Complete_Yes','Administered_Dose1_Pop_Pct', ]][0])/1000000, 1), data[data['Location'] == 'US'].iloc[0][['Series_Complete_Yes','Administered_Dose1_Pop_Pct', ]][1]

    y = [pct_partial]

    plt.figure(figsize = (10,2))
    plt.barh(width = y, y = ' ')
    plt.tick_params(labelbottom = False)
    plt.xlim(0,100)
    plt.savefig('/app/static/nationwidevaxx.png',  bbox_inches='tight')

    return fully_vaxx, pct_partial

# Gets the stats for a singular county (i.e. on the 'data' page)
def county_stats(county_name):
    if county_name == '':
        return "Please enter a county name (i.e. Orange County, CA)."
    else:
        data = pd.read_csv('fulldataset.csv', index_col = 0)
        vaxx_data = pd.read_csv('vaxxdataset.csv', index_col = 0)
        data['County FIPS'] = data['County FIPS'].apply(lambda value: '0' + str(value) if len(str(value)) == 4 else str(value))
        cols = data.columns

        inf_col = 0
        for col in cols:
            if "Cases" in col.split() and "per" in col.split():
                inf_col = col


        c_update = inf_col.split('of ')[-1]
        sorted_data = data.sort_values(by = inf_col, ascending = False)[['County Name', inf_col]].reset_index(drop = True)

        ctynum = len(sorted_data)

        high25pct = round(ctynum*0.25)
        low25pct = round(ctynum*0.75)

        # Sets thresholds for different COVID risk levels
        green = 1 # low
        yellow = 10 # moderately low
        orange = 25 # moderately high (red is greater than 25 --> high)

        # Info on specific county ("desired row")
        des_row = data[data['County Name'] == str(county_name)]
        des_row.rename(index = {des_row.index.values[0]: county_name}, inplace = True)

        # Details on masks
        mask_details= [des_row[col].values[0] for col in des_row.columns if 'mask' in col.lower()][0]
        mask_links = des_row["Learn More"].values[0]
        m_update = [col.split('as of ')[1] for col in data.columns if 'Mask Mandate Details' in col][0]

        des_row.drop(['Mask Mandate Details as of {}'.format(m_update), "Learn More"], axis = 1, inplace = True)

        data2 = data.drop(['Mask Mandate Details as of {}'.format(m_update), "Learn More"], axis = 1)

        # To compare metrics with the "average" county
        meaninfo = pd.DataFrame(pd.concat([data['Population'], data2.iloc[:, -15:-6]], axis = 1).mean()).transpose().round(2)

        for col in meaninfo.columns:
            if col != 'Population':
                meaninfo[col] = meaninfo[col].round(2)
            else:
                meaninfo[col] = int(meaninfo[col].round())
        
        meaninfo.index = ['Avg. American County']

        # Other metrics on the county
        otherinfo = pd.concat([pd.concat([des_row['Population'], des_row.iloc[:, -15:-6]], axis = 1), meaninfo])

        for col in otherinfo.columns:
            otherinfo[col] = otherinfo[col].apply(lambda value: "{:,}".format(value))

        stat = des_row[inf_col].iloc[0]

        rank = sorted_data[sorted_data['County Name']==county_name].index[0]+1

        # Building up the slider for infections' moving average risk

        css_prop = stat/27

        if css_prop <= 1:
            css_prop = css_prop
        else:
            css_prop = 1.0

        prop = (1-(rank/len(sorted_data)))
        pct = round(prop*100, 2)

        # Messages to be outputted for each risk value
        if stat == 0.0:
            rec = '{county_name} has a low risk of infection and is on track for containment. Regardless, some precaution should be taken and the guidelines below should be followed (see details below).'.format(county_name = county_name)
            color = '#7cff02'
            info = "With a rank of {rank} out of {ctynum} included counties, {county_name} is one of the lowest counties in terms of {inf_col}.".format(rank = rank, ctynum = ctynum, county_name = county_name, pct = pct, inf_col = inf_col)
            risk = 'Low'
        elif round(pct) == 100.0:
            rec = 'There is a high risk of infection in {county_name}, so precaution should be taken and guidelines should be followed strictly (see details below).'.format(county_name = county_name) 
            color = '#ff0600'
            info = "With a rank of {rank} out of {ctynum} included counties, {county_name} is the highest county in terms of {inf_col}.".format(rank = rank, ctynum = ctynum, county_name = county_name, pct = pct, inf_col = inf_col)
            risk = 'High'
        else:
            if stat < green:
                rec = '{county_name} has a low risk of infection and is on track for containment. Regardless, some precaution should be taken and guidelines should be followed (see details below).'.format(county_name = county_name)
                color = '#7cff02'
                risk = 'Low'
            elif green <= stat < yellow:
                rec = '{county_name} has a moderately low risk of infection, and strategic choices must be made about which package of non-pharmaceutical interventions to use for control. Precaution should be still be taken and guidelines should be followed (see details below).'.format(county_name = county_name) 
                color = '#fff800'
                risk = 'Moderately Low'
            elif yellow <= stat < orange:
                rec = '{county_name} has a moderately high risk of infection, and strategic choices must be made about which package of non-pharmaceutical interventions to use for control. Stay-at-home orders are advised unless viral testing and contact tracing capacity are implementable at levels meeting surge indicator standards. Precaution should be taken and guidelines should be followed (see details below).'.format(county_name = county_name)
                color = '#ffab00'
                risk = 'Moderately High'
            else:
                rec = '{county_name} has a high risk of infection, and stay-at-home orders may be necessary. Extra precaution should be taken and guidelines should be followed (see details below).'.format(county_name = county_name)
                color = '#ff0600'
                risk = 'High'
            if pct >= 50:
                info = "With a rank of {rank} out of {ctynum} included counties, {county_name} has a moving average higher than {pct}% of counties.".format(rank = rank, ctynum = ctynum, county_name = county_name, pct = pct)
            else:
                info = "With a rank of {rank} out of {ctynum} included counties, {county_name} has a moving average lower than {pct}% of counties.".format(rank = rank, ctynum = ctynum, county_name = county_name, pct = round(100-pct,2))

        riskimg = 'riskchart.png' # Not currently used...
        risk_pos = (round(26.5+(49*css_prop),2))
               
        m_update = 'Updated {}'.format([col.split('as of ')[1] for col in data.columns if 'Mask Mandate Details' in col][0])

        return otherinfo, stat, info, rec, risk_pos, pct, mask_details, mask_links, color, risk, c_update, m_update
        
# Nationwide choropleth map for either cases/deaths moving averages (infections/mortality rate)
def usplot(c_or_d):
    # Gets FIP codes for plotting
    with urlopen('https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json') as response:
        counties = json.load(response)
    
    data = pd.read_csv('fulldataset.csv', index_col = 0)
    
    # NE/FL have weird data
    data = data[data['State'] != 'NE']
    data = data[data['State'] != 'FL']

    config = {'displayModeBar': False}

    data['County FIPS'] = data['County FIPS'].apply(lambda value: '0' + str(value) if len(str(value)) == 4 else str(value))
    
    # Cases/infections plot
    if c_or_d == 'c':

        last_case_rate = [column for column in data.columns if "Cases" in column.split() and "per" in column.split()][0]
        
        date = last_case_rate.split('as of ')[1]

        num0 = len(data[data[last_case_rate] == 0])

        fig = px.choropleth(data, geojson=counties, locations='County FIPS', color=last_case_rate,
                               color_continuous_scale=['#3EAC58', '#F6E520','#F6E520','#F6E520','#F6E520', '#ED9A0C', '#ED9A0C','#ED9A0C', '#ED9A0C', '#ED9A0C', '#E64B01','#E64B01','#E64B01','#E64B01','#C92607'],
                               hover_name = 'County Name',
                               hover_data=[last_case_rate, 'Population'],
                               scope="usa", range_color=[0,40],
                               labels={last_case_rate:'Infection Risk (Daily Cases per 100k)'}

                               )
        fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, font_family = "Raleway", hoverlabel_font_family = "Raleway")
        fig.update_traces(marker_line_width=0, marker_opacity=0.8, hoverlabel_bgcolor='#e3f1ff', hoverlabel_bordercolor = '#e3f1ff', hoverlabel_font_color='#000066')
        fig.update_geos(showsubunits=True, subunitcolor="black", subunitwidth = 1.4)
        fig.write_html("/app/templates/c_usplot.html", full_html = False, config = config)
        
        sorted_data = data.sort_values(by = last_case_rate, ascending = False)[['County Name', last_case_rate]].reset_index(drop = True)

        top10 = sorted_data.head(10)[['County Name', last_case_rate]].reset_index(drop = True)
        bot10 = sorted_data.tail(10)[['County Name', last_case_rate]].reset_index(drop = True)

    # Deaths/mortality plot
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
        fig.write_html("/app/templates/d_usplot.html", full_html = False, config = config)

        sorted_data = data.sort_values(by = last_death_rate, ascending = False)[['County Name', last_death_rate]].reset_index(drop = True)

        top10 = sorted_data.head(10)[['County Name', last_death_rate]].reset_index(drop = True)
        bot10 = sorted_data.tail(10)[['County Name', last_death_rate]].reset_index(drop = True)

    return top10, bot10, date, num0

# Produces plot for infections moving average for a county
def avg_plot(cty):

    data = pd.read_csv('fulldataset.csv')
    data = pd.concat([data['County Name'], data[[col for col in data.columns if 'Cases' in col and 'Moving Avg.' in col]]], axis = 1)

    data = data[data['County Name'] == cty]

    data = data.transpose().iloc[1:].reset_index()

    data.columns = ['Date', 'Moving Avg']

    data['Date (Week of)'] = data['Date'].apply(lambda value: value.split('Avg. ')[-1])
    data.drop('Date', axis = 1, inplace = True)

    yval = 3

    for value in data['Moving Avg']:
        if value >= 25:
            if (value-27)+3 > yval:
                yval = (value-27)+3
            else:
                None
        else:
            None

    fig = go.Figure()

    fig.add_trace(go.Scatter(name = '(Moving Avg)', x = data['Date (Week of)'], y = data['Moving Avg'], line={'color': '#18FF51', 'width':5}, mode='lines+markers', hoverinfo = 'y'))
    fig.add_trace(go.Scatter(name = '(Moving Avg)', x=data['Date (Week of)'], y=data['Moving Avg'].where(data['Moving Avg'] >= 1), line={'color': '#FFF90F', 'width':5}, mode='lines+markers', hoverinfo = 'y'))
    fig.add_trace(go.Scatter(name = '(Moving Avg)', x=data['Date (Week of)'], y=data['Moving Avg'].where(data['Moving Avg'] >= 10), line={'color': '#FFAF00', 'width':5}, mode='lines+markers', hoverinfo = 'y'))
    fig.add_trace(go.Scatter(name = '(Moving Avg)', x=data['Date (Week of)'], y=data['Moving Avg'].where(data['Moving Avg'] >= 25), line={'color': '#ff0b00', 'width':5}, mode='lines+markers', hoverinfo = 'y'))
    
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', yaxis_range=[0,25+yval],
        font_family="Raleway", hoverlabel_font_family = 'Raleway', showlegend = False, hoverlabel_bgcolor = 'white', hoverlabel_bordercolor = 'white', hoverlabel_font_color = 'black', xaxis_showgrid = False, margin = dict(t=0, pad = 20), font_color = 'black', xaxis_title = '(Week of)'
    )

    config = {'displayModeBar': False}

    fig.write_html('/app/templates/{cty}_movingavgplot.html'.format(cty = cty), full_html = False, config = config)

# Produces vaccination plots (by age group and by full/partial vaxx. status)
def vaxx_plot(cty):
    data = pd.read_csv('vaxxdataset.csv', index_col = 0)
    data = data[data['County Name'] == cty]

    v_update = data.columns[2].split('of ')[-1]

    full_date = list(data['Date'])[-1]
    
    data.reset_index(drop = True, inplace = True)
    
    no_mo = {'January':'Jan.',
             'February':'Feb.',
             'March':'Mar.',
             'April':'Apr.',
             'May':'May',
             'June':'Jun.',
             'July':'Jul.',
             'August':'Aug.',
             'September':'Sep.',
             'October':'Oct.',
             'November':'Nov.',
             'December':'Dec.'
         }
    
    def easy_name(date):
        
        date = date.split()
        
        mo = no_mo[date[0]]
        yr = "'{}".format((date[2])[2:])
        
        return '{} {}'.format(mo, yr)
        
    data['Date'] = data['Date'].apply(lambda value: easy_name(value))
    
    date = list(data['Date'])[-1]
    
    # Age breakdown vaxx. progress over time
    fig = go.Figure()    

    fig.add_trace(go.Scatter(
            name='% Fully Vaccinated',
            x=data['Date'],
            y=data['% Fully Vaccinated as of {}'.format(full_date)],
            marker=dict(
                color='#69F68C')
        ))

    fig.add_trace(go.Scatter(
            name='% 12+ Fully Vaxx.',
            x=data['Date'],
            y=data['% ≥ 12 Fully Vaccinated as of {}'.format(full_date)],
            marker=dict(
                color='#EAB7F9')
        ))


    fig.add_trace(go.Scatter(
            name='% 18+ Fully Vaxx.',
            x=data['Date'],
            y=data['% ≥ 18 Fully Vaccinated as of {}'.format(full_date)],
            marker=dict(
                color='#FF8195')
        ))

    fig.add_trace(go.Scatter(
            name='% 65+ Fully Vaxx.',
            x=data['Date'],
            y=data['% ≥ 65 Fully Vaccinated as of {}'.format(full_date)],
            marker=dict(
                color='#FFC300')
        ))
    fig.update_layout(
        yaxis_title='% Fully Vaxx. by Age Group', yaxis_range=[0,100], xaxis_title = 'Month',
        title='Vaxx. Progress for {}'.format(cty), title_x = 0.5, font_family="Raleway", hoverlabel_font_family = 'Raleway', showlegend = False
    )
    
    # Full vs. partially vaxx. breakdown progress over time
    fig2 = go.Figure()

    if len(data[data['% Fully Vaccinated as of {}'.format(full_date)] > data['% At Least Partially Vaccinated as of {}'.format(full_date)]]) > 0:

        fig2.add_trace(go.Scatter(
            name='% Fully Vaccinated',
            x=data['Date'],
            y=data['% Fully Vaccinated as of {}'.format(full_date)],
            marker=dict(
                color='#69F68C')
        ))

        vaxxkeytype = 'vaxxkeyissue'

    else:

        fig2.add_trace(go.Scatter(
                name='% Fully Vaccinated',
                x=data['Date'],
                y=data['% Fully Vaccinated as of {}'.format(full_date)],
                marker=dict(
                    color='#69F68C')
            ))

        fig2.add_trace(go.Scatter(
                name='% 12+ Fully Vaxx.',
                x=data['Date'],
                y=data['% At Least Partially Vaccinated as of {}'.format(full_date)],
                marker=dict(
                    color='#81B8FF')
            ))
    
        vaxxkeytype = 'vaxxkey'

    fig2.update_layout(
        yaxis_title='% Fully and Part. Vaxx', yaxis_range=[0,100], xaxis_title = 'Month',
        title='Vaxx. Progress for {}'.format(cty), title_x = 0.5, font_family="Raleway", hoverlabel_font_family = 'Raleway', showlegend = False
    )
    
    # Age breakdown vaxx. current state
    data = pd.read_csv('fulldataset.csv', index_col = 0)
    data = data[data['County Name'] == cty]

    fig3 = go.Figure()    

    fig3.add_trace(go.Bar(
    y=['All'],
    x=data['% Fully Vaccinated as of {}'.format(full_date)],
    width=[0.5],
    name='% Fully Vaxx.',
    orientation='h',
    marker=dict(
        color='#69F68C'
        )
    ))

    fig3.add_trace(go.Bar(
    y=['12+'],
    x=data['% ≥ 12 Fully Vaccinated as of {}'.format(full_date)],
    width=[0.5],
    name='% 12+ Fully Vaxx.',
    orientation='h',
    marker=dict(
        color='#EAB7F9',
        )
    ))

    fig3.add_trace(go.Bar(
    y=['18+'],
    x=data['% ≥ 18 Fully Vaccinated as of {}'.format(full_date)],
    width=[0.5],
    name='% 18+ Fully Vaxx.',
    orientation='h',
    marker=dict(
        color='#FF8195',
        )
    ))

    fig3.add_trace(go.Bar(
    y = ['65+'],
    x=data['% ≥ 65 Fully Vaccinated as of {}'.format(full_date)],
    width=[0.5],
    name='% 65+ Fully Vaxx.',
    orientation='h',
    marker=dict(
        color='#FFC300',
        )
    ))

    fig3.update_layout(xaxis_range=[0,100], title ={'text':'% Vaccinated, {}'.format(full_date) ,'xanchor': 'center',
        'yanchor': 'top'}, xaxis_title="% People Vaccinated", yaxis_title = 'Age Demographic', font_family="Raleway", hoverlabel_font_family = 'Raleway', title_x=0.5, showlegend = False)

    # Full vs. partially vaxx Current State
    fig4 = go.Figure()    

    fig4.add_trace(go.Bar(
        x=data['% At Least Partially Vaccinated as of {}'.format(full_date)],
        y=['1+ Dose'],
        width=[0.5],
        name='% ≥ 1 Dose.',
        orientation='h',
        marker=dict(
            color='#81B8FF',
            )
        ))
    
    fig4.add_trace(go.Bar(
        y=['Full.'],
        x=data['% Fully Vaccinated as of {}'.format(full_date)],
        width=[0.5],
        name='% Fully Vaxx.',
        orientation='h',
        marker=dict(
            color='#69F68C'
            )
        ))
    
    fig4.update_layout(xaxis_range=[0,100], title ={'text':'% Vaccinated, {}'.format(full_date) ,'xanchor': 'center',
        'yanchor': 'top'}, xaxis_title="% People Vaccinated", font_family="Raleway", hoverlabel_font_family = 'Raleway', title_x=0.5, showlegend = False)

    config = {'displayModeBar': False}

    fig.write_html('/app/templates/{cty}_agevaxxprogressplot.html'.format(cty = cty), full_html = False, config = config)
    fig2.write_html('/app/templates/{cty}_fullpartvaxxprogressplot.html'.format(cty = cty), full_html = False, config = config)
    fig3.write_html('/app/templates/{cty}_agevaxxplot.html'.format(cty = cty), full_html = False, config = config)
    fig4.write_html('/app/templates/{cty}_fullpartvaxxplot.html'.format(cty = cty), full_html = False, config = config)

    return v_update, vaxxkeytype

# Produces the nationwide choropleth map on vaccination progress
def multivaxx_plot():
    
    data = pd.read_csv('fulldataset.csv', index_col = 0)
    date = [col for col in data.columns if 'Fully' in col][-1].split('as of ')[1]
    data = data[data['% Fully Vaccinated as of {}'.format(date)] != 0].reset_index(drop = True)
    data['County FIPS'] = data['County FIPS'].apply(lambda value: '0' + str(value) if len(str(value)) == 4 else str(value))

    df_top = data.sort_values(by = '% Fully Vaccinated as of {}'.format(date)).tail(10)[['County Name', '% Fully Vaccinated as of {}'.format(date)]].reset_index(drop = True)
    df_bottom = data.sort_values(by = '% Fully Vaccinated as of {}'.format(date), ascending = False).tail(10)[['County Name', '% Fully Vaccinated as of {}'.format(date)]].reset_index(drop = True)
    
    with urlopen('https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json') as response:
        counties = json.load(response)

    # TOP 10
    fig_top = go.Figure()    
    
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
    
    config = {'displayModeBar': False}

    fig_top.write_html('/app/templates/multivaxxplot_top.html', full_html = False, config = config)

    # BOTTOM 10
    fig_bottom = go.Figure()    
    
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
    
    fig_bottom.write_html('/app/templates/multivaxxplot_bottom.html', full_html = False, config = config)
    
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

    fig_map.write_html('/app/templates/us_vaxxmap.html', full_html = False, config = config)

    return date

# Allows users to explore the relationship between two attributes in the data (x, y) and add a trendline if wanted
def scatter(x, y, trendline):

    config = {'displayModeBar': False}

    data = pd.read_csv('fulldataset.csv', index_col = 0)
    vaxx_col = [col for col in data.columns if "Fully" in col and "≥" not in col][0]
    data = data[data[vaxx_col] != 0]
    
    if trendline == 'y': 
        fig = px.scatter(data_frame = data, x = x, y=y, trendline="ols", labels={
                     "x": x,
                     "y": y}, title="Scatterplot of {} and {}".format(x, y),
                     hover_name = 'County Name')
    else:
        fig = px.scatter(data_frame = data, x=x, y=y, labels={
                     "x": x,
                     "y": y}, title="Scatterplot of {} and {}".format(x, y),
                     hover_name = 'County Name')
    fig.update_layout(font_family = "Raleway", hoverlabel_font_family = "Raleway", title_x = 0.5)
    
    fig.write_html('/app/templates/{}_{}_{}.html'.format(trendline, x, y), full_html = False)
