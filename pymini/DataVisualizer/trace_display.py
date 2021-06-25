import tkinter as Tk
from config import config
import matplotlib as mpl
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from utils import trace, analysis
import matplotlib.colors
import pymini
import os
import gc
import time
import datetime
import numpy as np

from DataVisualizer import data_display

def load(parent):
    frame = Tk.Frame(parent)
    fig = Figure()
    fig.set_tight_layout(True)

    global ax
    ax = fig.add_subplot(111)
    fig.subplots_adjust(right=1, top=1)

    global canvas
    canvas = FigureCanvasTkAgg(fig, master=frame)
    canvas.get_tk_widget().pack(side=Tk.TOP, fill=Tk.BOTH, expand=1)
    ax.plot()

    ax.set_xlabel('Time (n/a)')
    ax.set_ylabel('y (n/a)')

    global default_xlim
    default_xlim = ax.get_xlim()

    global default_ylim
    default_ylim = ax.get_ylim()

    #connect

    return frame

def scroll(axis, dir=1, percent=0):
    if axis == "x":
        win_lim = ax.get_xlim()
    elif axis == "y":
        win_lim = ax.get_ylim()

    else:
        return None
    width = win_lim[1] - win_lim[0]
    delta = width * percent / 100
    new_lim = (win_lim[0] + delta * dir, win_lim[1] + delta * dir)

    if axis == "x":
        ax.set_xlim(new_lim)
    else:
        ax.set_ylim(new_lim)
    canvas.draw()

    """
    need to link this to the scrollbar once the trace is opened
    """

def zoom(axis, dir=1, percent=0, event=None):
    """
    zooms in/out of the axes by percentage specified in config
    :param axis: 'x' for x-axis, 'y' for y-axis. currently does not support both
    :param dir: 1 to zoom in , -1 to zoom out
    :param event:
    :return:
    """
    if axis == 'x':
        win_lim = ax.get_xlim()
    elif axis == 'y':
        win_lim = ax.get_ylim()
    else:
        return None

    delta = (win_lim[1] - win_lim[0]) * percent * dir / 100
    center_pos = 0.5
    try:
        if axis == 'x':
            center_pos = (event.xdata - win_lim[0]) / (win_lim[1] - win_lim[0])
        elif axis == 'y':
            center_pos = (event.ydata - win_lim[0]) / (win_lim[1] - win_lim[0])
    except:
        center_pos = 0.5

    new_lim = (win_lim[0] + (1 - center_pos) * delta, win_lim[1] - (center_pos) * delta)

    if axis == 'x':
        ax.set_xlim(new_lim)
        """
        need to compare against plot area (xlim of trace) once trace is loaded
        """
    else:
        ax.set_ylim(new_lim)
    canvas.draw()

    """
    need to link this to the scrollbar once a trace is opened
    """
# def get_axis_limits(axis='x'):
#     if axis == 'x':
#         return ax.get_xlim()
#     elif axis == 'y':
#         return ax.get_ylim()
#     return None

get_axis_limits = lambda axis:getattr(ax, 'get_{}lim'.format(axis))()


set_axis_limit = lambda axis, lim:getattr(ax, 'set_{}lim'.format(axis))([
        float(e) if e!= 'auto' else globals()['default_{}lim',format(axis)][i]
        for i, e in enumerate(lim)
    ])



