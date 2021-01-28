# -*- coding: utf-8 -*-
"""
    Created on Fri Oct  9 22:57:47 2020

    @author: Rubén Martínez https://greenenerguy.me/
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
import sys
from Met_Data.Read_Met_Data import read_met_data as met
from SCB_Data.Read_SCB_Data import read_SCB_data as scb
from INV_Data.Read_Inv_Data import read_inv_data as inv


proj_name, timeframe = sys.argv[1], sys.argv[2]


class Availability:   
    
    def __init__(self, proj_name, timeframe):
        self.proj_name = proj_name
        self.timeframe = timeframe
        folder_list = ['Met_Data', 'SCB_Data', 'INV_Data']
        self.met_data = met(folder_list[0], timeframe)
        self.scb_data = scb(folder_list[1], timeframe)[0] # function scb returns a tuple, the first element
                                                          # being a dataframe and the second being a dictionary
                                                          # Refer to the docstring of function scb
        self.scb_dict = scb(folder_list[1], timeframe)[1]
        self.inv_data = inv(folder_list[2], timeframe)
        
        
    def availability_calc(self, scb_no_comm = [], interv_no_comm = []):
        '''

        Parameters
        ----------
        scb_no_comm : TYPE, optional
            DESCRIPTION. The default is [].
        interv_no_comm : TYPE, optional
            DESCRIPTION. The default is [].

        Returns
        -------
        None.

        '''

        # I am creating a new dataframe which index is the index from one of the three dataframes calculated
        # by the functions called when constructing the Availability instance
        self.avail_df = pd.DataFrame(index=self.met_data.index)
        
        # I am creating column 'HGPOAm'; when the average of the readings of the trhee inclined pyranometers
        # is greater than 300 W/m2, value is 1; otherwise is 0
        self.avail_df['HGPOAm'] = np.where(self.met_data[['RAD_3 [W/m2]', 'RAD_4 [W/m2]', 'RAD_5 [W/m2]']].mean(axis=1) > 300, 1, 0)
        
        # I will add two columns: the first column 'GPOAI' being the global inclined irradiation measured by the inclined
        # pyranometers (kWh/m2), and the second one 'GHI' being the global horizontal irradiation measured by the horizontal
        # pyranometers (kWh/m2)
        self.avail_df['GPOAI'] = self.met_data[['RAD_3 [W/m2]', 'RAD_4 [W/m2]', 'RAD_5 [W/m2]']].mean(axis=1) / 1000
        self.avail_df['GHI'] = self.met_data[['RAD_1 [W/m2]', 'RAD_2 [W/m2]']].mean(axis=1) / 1000
            
        # I will create a dictionary where each key contains a dataframe including the string boxes pertaining
        # to each inverter; each column will be 1 if avail_df['HGPOAm'] == 1 and if active power of that 
        # string box at this hour is greater than 5 kW
        self.avail_scb = {}
        for key in self.scb_dict:
            self.avail_scb[key] = pd.DataFrame(index=self.scb_data.index)
            for col in self.scb_dict[key].columns:
                self.avail_scb[key][col] = np.where((self.scb_dict[key][col] > 5) & (self.avail_df['HGPOAm'] == 1), 1, 0)
        
        # I will create a dataframe where each column represents one of the inverters of the project
        # Each column will be 1 if active power of the corresponding inverter at that hour is > 0 OR the data is missing,
        # AND avail_df['HGPOAm'] == 1
        self.avail_inv = pd.DataFrame(index=self.scb_data.index)
        for col in self.inv_data.columns:
            self.avail_inv['HPm-I' + str(self.inv_data.columns.get_loc(col)+1)] = \
                          np.where(((self.inv_data[col] > 0) | (self.inv_data[col].isnull())) & (self.avail_df['HGPOAm'] == 1), 1, 0)

        
        # If there is any string box without communications, this information is manually given in the variable
        # scb_no_comm, that is a list containing the elements suffering from communication problems
        # Any string box is denominated as "SCB I-N", being I the inverter number they belong to, and N a correlative
        # number for all string boxes that belong to each inverter; I will extract the I so that I can identify to which
        # inverter the string box belongs
        self.inv_no_comm = []
        for scb in scb_no_comm:
            self.inv = int(scb.split()[1].split('-')[0]) # Extract the inverter "I" from a string with structure "SCB I-N"
            self.inv_no_comm.append(self.inv)
        self.inv_no_comm = list(set(self.inv_no_comm)) # Elimination of potential duplicates with set
        
        # I want to create a new dataframe where the columns represent communication problems from the string boxes
        # belonging to each group of inverters; if there is a communication problem in a string box that belongs to
        # inverter 3, then the column that represent inverter 3 will show 1 meaning that at that time there was a 
        # communication problem
        self.cont_inv = 1
        self.inv_comms = pd.DataFrame(index=self.inv_data.index)
        for elem in self.inv_data.columns:
            if self.cont_inv in self.inv_no_comm:    
                self.inv_comms['COM-I' + str(self.cont_inv)] = np.where(self.avail_df['HGPOAm'] == 1, 1, 0)
            else:
                self.inv_comms['COM-I' + str(self.cont_inv)] = 0
            self.cont_inv += 1            
            
        # I have to limit the intervals of communication problems to those given as input in variable "interv_no_comm" 
        # when calling the method; "interv_no_comm" is a list of tuples, where each tuple has two elements, the first 
        # element being the start of the interval and the second the end of the interval
        for tup in interv_no_comm:
            interv = pd.date_range(tup[0], tup[1], freq='H')
            for col in self.inv_comms.columns:
                self.inv_comms[col] = np.where(self.inv_comms.index.isin(interv) == True, self.inv_comms[col], 0)
            # test.availability_calc(scb_no_comm=['SCB 1-06', 'SCB 5-10'], interv_no_comm=[('2020-10-01 01:00:00', '2020-10-03 19:00:00')])
        
                
        # I will create a dataframe where each column represents one of the inverters of the project,
        # and I will calculate the availability of the string boxes at inverter level. I will first check whether
        # HGPOAm is 1, in which case I will sum the availability of all string boxes pertaining to that inverter
        self.cont_scb_group = 1
        self.avail_scb_per_inv = pd.DataFrame(index=self.scb_data.index)
        for key in self.avail_scb:
            # self.avail_scb_per_inv['Am-I' + str(self.cont_scb_group)] = np.where(self.avail_df['HGPOAm'] == 1, \
            #                                                                      self.avail_scb[key].sum(axis=1), 0)
            self.avail_scb_per_inv['Am-I' + str(self.cont_scb_group)] = np.where(self.avail_df['HGPOAm'] == 1, \
                                                                           np.where(self.inv_comms['COM-I' + str(self.cont_scb_group)] == 0, \
                                                                              self.avail_scb[key].sum(axis=1), \
                                                                              self.avail_inv['HPm-I' + str(self.cont_scb_group)] * len(self.avail_scb[key].columns)), 0)
            self.cont_scb_group += 1
            
        # I have now all elements to calculate availability of the project
        # I will add a column called 'HPm' to dataframe avail_df that sums all columns of avail_scb_per_inv
        # and will divide the result by the total number of string boxes of the project
        # I will add another column called 'Am' that calculates string box availability on a hourly basis
        self.avail_df['HPm'] = self.avail_scb_per_inv.sum(axis=1) / len(self.scb_data.columns)
        self.avail_df['Am'] = self.avail_df['HPm'] / self.avail_df['HGPOAm']
        
        # I will add a column called 'HPm-I' to dataframe avail_df that sums all columns of avail_inv
        # and will divide the result by the total number of inverters of the project
        self.avail_df['HPm-I'] = self.avail_inv.sum(axis=1) / len(self.avail_inv.columns)

        # Now I can calculate availability at string box and inverter levels, as well as the 
        # irradiation gain originated by the one-axis trackers
        self.month_avail_scb = self.avail_df['HPm'].sum(axis=0) / self.avail_df['HGPOAm'].sum(axis=0)
        self.month_avail_inv = self.avail_df['HPm-I'].sum(axis=0) / self.avail_df['HGPOAm'].sum(axis=0)
        self.irr_gain = (self.avail_df['GPOAI'].sum(axis=0) - self.avail_df['GHI'].sum(axis=0)) / \
                             self.avail_df['GHI'].sum(axis=0)
        
        # Printing out the calculation results
        print("Project availability at string box level is {:.2%}".format(self.month_avail_scb))
        print("Project availability at inverter level is {:.2%}".format(self.month_avail_inv))
        print("Irradiation gain is {:.2%}".format(self.irr_gain))
        
        # Creation of another dataframe 'output_df' that combines previous most relevant data and calculations
        self.output_df = pd.DataFrame(index=self.avail_df.index)
        for key in self.avail_scb:
            self.output_df = self.output_df.merge(self.avail_scb[key], left_index=True, right_index=True)
            
        self.list_of_columns = [self.avail_df['HGPOAm'], self.avail_df['HPm'], self.avail_df['Am'],
                             self.avail_df['GPOAI'], self.avail_df['GHI'], self.avail_inv, 
                             self.avail_scb_per_inv, self.inv_comms]
        for item in self.list_of_columns:
            self.output_df = self.output_df.merge(item, left_index=True, right_index=True)
            
        # I will create an Excel workbook including all information, from raw data to availability calculations
        filename = 'Availability Calc - ' + self.proj_name + ' - ' + self.timeframe + '.xlsx'
        self.writer = pd.ExcelWriter(filename)
        self.scb_data.to_excel(self.writer, sheet_name='RAW_SCB')
        self.met_data.to_excel(self.writer, sheet_name='RAW_MET')
        self.inv_data.to_excel(self.writer, sheet_name='RAW_INV')
        self.output_df.to_excel(self.writer, sheet_name='AVA')
        self.writer.save()
            

Availability(proj_name, timeframe).availability_calc()
