# -*- coding: utf-8 -*-
"""
Created on Sun Oct 18 23:11:43 2020

@author: Rubén Martínez Fanals
         https://www.linkedin.com/in/fanals/
         https://greenenerguy.me/
"""
import os
import pandas as pd

def read_SCB_data(SCB_data_path, timeframe):
    '''
    Parameters
    ----------
    SCB_data_path : String name indicating the relative path where the string box data is located 
                    e.g. 'SCB_Data' is the subfolder from current folder where to look for this data
    timeframe : String name indicating the folder where the string box csv data to be read is located;
                e.g. the subfolder \SCB_Data\2020_09 contains the csv files where the September string box
                data is located. timeframe refers to the string '2020_09'

    Returns
    -------
    SCB_df : Pandas Dataframe that contains the clean active power string box data from all groups of string boxes
             of the project, read in the csv file located in \SCB_data_path\timeframe, the index being day and time
    SCB_dict: A dictionary of Pandas Dataframes with the same information as SCB_df, however each dictionary
              key contains the string boxes assigned to each of the inverters of the project
             
    '''
    
    # In my specific case, the string box data are stored in the timeframe folder within several .csv files, each .csv
    # file for each of the group of string boxes assigned to each inverter; these files include the string 'SCB' in 
    # the file name
    SCB_dict = dict()
    path = os.path.join(os.getcwd(), SCB_data_path, timeframe)       
    for file in os.listdir(path):
        if 'SCB' in file:
            SCB_col_names = pd.read_csv(os.path.join(path, file), delimiter=';', skiprows=1).columns
            SCB_dict[file[11:17]] = pd.read_csv(os.path.join(path, file), engine='python', delimiter='\;', skiprows=2)
            SCB_dict[file[11:17]].columns = SCB_col_names # I am extracting the names of the string boxes to populate
                                                          # the columns in each of the keys of the SCB_dict dictionary
                                                          # the excerpt file[11:17] extracts the name of each string box
        
    for key in SCB_dict:
        SCB_dict[key] = SCB_dict[key].applymap(lambda x: x.replace('"', '')) # replace " from all the dataframe
        
        for col in SCB_dict[key].columns[1:]:
            SCB_dict[key][col] = pd.to_numeric(SCB_dict[key][col], errors='coerce') # transform strings into numbers
            
        # get dates and times    
        SCB_dict[key]['Day'] = SCB_dict[key][SCB_dict[key].columns[0]].apply(lambda x: x.split()[0].split('/')[0])
        SCB_dict[key]['Month'] = SCB_dict[key][SCB_dict[key].columns[0]].apply(lambda x: x.split()[0].split('/')[1])
        SCB_dict[key]['Year'] = SCB_dict[key][SCB_dict[key].columns[0]].apply(lambda x: x.split()[0].split('/')[2])
        SCB_dict[key]['Time'] = SCB_dict[key][SCB_dict[key].columns[0]].apply(lambda x: x.split()[1])
        SCB_dict[key]['Date'] = SCB_dict[key]['Year'] + '-' + SCB_dict[key]['Month'] + '-' + \
                                SCB_dict[key]['Day'] + ' ' + SCB_dict[key]['Time']
        SCB_dict[key]['Date'] = pd.to_datetime(SCB_dict[key]['Date']) # create datetime object
        SCB_dict[key].set_index('Date', inplace=True) # define datetime object as index of the dataframe
        SCB_dict[key] = SCB_dict[key].drop(['Day','Month','Year','Time'], axis=1) # eliminate auxiliary columns
        del SCB_dict[key][SCB_dict[key].columns[0]] # eliminate first column where I have extracted dates and times from
        
    SCB_df = pd.DataFrame(index=SCB_dict[list(SCB_dict)[0]].index) # extracts the index from the first key of SCB_dict
    for key in SCB_dict:
        SCB_df = SCB_df.merge(SCB_dict[key], left_index=True, right_index=True) # merges all string boxes into a single
                                                                                # dataframe

        
    return SCB_df, SCB_dict
