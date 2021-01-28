# -*- coding: utf-8 -*-
"""
Created on Mon Oct 19 23:02:59 2020

@author: Rubén Martínez
"""
import os
import pandas as pd

def read_inv_data(inv_data_path, timeframe):
    '''
    Parameters
    ----------
    inv_data_path : String name indicating the relative path where the inverter active power data is located 
                    e.g. 'Inv_Data' is the subfolder from current folder where to look for this data
    timeframe : String name indicating the folder where the inverter active power csv data to be read is located;
                e.g. the subfolder \Inv_Data\2020_09 contains the csv file where the September inverter power data
                is located. timeframe refers to '2020_09'

    Returns
    -------
    inv : Pandas Dataframe containing the clean active power inverter data read in the csv file located in 
            \inv_data_path\timeframe, which index is day and time
    '''
    
    path = os.path.join(os.getcwd(), inv_data_path, timeframe)       
    for file in os.listdir(path):
        if file.endswith('csv') and 'Report' in file:
            inv_data = file    
                
    file_name = os.path.join(path, inv_data)
    project_name, inv_col_names = pd.read_csv(file_name).columns[0].split(';')[-1].replace('"', ''), \
                                  pd.read_csv(file_name, delimiter=';', skiprows=1).columns
                                                                    # get project name
                                                                    # from data columns
    # now I read .csv file and skip first two rows
    inv = pd.read_csv(file_name, engine='python', delimiter='\;', skiprows=2)
    inv = inv.applymap(lambda x: x.replace('"', '')) # replace " from all the dataframe
    inv.columns = inv_col_names
                                                                        
    num_cols = len(inv.columns)
            
    for col in inv.columns[1:]:
        inv[col] = pd.to_numeric(inv[col], errors='coerce') # transform strings
                                                            # into numbers                                                 
    # get dates and times
    inv['Day'] = inv[inv.columns[0]].apply(lambda x: x.split()[0].split('/')[0])
    inv['Month'] = inv[inv.columns[0]].apply(lambda x: x.split()[0].split('/')[1])
    inv['Year'] = inv[inv.columns[0]].apply(lambda x: x.split()[0].split('/')[2])
    inv['Time'] = inv[inv.columns[0]].apply(lambda x: x.split()[1])
    
    # build date from Day, Month, Year and Time items from previous block
    inv['Date'] = inv['Year'] + '-' + inv['Month'] + '-' + inv['Day'] + ' ' + inv['Time']
    
    inv['Date'] = pd.to_datetime(inv['Date']) # create datetime object
    inv.set_index('Date', inplace=True) # define datetime object as index of the dataframe
    del inv[inv.columns[0]] 
    inv.drop(inv.columns[num_cols-1:], inplace=True, axis=1)
        
    start_date = inv.index.values.astype(str)[0][:16] \
                                .replace('T', '-').replace(':', 'h') # get first measurement item
    end_date = inv.index.values.astype(str)[-1][:16] \
                                .replace('T', '-').replace(':', 'h') # get last measurement item
                                
    csv_name = os.getcwd() + '\\' + project_name + '_' + start_date + '_' + end_date + '.csv'
    
    return inv