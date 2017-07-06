"""This file is to demonstrate the use of the modules"""

# Overview
from AirTrafficDevTool.overview import Overview
view = Overview(input_file='sample.yaml', save_plots=True)
print(view.output_names())

# SSD Individual
from AirTrafficDevTool.ssd_individual import SSDi

# SSD
from AirTrafficDevTool.ssd import SSD