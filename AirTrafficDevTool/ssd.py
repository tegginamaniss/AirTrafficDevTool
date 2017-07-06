import matplotlib.patches as mpatch
import matplotlib.pyplot as plt
import numpy as np
import shapely.geometry as sg
from descartes import PolygonPatch
from AirTrafficDevTool.file import File as FileReader
from AirTrafficDevTool.ssd_individual import SSDi

KTS2MPS = 0.5144
NMI2M = 1852
HR2S = 3600
D2R = np.deg2rad(1)


class SSD:
    def __init__(self, input_file, input_folder=None, output_folder=None, show_plots=False, save_plots=None, formats=None):

        if input_folder is None:
            self.ip_folder = './Input/'
        else:
            self.ip_folder = input_folder

        if output_folder is None:
            self.folder = "./Output/"
        else:
            self.folder = output_folder

        self.input_file = self.ip_folder + input_file
        self.output_file = input_file[0:-5]
        self.show_plots = show_plots
        if save_plots is None:
            self.save_plots = True
        elif isinstance(save_plots, bool):
            self.save_plots = save_plots
        else:
            raise Exception("Paramter 'save_plots' must be a boolean")
        if formats is None:
            self.formats = ['svg']
        else:
            self.formats = formats
        self.data = None
        self.processed_data = dict()

        # Begin the script
        self.__begin()

    def __begin(self):
        # Read the input
        self.data = self.__read_input()

        # Process data
        self.__data_processing()

        # Plot settings
        self.__create_ssd()

    def __read_input(self):
        return FileReader(self.input_file, 'yaml', False).load_data()['data']

    def __data_processing(self):

        # acids = [item[0] for item in self.data]
        acids = ['MS848']

        for acid in acids:  # loop over all acids
            # find absolute own position
            for item in self.data:  # loop over all elements to identify the own data
                if item[0] != acid:  # skip if the id doesn't match
                    continue
                o_id, o_posx, o_posy, o_hdg = item[0], item[1][0], item[1][1], item[3]

            r_data = []
            # calculate translated and rotated positions
            for item in self.data:
                r_id = item[0]
                n_x = item[1][0] - o_posx
                n_y = item[1][1] - o_posy
                r_x = float("{0:.2f}".format(n_x * np.cos(np.deg2rad(o_hdg)) - n_y * np.sin(np.deg2rad(o_hdg))))
                r_y = float("{0:.2f}".format(n_x * np.sin(np.deg2rad(o_hdg)) + n_y * np.cos(np.deg2rad(o_hdg))))

                r_hdg = item[3] - o_hdg if item[3] - o_hdg >= 0 else item[3] - o_hdg + 360
                # Units conversion [acid, [M, M], MPS, R]
                r_new = [r_id, [r_x * NMI2M, r_y * NMI2M], item[2] * KTS2MPS, r_hdg * D2R]
                r_data.append(r_new)
            self.processed_data[acid] = r_data

    def __create_ssd(self):
        new = None
        for key, value in zip(self.processed_data.keys(), self.processed_data.values()):
            new = SSDi(acid=key, data=value)

if __name__=="__main__":
    ssd = SSD(input_file='sample.yaml')
