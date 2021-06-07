import numpy as np
import pandas as pd

def create_vaxx_data():

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

    vaxx = pd.read_csv('https://data.cdc.gov/api/views/8xkx-amqh/rows.csv?accessType=DOWNLOAD')
    
    latest_date = vaxx['Date'][0]
    
    month, day, year = [int(value) for value in latest_date.split('/')]
    date = '{month} {day}, {year}'.format(month = no_mo[month], day = day, year = year)
    
    #year, month, day = [int(val) for val in latest_date.split('-')]
    #date = '{month} {day}, {year}'.format(month = no_mo[month], day = day, year = year)

    vaxx_data = vaxx[vaxx['Date'] == latest_date].sort_values(by = 'Recip_State').reset_index(drop = True)
    vaxx_data['Recip_County'] = vaxx_data['Recip_County'] + ', ' + vaxx_data['Recip_State']
    
    for col in vaxx_data.columns:
        if col != 'Recip_County' and 'Pct' not in col:
            vaxx_data.drop(col, axis = 1, inplace = True)
            
    vaxx_data.columns = ['County Name', '% Fully Vaccinated as of {}'.format(date),'% ≥ 12 Fully Vaccinated as of {}'.format(date), '% ≥ 18 Fully Vaccinated as of {}'.format(date), '% ≥ 65 Fully Vaccinated as of {}'.format(date)]

    return vaxx_data