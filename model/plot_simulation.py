"""
This file was used to  temperature plots from the H-Plane file generated from the si3d model.
Usage:
Set the following parameters

h_plane_file [str  ]: The path to the H-Plane file
dx           [float]: A float representing the delta x value used during simulation. (idx from si3d_inp.txt)
"""

# Global
import os
h_plane_file = "./model/psi3d/plane_2"
dx = 200
print("Running from", os.getcwd())
print("Searching for h_plane file in", h_plane_file)

from HPlane_Si3DtoPython import HPlane_Si3dToPython
from matplotlib import pyplot as plt
from matplotlib.widgets import Slider
import numpy as np

class DynamicPlot:
    def __init__(self, on_plot, min_value, max_value, init_value, val_step, slider_name='Value'):
        """ Creates a plot with a slider that changes based on update

        Args:
            on_plot (function(ax, value)): a function that takes in a figure's axes and the slider's value,
                and plots new data
            min_value (float): a minimum value for the slider
            max_value (float): a maximum value for the slider
            init_value (float): the initial value for the slider
            val_step (float): the step size of the slider
            slider_name (str, optional): A name for the slider. Defaults to 'Value'.
        """
        self.fig, self.ax = plt.subplots()
        plt.subplots_adjust(right=0.8)
        self.ax.margins(x=0)

        self.axcolor = 'lightgoldenrodyellow'
        self.ax_slider = plt.axes([0.25, 0.05, 0.65, 0.01], facecolor=self.axcolor)
        
        self.s_value = Slider(self.ax_slider, slider_name, min_value, max_value, valinit=init_value, valstep=val_step)

        def update(val):
            self.ax.cla()
            slider_value = self.s_value.val
            on_plot(self, slider_value)
            self.fig.canvas.draw_idle()

        self.s_value.on_changed(update)
        on_plot(self, min_value)

    def show(self):
        plt.show()

h_plane = HPlane_Si3dToPython(h_plane_file, dx)
xg = h_plane['xg']
yg = h_plane['yg']
n_rows, n_cols, n_frames = h_plane['T'].shape
print(f"(row, cols, n_frames) = {(n_rows, n_cols, n_frames)}")

def on_plot(my_plot, frame):
    z = h_plane['T'][:, :, frame]
    surface_temp = my_plot.ax.pcolormesh(xg, yg, z, shading='gouraud', cmap='RdYlBu_r')
    my_plot.ax.set_aspect('equal')
    my_plot.ax.axis('off')

    my_plot.fig.suptitle(f"{h_plane['time'][frame]}")

    if hasattr(my_plot, 'cbar'):
        my_plot.cbar.remove()
    my_plot.cax = plt.axes([0.7, 0.125, 0.02, 0.75])
    my_plot.cbar = my_plot.fig.colorbar(surface_temp, cax=my_plot.cax)
    my_plot.cbar.ax.tick_params(labelsize=9)
    my_plot.ax.text(0.8, 0.5, "° Celsius", transform=my_plot.fig.transFigure)

tmp_plot = DynamicPlot(on_plot, 0, n_frames - 1, 7, 1, 'Frame #')
tmp_plot.show()