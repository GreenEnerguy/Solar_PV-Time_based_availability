# -*- coding: utf-8 -*-
"""
Created on Sat Oct 17 23:26:59 2020

@author: Rubén Martínez Fanals
         https://www.linkedin.com/in/fanals/
         https://greenenerguy.me/
"""
import os
import pandas as pd

def read_met_data(met_data_path, timeframe):
    '''
    Parameters
    ----------
    met_data_path : String name indicating the relative path of the folder where the meteorological data is located 
                    e.g. 'Met_Data' is the subfolder relative to the folder containing "Availability_Calc.py" where 
                    to look for this data
    timeframe : String name indicating the folder with the meteorological csv data to be read; e.g. the subfolder 
                \Met_Data\2020_09\ contains the csv file where the September meteo data is stored. In this instance, 
                timeframe refers to the string '2020_09'

    Returns
    -------
    meteo : Pandas Dataframe that contains the clean meteorological data read in the csv file located in 
            \met_data_path\timeframe, the index being day and time

    '''
    
    # In my specific case, the met data is stored in the timeframe folder within a .csv file 
    # that includes the string 'Report' in the file name
    path = os.path.join(os.getcwd(), met_data_path, timeframe)       
    for file in os.listdir(path):
        if file.endswith('csv') and 'Report' in file:
            met_data = file
            
    file_name = os.path.join(path, met_data)
    project_name = pd.read_csv(file_name).columns[0].split(';')[-1].replace('"', '')
                                                                    # get project name
                                                                    # from data columns
    
    # In the following chunk of code I conduct a cleaning of the csv file
    # first I read the .csv file and skip first two rows due to the configuration of the raw .csv file
    meteo = pd.read_csv(file_name, engine='python', delimiter='\;', skiprows=2)
    meteo = meteo.applymap(lambda x: x.replace('"', '')) # replace " from all the dataframe
    meteo.columns = ['RAD_' + str(i) + ' [W/m2]' for i in range(len(meteo.columns))]
    

    num_columns = len(meteo.columns)
        
    for col in meteo.columns[1:]:
        meteo[col] = pd.to_numeric(meteo[col], errors='coerce') # transform strings
                                                                # into numbers
        
    # get dates and times
    meteo['Day'] = meteo[meteo.columns[0]].apply(lambda x: x.split()[0].split('/')[0])
    meteo['Month'] = meteo[meteo.columns[0]].apply(lambda x: x.split()[0].split('/')[1])
    meteo['Year'] = meteo[meteo.columns[0]].apply(lambda x: x.split()[0].split('/')[2])
    meteo['Time'] = meteo[meteo.columns[0]].apply(lambda x: x.split()[1])
    
    # build date from Day, Month, Year and Time items from previous block
    meteo['Date'] = meteo['Year'] + '-' + meteo['Month'] + '-' + meteo['Day'] \
                         + ' ' + meteo['Time']
                         
    meteo['Date'] = pd.to_datetime(meteo['Date']) # create datetime object
    meteo.set_index('Date', inplace=True) # define datetime object as index of the dataframe
    del meteo[meteo.columns[0]] 
    meteo.drop(meteo.columns[num_columns-1:], inplace=True, axis=1)
    
    # start_date = meteo.index.values.astype(str)[0][:16] \
    #                             .replace('T', '-').replace(':', 'h') # get first measurement item
    # end_date = meteo.index.values.astype(str)[-1][:16] \
    #                            .replace('T', '-').replace(':', 'h') # get last measurement item
    
    # create name of the .csv file as a string
    # csv_name = os.getcwd() + '\\' + project_name + '_' + start_date + '_' + end_date + '.csv'
    
    return meteo
        