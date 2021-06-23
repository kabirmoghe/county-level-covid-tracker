import io
from io import StringIO
import os
import boto3
import pandas as pd

'''
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
'''

def create_vaxx_data():
    
    aws_access_key_id = 'AKIA2RCGHBDMFYOMRPOY'
    aws_secret_access_key = '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'
    
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
    
    for col in data.columns:
        if col != 'Recip_County' and 'Pct' not in col and col != 'Date':
            data.drop(col, axis = 1, inplace = True)
        
    data.columns = ['Date', 'County Name', '% Fully Vaccinated as of {}'.format(date),'% ≥ 12 Fully Vaccinated as of {}'.format(date), '% ≥ 18 Fully Vaccinated as of {}'.format(date), '% ≥ 65 Fully Vaccinated as of {}'.format(date)]

    data = data.iloc[::-1]
    
    data.reset_index(drop = True, inplace = True)
    
    data['Date'] = data['Date'].apply(lambda date: word_name(date))

    #data.to_csv('vaxxdataset.csv')
    
    filename = 'vaxxdataset.csv'
    bucketname = 'coviddatakm'
    
    csv_buffer = StringIO()
    data.to_csv(csv_buffer)
    
    client = boto3.client('s3')
    
    response = client.put_object(Body = csv_buffer.getvalue(), Bucket = bucketname, Key = filename)

if __name__ == '__main__':
    create_vaxx_data()