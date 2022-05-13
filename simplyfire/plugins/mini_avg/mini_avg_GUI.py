"""
mini_avg plugin - UI handling and loading
Must be loaded from the base UI system.
Use the plugin to generate average mini plots.
Minis must be analyzed using the mini_analysis plugin first.

SimplyFire - Customizable analysis of electrophysiology data
Copyright (C) 2022 Megumi Mori
This program comes with ABSOLUTELY NO WARRANTY

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

from simplyfire.utils.plugin_controller import PluginController
from simplyfire.utils.plugin_form import PluginForm
from simplyfire.utils.plugin_popup import PluginPopup
from simplyfire.utils import custom_widgets

from simplyfire import app
import tkinter as Tk
from tkinter import messagebox, ttk

import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import  FigureCanvasTkAgg

from . import mini_avg

## set module variables ##
tab_label = 'Avg'
menu_label = 'Mini Averaging'
name = 'mini_avg'

data_neg = np.zeros((1,))
data_pos = np.zeros((1,))
average_mini = None

ms_from_peak = 50

mini_groups = []
num_minis = []
group_index = 0
lines = []

## define functions ##
def _apply_setting(event=None):
    global ms_from_peak
    global average_mini
    if len(mini_groups) == 0:
        return None # nothing to initialize
    if len(mini_groups) > 0 and average_mini is not None:
        if ms_from_peak<float(form.inputs['ms_from_peak'].get()):
            if not messagebox.askyesno('Warning', f'Extending range. Values will be missing from positive and negative ends of the plot. Continue?'):
                form.inputs['ms_from_peak'].set(ms_from_peak)
                return
    try:
        ms_from_peak = float(form.inputs['ms_from_peak'].get())
        sampling_rate = app.interface.recordings[0].sampling_rate
        new_len = int(ms_from_peak * sampling_rate / 1000) * 2 - 1
        delta_len = int((new_len - average_mini.shape[0])/2)
        if delta_len > 0:
            average_mini = np.concatenate((np.zeros((len(mini_groups), delta_len,)), average_mini), axis=1)
            average_mini = np.concatenate(average_mini, (np.zeros((delta_len,))), axis=1)
            print(data_neg.shape)
        elif delta_len < 0:
            average_mini = average_mini[-delta_len:delta_len]
    except Exception as e:
        print(f'mini avg GUI apply settings: {e}')
        pass
    app.interface.focus()

def _add_data(event=None):
    if len(app.interface.recordings) == 0:
        messagebox.showerror(title='Error', message='Please open a recording file first')
        return
    data = app.plugin_manager.get_script('mini_analysis', 'mini_GUI').mini_df
    if len(data) == 0:
        messagebox.showerror(title='Error', message='No minis to average')
        return
    if len(mini_groups) == 0:
        _create_group()

    global average_mini
    global average_mini
    if average_mini is None: # first dataset
        new_len = int(ms_from_peak * app.interface.recordings[0].sampling_rate / 1000) * 2 + 1
        average_mini = np.zeros((len(mini_groups), new_len))
    elif average_mini.shape[0] < len(mini_groups): # update to match the number of groups
        average_mini = np.vstack((average_mini, np.zeros((len(mini_groups) - average_mini.shape[0],average_mini.shape[1]))))
    average_mini[group_index, :], num = mini_avg.update_aggregate(ys=app.interface.recordings[0].get_ys(),
                                          sampling_rate=app.interface.recordings[0].sampling_rate,
                                          mini_df=data,
                                          average_mini=average_mini[group_index, :]*num_minis[group_index])
    _update_plot()
    popup.show_window()

def _update_plot(event=None):
    pass
    xs = np.arange(start=-ms_from_peak/1000,
                   stop=(ms_from_peak)/1000 + 1/app.interface.recordings[0].sampling_rate,
                   step=1/app.interface.recordings[0].sampling_rate)
    global lines
    for i,l in enumerate(lines):
        if l is not None:
            l.set_ydata(average_mini[i, :])
        else:
            lines[i], = popup.ax.plot(xs, average_mini[i,:])
    popup.canvas.draw()


def _create_new():
    if len(app.interface.recordings) == 0:
        messagebox.showerror(title='Error', message='Please open a recording file first')
        return
    data = app.plugin_manager.get_script('mini_analysis', 'mini_GUI').mini_df
    if len(data) == 0:
        messagebox.showerror(title='Error', message='No minis to average')
        return

    _clear_data()
    global data_neg
    global average_mini
    global num_minis

    average_mini, num_minis = mini_avg.update_aggregate(ys=app.interface.recordings[0].get_ys(),
                                                   sampling_rate=app.interface.recordings[0].sampling_rate,
                                                   mini_df=data,
                                                   average_mini=average_mini*num_minis)
    xs = np.arange(start=-ms_from_peak/1000,
                   stop=(ms_from_peak)/1000 + 1/app.interface.recordings[0].sampling_rate,
                   step=1/app.interface.recordings[0].sampling_rate)
    popup.show_window()
    popup.ax.plot(xs, average_mini)


def _clear_data(event=None):
    global num_minis
    num_minis = []

    global ms_from_peak
    ms_from_peak = float(form.inputs['ms_from_peak'].get())
    sampling_rate = app.interface.recordings[0].sampling_rate

    global average_mini
    average_mini = None

    global mini_groups
    mini_groups = []
    form.inputs['choose_group'].clear_options()
    form.inputs['choose_group'].set('')

    global lines
    for l in lines:
        if l is not None:
            l.remove()
        del l
    lines = []
    popup.ax.clear()
    popup.canvas.draw()

    form.inputs['add_group'].set('New Group')

def _create_group(event=None):
    if len(mini_groups) == 0:
        form.inputs['choose_group'].clear_options()
    name = form.inputs['add_group'].get()
    index = len(mini_groups)
    mini_groups.append(name)
    num_minis.append(0)
    form.inputs['choose_group'].add_command(name,
                                          command=lambda c=index:_set_group(c))
    _set_group(index)
    form.inputs['add_group'].set(f'New Group {len(mini_groups)}')
    lines.append(None)

def _set_group(index):
    global group_index
    group_index = index
    form.inputs['choose_group'].set(mini_groups[group_index])





## Make GUI components ##
controller = PluginController(name=name, menu_label=menu_label)
form = PluginForm(plugin_controller=controller, tab_label=tab_label,
                  scrollbar=True, notebook=app.cp_notebook)
popup = PluginPopup(plugin_controller=controller)
## set up form GUI ##
form.insert_title(text='Mini Averaging')
form.insert_title(text='Range setting', separator=False)
form.insert_label_entry(
    name='ms_from_peak',
    text='Window to average centered around the peak (ms)',
    validate_type='float/None',
    default=ms_from_peak
)
form.inputs['ms_from_peak'].bind('<Return>', _apply_setting)
form.inputs['ms_from_peak'].bind('<FocusOut>', _apply_setting)
form.insert_button(text='Apply', command=_apply_setting)

form.insert_label_optionmenu(name='choose_group', text='Current group:',
                             options=[''],
                             default=''
                           )
form.insert_separator()

form.insert_button(text='Clear All', command=_clear_data)
form.insert_button(text='Add Data', command=_add_data)

create_frame = form.make_panel()
create_frame.grid_columnconfigure(0, weight=1)
create_frame.grid_rowconfigure(0, weight=1)
form.inputs['add_group'] = custom_widgets.VarEntry(parent=create_frame)
form.inputs['add_group'].set('New Group')
form.inputs['add_group'].grid(column=0, row=0, sticky='news')
create_button = ttk.Button(master=create_frame, text='Create Group', command=_create_group)
create_button.grid(column=1, row=0, sticky='news')

## set up graph popup ##
popup.frame = Tk.Frame(popup)
popup.frame.grid(column=0, row=0)#, sitcky='news')
popup.frame.grid_columnconfigure(0, weight=1)
popup.frame.grid_rowconfigure(1, weight=1)

popup.fig = Figure()
popup.fig.set_tight_layout(True)
popup.ax = popup.fig.add_subplot(111)
popup.fig.subplots_adjust(right=1, top=1)

popup.canvas = FigureCanvasTkAgg(popup.fig, master=popup.frame)
popup.canvas.get_tk_widget().grid(column=0, row=1, sticky='news')
popup.ax.plot()

popup.toolbar = custom_widgets.NavigationToolbar(popup.canvas, popup.frame)
popup.toolbar.grid(column=0, row=0, sticky='news')