class InteractivePlot():
    def __init__(self, parent):

        self.fig = Figure()
        self.fig.set_tight_layout(True)

        self.ax = self.fig.add_subplot(111)
        self.fig.subplots_adjust(right=1, top=1)
        self.canvas = FigureCanvasTkAgg(self.fig, master=parent)
        self.canvas.get_tk_widget().pack(side=Tk.TOP, fill=Tk.BOTH, expand=1)
        self.ax.plot()

        self.labels = {'x': 'Time (n/a)',
                      'y': 'y (n/a)'}
        self.ax.set_xlabel(self.labels['x'])
        self.ax.set_ylabel(self.labels['y'])
        self.default_xlim = self.ax.get_xlim()
        self.default_ylim = self.ax.get_ylim()

        #initialize cid
        self.canvas.mpl_connect('key_press_event', self._on_key)
        self.canvas.mpl_connect('button_press_event', self._on_mouse_press)
        self.canvas.mpl_connect('motion_notify_event', self._on_mouse_move)
        self.canvas.mpl_connect('button_release_event', self._on_mouse_release)

        self.trace = None # take this off later once the event finding is completed and can be handled in try/except

        self.markers = {}
        self.temp = []

    ##################################################
    #                 User Interface                 #
    ##################################################

    def _on_key(self, e):
        """
        Keyboard key press event
        :param e:
        :return:
        """
        print(e)

    def _on_mouse_press(self, e):
        print('click')
        self.focus()
        self.press = True
        if self.canvas.toolbar.mode == "":
            # pymini.data_table.add_event({
            #     't':e.xdata
            # })
            pass

    def _on_mouse_release(self, e):
        self.press = False
        if pymini.get_value('trace_mode') == 'continuous' and self.trace is not None: # remove the None case later, when the finder is completed
            try:
                if self.drag:
                    self.drag = False
                    return None
            except:
                pass
            print('click!')
            self._find_event_manual(e.xdata)
    def _on_mouse_move(self, e):
        try:
            if self.press:
                self.drag = True
        except:
            pass

    ##################################################
    #                    Analysis                    #
    ##################################################
    def _find_event_manual(self, x):
        print('find event manual')
        # xs = np.array(self.ax.lines[0].get_xdata())
        # ys = np.array(self.ax.lines[0].get_ydata())
        # x_idx = search_index(x, xs, self.trace.sampling_rate)  # should be the only line on the plot
        # dir = 1
        # if pymini.get_value('detector_direction') == "negative":
        #     dir = -1
        # # switcher implementation:
        # # switch = {
        # #     'positive': np.array(self.ax.lines[0].get_ydata())
        # #     'negative': np.array(self.ax.lines[0].get_ydata)) * -1
        # # }
        # # ys = switch.get(pymini.get_value('detector_points_search', None))
        # # need to limit per window
        # xlim = self.ax.get_xlim()
        # xlim_idx = (
        #     search_index(xlim[0], xs, self.trace.sampling_rate),
        #     search_index(xlim[1], xs, self.trace.sampling_rate)
        # )
        #
        # #narrow range by xlim
        # start_idx = max(x_idx - int(int(pymini.get_value('detector_points_search'))/2), xlim_idx[0])
        # end_idx = min(x_idx + int(int(pymini.get_value('detector_points_search'))/2), xlim_idx[1])
        #
        # # narrow range by ylim
        # ylim = self.ax.get_ylim()
        # print(ys[xlim_idx[0]:xlim_idx[1]] > ylim[1])
        # print(ys[xlim_idx[0]:xlim_idx[1] < ylim[0]])
        #
        # a = ys[xlim_idx[0]:xlim_idx[1]] > ylim[1]
        # b = ys[xlim_idx[0]:xlim_idx[1]] < ylim[0]
        #
        # print(a | b)
        # ylim_idx = np.where(a|b)[0] + xlim_idx[0]
        # ylim_lower, ylim_higher = None, None
        #
        # if len(ylim_idx) > 0:
        #     for i, y_idx in enumerate(ylim_idx):
        #         ylim_lower = y_idx
        #         if y_idx > x_idx: # surpassed x
        #             ylim_higher = y_idx
        #             ylim_lower = ylim_idx[i - 1] # if there was one before, that is on the left of x
        #             if ylim_lower > ylim_higher:
        #                 ylim_lower = None
        #             break
        #     if ylim_higher is None:
        #         ylim_lower = ylim_idx[-1]
        #
        # if ylim_lower:
        #     start_idx = max(start_idx, ylim_lower)
        # if ylim_higher:
        #     end_idx = min(end_idx, ylim_higher)
        # print((ylim_lower, ylim_higher))
        # print((start_idx, end_idx))
        #
        # lag = int(pymini.get_value('detector_points_baseline'))
        # max_pt_baseline = int(pymini.get_value('detector_max_points_baseline'))
        # threshold = float(pymini.get_value('detector_min_amp'))
        # data = self._find_event(x_idx, dir, xs, ys, start_idx, end_idx, lag, max_pt_baseline, threshold)
        # try:
        #     pymini.data_table.add_event(data)
        #
        #     self._plot_markers()
        #
        #     #plot successful event
        # except Exception as e:
        #     print('_find_event_manual: {}'.format(e))
        #     #cannot be added
        #     None




    def _find_event(self, x_idx, dir, xs, ys, start_idx, end_idx, lag, max_pt_baseline, threshold):
        print('find event')

        #### FIND PEAK ####
        data = {}
        try:
            peak_y = max(ys[start_idx:end_idx] * dir)
            peaks = np.where(ys[start_idx:end_idx] * dir ==peak_y)[0] + start_idx #list of all matches
            peak_idx = peaks[0] #take the earliest time point
        except Exception as e:
            print('find event, find index of max: {}'.format(e)) #erase this if no errors are expected
            return None
        FUDGE = 10 #adjust this if needed

        # check if the peak is only a cut-off of a slope:
        # recursively narrow the search area and look for another local extremum
        if peak_idx <= start_idx + FUDGE:
            # slope going to the left edge of the search area
            return self._find_event(x_idx, dir, xs, ys, start_idx + FUDGE, end_idx, lag, max_pt_baseline, threshold)

        if peak_idx > end_idx - FUDGE:
            return self._find_event(x_idx, dir, xs, ys, start_idx, end_idx - FUDGE, lag, max_pt_baseline, threshold)
            return None
        self.ax.scatter(xs[start_idx:end_idx], ys[start_idx:end_idx])
        data['t'] = xs[peak_idx] # for the table
        data['peak_coord_x'] = xs[peak_idx]
        data['peak_coord_y'] = ys[peak_idx] # for the plot


        #### FIND START OF EVENT ####
        base_idx = peak_idx - 1
        y_avg = np.mean(ys[base_idx - lag+1:base_idx+1] * dir) # should include the base_idx in the calculation, also, why was it base_idx+2?

        while base_idx > max(start_idx - max_pt_baseline + lag, lag):
            y_avg = (y_avg * (lag) + (ys[base_idx - lag] - ys[base_idx]) * dir)/(lag) # equivalent to np.mean(ys[base_idx - lag: base_idx]))
            if y_avg > ys[base_idx] * dir:
                break
            base_idx -= 1
        else:
            print('could not find start')
            return None #could not find start

        data['start_coord_x'] = xs[base_idx]
        data['start_coord_y'] = ys[base_idx]

        data['baseline'] = y_avg #instead of the coord right at the interception
        data['baseline_unit'] = self.trace.y_unit # make sure channel in trace cannot change unexpectedly
        data['t_start'] = xs[base_idx]

        #### DETERMINE AMPLITUDE ####
        data['amp'] = (ys[peak_idx] - ys[base_idx]) # implement decay extrapolation later

        if data['amp'] * dir < threshold:
            print('event was too small: {} '.format(data['amp']))
            self.ax.scatter(xs[base_idx], ys[base_idx], marker='x', color='black')
            return None # event was too small

        data['amp_unit'] = self.trace.y_unit

        #### FIND END OF EVENT ####

        end_idx = peaks[-1]
        y_avg = np.mean(ys[end_idx: end_idx + lag]) * dir
        while end_idx < min(end_idx + max_pt_baseline - lag, len(ys) - lag):
            y_avg = (y_avg * (lag) + (ys[end_idx + lag] - ys[end_idx]) * dir) / (lag) # equivalent to np.mean(ys[end_idx + 1: end_idx + lag + 1])
            # self.ax.scatter(xs[end_idx], y_avg, c='orange')
            if y_avg > ys[end_idx] * dir:
                break
            end_idx += 1
        else:
            print('could not find end')
            return None #end could not be found

        data['end_coord_x'] = xs[end_idx]
        data['end_coord_y'] = ys[end_idx]

        data['t_end'] = xs[end_idx]

        #### CALCULATE RISE ####

        data['rise_const'] = (xs[peak_idx] - xs[start_idx])*1000
        data['rise_unit'] = 'ms' if self.trace.x_unit in ['s', 'seconds', 'second', 'sec'] else '{}/1000'.format(self.trace.x_unit)
        data['channel'] = self.trace.channel + 1 # 1-indexing

        data['datetime'] = datetime.datetime.now()
        return data




    def open_trace(self, filename):
        try:
            self.trace = trace.Trace(filename)
        except:
            return None
        #set the default save path for images
        if pymini.get_value('file_autodir'):
            mpl.rcParams['savefig.directory'] = os.path.split(filename)[0]

        if pymini.get_value('force_channel') == '1':
            try:
                self.trace.set_channel(
                    int(pymini.get_value('force_channel_id')) - 1 #1indexing
                )
            except:
                pass
        self._clear()
        data_display.clear()
        gc.collect()

        pymini.widgets['trace_info'].set(
            '{} : {}Hz : {} channel{}'.format(
                self.trace.fname,
                self.trace.sampling_rate,
                self.trace.channel_count,
                's' if self.trace.channel_count > 1 else ""
            )
        )

        xlim = None
        ylim = None

        self.plot(self.trace, xlim, ylim)

        if pymini.get_value('apply_axis_limit') == "1":
            self.set_axis_limits(
                {
                    'x': (
                        pymini.get_value('min_x'),
                        pymini.get_value('max_x')
                    ),
                    'y': (
                        pymini.get_value('min_y'),
                        pymini.get_value('max_y')
                    )

                }
            )
        pymini.get_widget('channel_option').clear_options()
        for i in range(self.trace.channel_count):
            pymini.get_widget('channel_option').add_option(
                label = "{}: {}".format(i+1, self.trace.channel_labels[i]),
                command=lambda c=i:self._choose_channel(c)
            )
        pymini.set_value('channel_option', "{}: {}".format(self.trace.channel + 1, self.trace.y_label))
        self.draw()

    def _choose_channel(self, num):
        self.trace.set_channel(num)
        pymini.set_value('channel_option', "{}: {}".format((self.trace.channel+1), self.trace.y_label))

        xlim = self.ax.get_xlim()
        self._clear()


        self.plot(self.trace, xlim)

        pass

    ##################################################
    #                      Plot                      #
    ##################################################

    def plot(self, trace, xlim=None, ylim=None):
        """
        plots data from the trace
        will first plot everything with autoscale, and save the limits as defaults.
        To avoid this behavior, make a separate function
        :param trace: Trace object
        :param xlim: desired xlim
        :param ylim: desired ylim
        :return:
        """
        # print('trace channel = {}'.format(trace.channel))
        xs = trace.get_xs()
        ys = trace.get_ys()
        self.ax.set_xlabel(
            trace.x_label
        )
        self.ax.set_ylabel(
            trace.y_label
        )
        self.ax.autoscale(enable=True, axis='x', tight=True)
        self.ax.autoscale(enable=True, axis='y', tight=True)

        self.ax.plot(
            xs,
            ys,
            linewidth=pymini.get_value('style_trace_line_width'),
            c=pymini.get_value('style_trace_line_color')
        )
        self.default_xlim = self.ax.get_xlim()
        self.default_ylim = self.ax.get_ylim()

        try:
            self.ax.set_xlim(xlim)
        except:
            pass
        try:
            self.ax.set_ylim(ylim)
        except:
            pass

        self.draw()

    def _plot_marker_temp(self, x, y, marker, c):
        self.temp.append(self.scatter(x, y, marker, c))

    def _plot_markers(self):
        self._clear_markers()
        if pymini.get_value('show_peak'):
            self.markers['peak'] = self.ax.scatter(
                x=pymini.data_table.get_column('peak_coord_x', self.trace.channel + 1),
                y=pymini.data_table.get_column('peak_coord_y', self.trace.channel + 1),
                marker='o',
                alpha=0.5,
                c=pymini.get_value('style_event_color_peak')

            )
        if pymini.get_value('show_start'):
            self.markers['start'] = self.ax.scatter(
                x=pymini.data_table.get_column('start_coord_x', self.trace.channel + 1),
                y=pymini.data_table.get_column('start_coord_y', self.trace.channel + 1),
                marker='x',
                alpha=0.5,
                c=pymini.get_value('style_event_color_start')
            )
        if pymini.get_value('show_end'):
            self.markers['start'] = self.ax.scatter(
                x=pymini.data_table.get_column('end_coord_x', self.trace.channel + 1),
                y=pymini.data_table.get_column('end_coord_y', self.trace.channel + 1),
                marker='x',
                alpha=0.5,
                c=pymini.get_value('style_event_color_end')
            )
        self.draw()


    def _clear_markers(self):
        for key in self.markers:
            self.markers[key].remove()
        for t in self.temp:
            t.remove()
        for c in self.ax.collections: # take care of the rest
            self.ax.collections.remove(c)
        self.temp=[]

    def _clear(self):
        for l in self.ax.lines:
            self.ax.lines.remove(l)
        for c in self.ax.collections:
            self.ax.collections.remove(c)
        for t in self.temp:
            t.remove()
        self.markers = {}
        self.temp = []
        self.ax.clear()
        gc.collect()
        self.draw()

    def draw(self):
        self.canvas.draw()

        pass




    def set_single_axis_limit(self, axis, idx, value):
        if idx == 0:
            self._set_ax_lim(axis, (value, self.get_axis_limits(axis)[1]))
        elif idx == 1:
            self._set_ax_lim(axis, (self.get_axis_limits(axis)[0], value))



    def get_unit(self, axis):
        try:
            return getattr(self.trace, '{}_unit'.format(axis), 'n/a')
        except:
            return 'n/a'

    def show_all_plot(self):
        self.ax.set_xlim(self.default_xlim)
        self.ax.set_ylim(self.default_ylim)
        self.draw()

    def apply_all_style(self):
        # markers should be in collections, not lines, so this shouldn't affect peaks, baselines, etc
        for l in self.ax.lines:
            l.set_color(pymini.get_value('style_trace_line_color'))
            l.set_linewidth(float(pymini.get_value('style_trace_line_width')))

        self.draw()

    def apply_style(self, key):
        try:
            if key == 'style_trace_line_width':
                for l in self.ax.lines:
                    l.set_linewidth(float(pymini.get_value('style_trace_line_width')))
            elif key == 'style_trace_line_color':
                for l in self.ax.lines:
                    l.set_color(pymini.get_value('style_trace_line_color'))
            self.draw()
            return True
        except:
            return False

    def focus(self):
        self.canvas.get_tk_widget().focus_set()







