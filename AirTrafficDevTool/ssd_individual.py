import matplotlib.patches as mpatch
import matplotlib.pyplot as plt
import numpy as np
import shapely.geometry as sg
from descartes import PolygonPatch
from AirTrafficDevTool.file import File as FileReader

KTS2MPS = 0.5144
NMI2M = 1852
HR2S = 3600
D2R = np.deg2rad(1)


class SSDi:
    def __init__(self, stand_alone=False, acid=None, data=None, input_file=None, input_folder=None, output_folder=None, show_plots=False, save_plots=None, formats=None):
        if not stand_alone:
            self.o_acid = acid
            self.data = data
            self.__data_processing()
        else:
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
                raise Exception("paramter 'save_plots' must be a boolean")
            if formats is None:
                self.formats = ['svg']
            else:
                self.formats = formats
            self.data = None
            self.processed_data = []
            self.saved_names = []
            self.fig_width = None
            self.fig_height = None
            self.fig_num = None
            self.left = None
            self.bottom = None
            self.width = None
            self.height = None
            self.ov_num = None

            # Line thickness definitions
            self.markersize = 10
            self.vthin = 0.3
            self.thinline = 0.5
            self.line = 1
            self.thickline = 1.5

            # Begin the script
            self.__begin()

    def __begin(self):
        # Read the input
        self.data = self.__read_input()

        # Process data
        self.__data_processing()

        # Plot settings
        self.__plot_config()

        # Plot data
        self.__plot_overview()

    def __read_input(self):
        return FileReader(self.input_file, 'yaml', False).load_data()['data']

    def __data_processing(self):
        print(self.o_acid)
        r_data = []
        for item in self.data:
            if self.o_acid == item[0]:
                o_data = item
            else:
                r_data.append(item)
        self.calculations(o_data, r_data)

    def calculations(self, o_data, r_data):
        # Scale the velocity for the SSD diagram
        o_acid, o_px, o_py, o_vel, o_hdg = o_data[0], o_data[1][0], o_data[1][1], o_data[2], o_data[3]
        ssd_o_vel = self.__vel2radius(o_vel)

        # Calculate the velocity space
        inner = sg.Point(o_px, o_py).buffer(self.rad_i)
        outer = sg.Point(o_px, o_py).buffer(self.rad_o)
        velo_donut = outer.difference(inner)

        pdata = []
        # Calculate data for each intruder
        for item in r_data:
            n_acid = item[0]
            n_px, n_py = item[1][0], item[1][1]
            n_vel = item[2]
            n_hdg = item[3]

            n_cnf_ang = n_hdg
            if n_cnf_ang < 0:
                n_cnf_ang += 360 * D2R

            self.myfunc(o_data, item)

            ssd_n_vel = self.__vel2radius(n_vel)

            ssd_nv_x = ssd_n_vel * np.sin(n_cnf_ang)
            ssd_nv_y = ssd_n_vel * np.cos(n_cnf_ang)

            n_px_rel = n_px / NMI2M + ssd_nv_x
            n_py_rel = n_py / NMI2M + ssd_nv_y

            # calculate FBZ properties
            distance, leg_length, [leg1, leg2] = self.__calculate_ssd_legs([n_px_rel, n_py_rel], [ssd_nv_x, ssd_nv_y])

            # Infer traffic data severity
            o_vx, o_vy = o_vel * np.sin(o_hdg), o_vel * np.cos(o_hdg)
            n_vx, n_vy = n_vel * np.sin(n_hdg), n_vel * np.cos(n_hdg)
            n_tcpa, n_dcpa, n_tlos, ssd_fc, ssd_ec, p_level = self.__calc_severity([o_px, o_py, o_vx, o_vy],
                                                                                   [n_px, n_py, n_vx, n_vy])
            # create fbz
            fbz = self.__create_fbz([[ssd_nv_x, ssd_nv_y], leg1, leg2])

            # create bounded fbz
            bounded_fbz = velo_donut.intersection(fbz)

            # create ssd patch
            if self.ssd_type == 'between':
                # create SSD patch
                ssd_patch = self.__create_ssd_b_patch(bounded_fbz)

                if n_py_rel == ssd_nv_y:
                    ssd_fc = self.inf_color

                ssd_patch.set_fc(ssd_fc)
                ssd_patch.set_ec(ssd_ec)

                # elif self.ssd_type == 'within':
                print(n_tlos)
                pt1, pt2 = self.__create_w_patches(bounded_fbz, [o_px, o_py, o_vx, o_vy], [n_px, n_py, n_vx, n_vy])
                # fbz_patches = self.__create_w_patches(bounded_fbz, [o_px, o_py, o_vx, o_vy], [n_px, n_py, n_vx, n_vy])
                # create SSD patch
                # ssd_patch = self.__create_ssd_w_patch(velo_donut, fbz)
            else:
                raise Exception("Only 2 types available")

            pdata.append([item, ssd_patch, n_tcpa, n_dcpa, n_tlos, p_level, [n_px_rel, n_py_rel], [pt1, pt2]])

        # Find the level of priority
        # plot_data = self.find_priority(pdata)
        self.imaging(o_data, pdata, velo_donut, ssd_o_vel)



    def __plot_config(self):
        pass

    def __plot_overview(self):
        pass

    def output_data(self):
        pass

if __name__=="__main__":
    ssd = SSDi(input_file='sample.yaml', stand_alone=True)
