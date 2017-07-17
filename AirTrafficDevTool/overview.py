import matplotlib.patches as mpatch
import matplotlib.pyplot as plt
import numpy as np
import shapely.geometry as sg
from descartes import PolygonPatch
from AirTrafficDevTool.file import File as FileReader
import os

KTS2MPS = 0.5144
NMI2M = 1852
HR2S = 3600
D2R = np.deg2rad(1)


class Overview:
    def __init__(self, input_file, input_folder=None, output_folder=None, show_plots=False, save_plots=None, formats=None):

        if input_folder is None:
            self.ip_folder = './Input/'
        else:
            self.ip_folder = input_folder

        if output_folder is None:
            self.folder = os.path.abspath("./Output/")
        else:
            self.folder = os.path.abspath(output_folder)

        rel_path = self.ip_folder + input_file
        self.input_file = os.path.abspath(rel_path)
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
        total_steps = 4

        # Read the input
        self.data = self.__read_input()
        self.__status_bar(1, total_steps)

        # Process data
        self.__data_processing()
        self.__status_bar(2, total_steps)

        # Plot settings
        self.__plot_config()
        self.__status_bar(3, total_steps)

        # Plot data
        self.__plot_overview()
        self.__status_bar(4, total_steps)
        print("\nEnd of overview generation")

    def __read_input(self):
        return FileReader(self.input_file, 'yaml', False).load_data()['data']

    def __data_processing(self):
        # Get the x and y limits of the plot
        lx, rx, by, ty = self.__find_plot_limits()

        # Create the North symbol patch
        north_patch, north_bx, north_by = self.__create_north_patch(lx, rx, ty)

        # Create the Scale patch
        scale_patch_km, scale_patch_nm = self.__create_scale_patch(lx, rx, by)

        vec_length = -0.025*(rx-lx)
        pack = []
        for items in self.data:
            acid = items[0]
            xpos = items[1][0]
            ypos = items[1][1]
            vel = items[2]
            hdg = items[3]

            xpos_m = xpos * NMI2M
            ypos_m = ypos * NMI2M
            hdg_rad = hdg * D2R

            # Information inside text box
            text_info = acid + "\nSPD: " + str(int(vel)) + " kts\nHDG: " + str(hdg) + " \xb0"

            # Create a text box patch
            tb_patch, tbx, tby, p_dict = self.__textbox_props(xpos_m, ypos_m, hdg)

            xn, yn = self.__nearest(p_dict, xpos_m, ypos_m)

            xv = xpos_m + vec_length * np.sin(-hdg_rad)
            yv = ypos_m - vec_length * np.cos(-hdg_rad)
            pack.append([[xpos_m, ypos_m, -hdg], [tb_patch, tbx, tby, text_info, xn, yn], [xv, yv]])

        self.processed_data = [[lx, rx, by, ty], [north_patch, north_bx, north_by], [scale_patch_km, scale_patch_nm], pack]

    def __plot_config(self):
        self.fig_width = 9  # inches
        self.fig_height = self.fig_width
        self.fig_num = 0
        self.left = 400
        self.bottom = 150
        self.width = 900
        self.height = 900

    def __plot_overview(self):
        limits = self.processed_data[0]
        north_star = self.processed_data[1]
        scale_data = self.processed_data[2]
        data = self.processed_data[3]

        self.fig_num += 1
        self.ov_num = self.fig_num

        plt.figure(num=self.ov_num, figsize=(self.fig_width, self.fig_height))
        ax1 = plt.subplot(111)
        plt.gca().set_aspect('equal', adjustable='box')
        plt.get_current_fig_manager().window.setGeometry(self.left, self.bottom, self.width, self.height)

        # Start looping and plotting
        for item in data:
            # Plot the a/c symbol
            plt.plot(item[0][0], item[0][1], marker=(3, 0, item[0][2]), markersize=self.markersize, fillstyle='full', color='k')

            # Draw information text box
            ax1.add_patch(item[1][0])

            # Write information inside the box
            ax1.text(item[1][1], item[1][2], item[1][3], size=8, ha='left', va='center')

            # Draw info box to aircraft line
            plt.plot([item[0][0], item[1][4]], [item[0][1], item[1][5]], color='k', lw=self.vthin)

            # Draw velocity vector
            plt.plot([item[0][0], item[2][0]], [item[0][1], item[2][1]], color='k', lw=self.line)

        # Draw the North symbol
        ax1.add_patch(north_star[0][0])
        ax1.add_patch(north_star[0][1])
        ax1.text(north_star[1], north_star[2], 'N', size=15, ha='center', va='center')

        # Draw the scale
        ax1.add_patch(scale_data[0][0])
        ax1.text(scale_data[0][1], scale_data[0][2], scale_data[0][3], size=8, ha='center', va='center')
        ax1.add_patch(scale_data[1][0])
        ax1.text(scale_data[1][1], scale_data[1][2], scale_data[1][3], size=8, ha='center', va='center')

        plt.xlim((limits[0], limits[1]))
        plt.ylim((limits[2], limits[3]))

        # Hide ticks
        plt.xticks([])
        plt.yticks([])

        # save the plots
        if self.save_plots:
            if not self.formats:
                raise Exception("No formats specified. please specify to continue!")
            for idx, ext in enumerate(self.formats):
                fname = "AirTraffic_Overview_" + self.output_file + "." + ext
                name = self.folder + '\\' + fname
                plt.savefig(name, format=ext, dpi=600, bbox_inches='tight')
                self.saved_names.append([self.folder, fname])

        # Show the plots
        if self.show_plots:
            plt.show()

    def __create_scale_patch(self, lx, rx, by):
        pw = rx - lx
        r_big = 0.2 * pw

        width1 = 50e3
        width2 = 25*NMI2M
        height = r_big/20

        left = rx - width1 - r_big/4
        bottom = by + r_big/4

        bar_km = sg.Polygon([(left, bottom), (left+width1, bottom), (left+width1, bottom+height), (left, bottom+height), (left, bottom)])
        bar_nm = sg.Polygon([(left, bottom), (left+width2, bottom), (left+width2, bottom-height), (left, bottom-height), (left, bottom)])

        patch_km = PolygonPatch(bar_km, fc='none', ec='k', alpha=1, lw=self.thinline)
        patch_nm = PolygonPatch(bar_nm, fc='none', ec='k', alpha=1, lw=self.thinline)

        scale_x1 = left + 5e3
        scale_y1 = bottom + 2*height
        scale_t1 = '50 km'
        scale_x2 = left + 5e3
        scale_y2 = bottom - 2*height
        scale_t2 = '25 nm'
        return [patch_km, scale_x1, scale_y1, scale_t1], [patch_nm, scale_x2, scale_y2, scale_t2]

    def __create_north_patch(self, lx, rx, ty):
        pw = rx - lx
        r_big = 0.07 * pw
        r = r_big / 2
        nx = rx - 0.8 * r_big
        ny = ty - 1.3 * r_big
        coef1 = 1.5
        coef2 = 0.5

        lb = [(nx, ny + coef2 * r), (nx, ny + coef1 * r), (nx - coef2 * r, ny), (nx, ny + coef2 * r)]
        rb = [(nx, ny + coef2 * r), (nx + coef2 * r, ny), (nx, ny + coef1 * r), (nx, ny + coef2 * r)]

        # Creating boundary path left and right
        bpl = PolygonPatch(sg.Polygon(lb), fc='none', ec='k', alpha=1, lw=self.thinline)
        bpr = PolygonPatch(sg.Polygon(rb), fc='k', ec='k', alpha=1, lw=self.thinline)
        north_patch = [bpl, bpr]

        tbx = nx
        tby = ny - coef2 * r
        return north_patch, tbx, tby

    def __textbox_props(self, xpos, ypos, trk):
        tb_dist = 9 * NMI2M
        width = 24e3
        height = 13e3

        tb_ang = -(trk - 90) * np.pi / 180
        tbcx = xpos - tb_dist * np.cos(tb_ang)
        tbcy = ypos - tb_dist * np.sin(tb_ang)

        lx = tbcx - width / 2
        by = tbcy - height / 2
        rx = lx + width
        ty = by + height
        tbx = lx + 500
        tby = 0.5 * (by + ty)
        tb_patch = mpatch.Rectangle((lx, by), width, height, fill=False, lw=self.thinline)
        p_dict = dict(
            p0=np.array([lx, by]),
            p1=np.array([lx, ty]),
            p2=np.array([rx, by]),
            p3=np.array([rx, ty]),
        )
        return tb_patch, tbx, tby, p_dict

    def __find_plot_limits(self):
        x = []
        y = []

        for items in self.data:
            x.append(items[1][0] * NMI2M)
            y.append(items[1][1] * NMI2M)

        offset = 15 * NMI2M
        lx = min(x) - offset
        rx = max(x) + offset
        xdiff = rx - lx
        by = min(y) - offset
        ty = max(y) + offset
        ydiff = ty - by

        if xdiff < ydiff:
            lx = (lx + rx - ydiff) / 2
            rx = lx + ydiff
        return lx, rx, by, ty

    @staticmethod
    def __nearest(p_dict, x, y):
        """find nearest corner
        """
        pts = p_dict.keys()
        ac = np.array([x, y])
        dist = []
        for pt in pts:
            dist.append(np.linalg.norm(ac - p_dict[pt]))
        pmin = dist.index(min(dist))
        minx = p_dict['p' + str(pmin)][0]
        miny = p_dict['p' + str(pmin)][1]
        return minx, miny

    def output_names(self):
        return self.saved_names

    @staticmethod
    def __status_bar(i, steps):
        import sys
        perc = i / steps * 100
        sys.stdout.write('\r')
        # the exact output you're looking for:
        length = 50
        comman = "sys.stdout.write('Progress\t: [%-" + str(length) + "s] %d%%' % ('='*" + str(
            int(perc * length / 100)) + ", " + str(perc) + "))"
        exec(comman)
        sys.stdout.flush()

if __name__ == "__main__":
    view = Overview(input_file='sample.yaml', formats=['svg', 'png'])
