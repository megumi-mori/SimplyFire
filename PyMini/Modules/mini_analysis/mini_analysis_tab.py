import matplotlib.backend_bases
from PyMini.Modules.base_control_module import BaseControlModule
from PyMini import app
from PyMini.utils import writer, widget
from . import mini_analysis
import pandas as pd
import os
from tkinter import filedialog, messagebox, ttk
import tkinter as Tk
import numpy as np
from PyMini.Backend import analyzer2

class ModuleControl(BaseControlModule):
    def __init__(self):
        super(ModuleControl, self).__init__(
            name= 'mini_analysis',
            menu_label='Mini Analysis',
            tab_label='Mini',
            parent=app.root,
            scrollbar=True,
            filename=__file__,
            has_table=True
        )

        # variable attributes
        self.changes = {}
        self.changed = False
        self.parameters = {}

        self.mini_df = pd.DataFrame(columns=['compound'])
        self.mini_df = self.mini_df.astype({'compound':bool}) # set column types as necessary

        self.saved = True # track if mini data has been saved
        self.mini_filename = ""

        # variables for plotting
        self.markers = {'peak':None, 'decay':None, 'start':None}
        self.event_pick = False

        self.peak_color = 'green'
        self.decay_color = 'blue'
        self.start_color = 'red'
        self.highlight_color = 'red'

        self.peak_size = self.values.get('style_mini_size', self.default['style_mini_size'])
        self.decay_size = 5
        self.start_size = 5
        self.highlight_size = 5

        # GUI set up
        self._load_layout() # all widget placements in GUI
        self._load_binding() # all event bindings in GUI
        self._modify_GUI() # change other GUI components


    def _apply_column_options(self, e=None):
        app.get_data_table(self.name).show_columns(
            [k for k,v in self.mini_header2config.items() if self.widgets[v].get()]
        )
    def _apply_parameters(self, e=None):
        app.interface.focus()
        for i in self.parameters:
            if self.parameters[i] != self.widgets[i].get():
                self.changes[i] = self.widgets[i].get()
                self.changed = True

    def _columns_show_all(self, e=None):
        for option in self.data_display_options:
            self.widgets[option[0]].set('1')
        self._apply_column_options()
    def _columns_hide_all(self, e=None):
        for option in self.data_display_options:
            self.widgets[option[0]].set('')
        self._apply_column_options()

    def filter_all(self, e=None):
        if self.mini_df.shape[0] == 0:
            return None
        # deal with undo later
        params = self.get_params()
        self.mini_df = mini_analysis.filter_mini(mini_df=self.mini_df, xlim=None, **params)
        self.update_event_markers()
        self.update_module_table()
        app.clear_progress_bar()
        pass

    def filter_window(self, e=None):
        if self.mini_df.shape[0] == 0:
            return None
        params=self.get_params()
        xlim = app.trace_display.ax.get_xlim()
        self.mini_df = mini_analysis.filter_mini(mini_df=self.mini_df, xlim=xlim, **params)
        self.update_event_markers()
        self.update_module_table()
        app.clear_progress_bar()
        pass

    def canvas_mouse_release(self, event: matplotlib.backend_bases.Event=None):
        if not self.has_focus():
            return None
        if self.event_pick:
            self.event_pick = False
            return None
        if event.button != 1:
            return None
        if app.trace_display.canvas.toolbar.mode != "":
            return None
        if len(app.interface.recordings) == 0:
            return None
        if self.has_focus():
            if app.menubar.widgets['trace_mode'].get() != 'continuous':
                messagebox.showerror(title='Error', message='Please switch to continuous mode to analyze minis.')
                return None
            self.module_table.unselect()
            try:
                self.find_mini_manual(event.xdata)
            except:
                pass
            pass

    def change_channel(self, event=None):
        self.module_table.set(self.extract_channel_subset())
        self.update_event_markers()
        pass

    def default_core_params(self, e=None):
        self.set_to_default('detector_core')
        self.populate_decay_algorithms()
        self.populate_compound_params()

    def delete_clear(self, undo=True):
        # deal with undo later
        # use this to clear the entire mini dataframe (all channels)
        self.mini_df = self.mini_df.iloc[0:0]
        self.module_table.clear()
        self.update_event_markers()

    def delete_all(self, undo=True):
        # deal with undo later
        # use this to clear the mini data for the current channel
        try:
            self.mini_df = self.mini_df[self.mini_df['channel']!=app.interface.channel]
        except:
            # no data yet
            pass
        self.update_event_markers()
        self.update_module_table()
    def delete_in_window(self, undo=True):
        # deal with undo later
        xlim = app.trace_display.ax.get_xlim()
        selection = self.mini_df[(self.mini_df['t'] > xlim[0]) &
                            (self.mini_df['t'] < xlim[1]) &
                            (self.mini_df['channel'] == app.interface.channel)].t.values
        self.delete_selection(selection)

    def delete_from_canvas(self, selection, undo=True):
        self.module_table.delete_selected() # make this direct within  class?


    def delete_selection(self, selection):
        # pass list of floats (corresponding to 't' column) to delete
        self.mini_df = self.mini_df[(~self.mini_df['t'].isin(selection))|(self.mini_df['channel']!=app.interface.channel)]
        self.module_table.delete(selection)
        self.update_event_markers()

    def extract_column(self, colname: str, t: list=None) -> list:
        # extract data for a specific column from the mini dataframe
        try:
            return list(self.extract_channel_subset(t)[colname])
        except:
            return None

    def extract_channel_subset(self, t: list=None) -> pd.DataFrame:
        # extract mini data from current channel
        if len(app.interface.recordings) == 0:
            return None
        if self.mini_df.shape[0] == 0:
            return None
        if t:
            return self.mini_df[(self.mini_df['t'].isin(t)) & (self.mini_df['channel'] == app.interface.channel)]
        else:
            return self.mini_df[self.mini_df['channel'] == app.interface.channel]

    def find_mini_manual(self, x):
        if x is None:
            return None
        self.module_table.unselect()
        xlim = app.trace_display.ax.get_xlim()
        r = (xlim[1] - xlim[0]) * float(self.widgets['detector_core_search_radius'].get()) / 100

        self.find_mini_at(max(x-r, xlim[0]), min(x+r,xlim[1]))

    def find_mini_at(self, x1, x2):
        """
        calls mini analysis algorithm centered around x, with
        """
        # convert % x-axis to points search using sampling rate?

        xs = app.trace_display.ax.lines[0].get_xdata()
        ys = app.trace_display.ax.lines[0].get_ydata()
        params = self.get_params()

        mini = app.interface.al.find_mini_manual(xlim=(x1, x2), xs=xs, ys=ys,
                                                 x_sigdig=app.interface.recordings[0].x_sigdig,
                                                 sampling_rate=app.interface.recordings[0].sampling_rate,
                                                 channel=app.interface.recordings[0].channel,
                                                 reference_df=self.mini_df, y_unit=app.interface.recordings[0].y_unit,
                                                 x_unit=app.interface.recordings[0].x_unit, **params)
        if mini['success']:
            self.mini_df = self.mini_df.append(mini,
                                               ignore_index=True,
                                               sort=False)
            self.mini_df = self.mini_df.sort_values(by='t')
            self.module_table.add({key: value for key, value in mini.items() if key in self.mini_header2config})
            self.update_event_markers()
            self.saved = False  # track change
    def find_mini_all(self, event=None):
        self.module_table.unselect()
        try:
            xs = app.trace_display.ax.lines[0].get_xdata()
            ys = app.trace_display.ax.lines[0].get_ydata()
        except: # no traces yet
            return
        params = self.get_params()
        df = app.interface.al.find_mini_auto(xlim=None, xs=xs, ys=ys, x_sigdig=app.interface.recordings[0].x_sigdig,
                               sampling_rate=app.interface.recordings[0].sampling_rate, channel=app.interface.recordings[0].channel,
                      reference_df=self.mini_df, y_unit=app.interface.recordings[0].y_unit,
                               x_unit=app.interface.recordings[0].x_unit, progress_bar=app.pb, **params)

        self.mini_df = pd.concat([self.mini_df, df])
        if df.shape[0] > 0:
            # if int(app.widgets['config_undo_stack'].get()) > 0:
            #     add_undo([
            #         lambda iid=df['t'].values, u=False: delete_event(iid, undo=u),
            #         lambda msg='Undo mini search': detector_tab.log(msg)
            #     ])
            self.update_event_markers()
            self.module_table.append(df)
            self.saved = False # track change

        # if detector_tab.changed:
        #     log_display.search_update('Auto')
        #     log_display.param_update(detector_tab.changes)
        #     detector_tab.changes = {}
        #     detector_tab.changed = False
        app.clear_progress_bar()

    def find_mini_range(self, event=None):
        self.module_table.unselect()
        try:
            xs = app.trace_display.ax.lines[0].get_xdata()
            ys = app.trace_display.ax.lines[0].get_ydata()
        except:  # no traces yet
            return
        params = self.get_params()
        df = app.interface.al.find_mini_auto(xlim=app.trace_display.ax.get_xlim(), xs=xs, ys=ys, x_sigdig=app.interface.recordings[0].x_sigdig,
                                             sampling_rate=app.interface.recordings[0].sampling_rate,
                                             channel=app.interface.recordings[0].channel,
                                             reference_df=self.mini_df, y_unit=app.interface.recordings[0].y_unit,
                                             x_unit=app.interface.recordings[0].x_unit, progress_bar=app.pb, **params)

        self.mini_df = pd.concat([self.mini_df, df])
        if df.shape[0] > 0:
            # if int(app.widgets['config_undo_stack'].get()) > 0:
            #     add_undo([
            #         lambda iid=df['t'].values, u=False: delete_event(iid, undo=u),
            #         lambda msg='Undo mini search': detector_tab.log(msg)
            #     ])
            self.update_event_markers()
            self.module_table.append(df)
        app.clear_progress_bar()

    def get_params(self):
        params = {}
        params['direction'] = {'negative': -1, 'positive': 1}[
            self.widgets['detector_core_direction'].get()]  # convert direction to int value
        params['compound'] = self.widgets['detector_core_compound'].get() == '1'
        params['decay_algorithm'] = self.widgets['detector_core_decay_algorithm'].get()

        for k, d in self.core_params.items():
            try:
                params[k] = d['conversion'](self.widgets[d['id']].get())
            except:
                if self.widgets[d['id']].get() == 'None':
                    params[k] = None
                else:
                    params[k] = self.widgets[d['id']].get()
        for k, d in self.filter_params.items():
            try:
                params[k] = d['conversion'](self.widgets[d['id']].get())
            except:
                if self.widgets[d['id']].get() == 'None' or self.widgets[d['id']].get() == '':
                    params[k] = None
                else:
                    params[k] = self.widgets[d['id']].get()
        for k, d in self.decay_params.items():
            try:
                params[k] = d['conversion'](self.widgets[d['id']].get())
            except:
                if self.widgets[d['id']].get() == 'None':
                    params[k] = None
                else:
                    params[k] = self.widgets[d['id']].get()
        if params['compound']:
            for k, d in self.compound_params.items():
                params[k] = self.widgets[d['id']].get()
        return params

    def populate_decay_algorithms(self, e=None):
        algorithm = self.widgets['detector_core_decay_algorithm'].get()
        for k, d in self.decay_params.items():
            if algorithm in d['algorithm']:
                self.show_label_widget(self.widgets[d['id']])
            else:
                self.hide_label_widget(self.widgets[d['id']])
        self.record_param_change('decay algorithm', algorithm)

    def populate_compound_params(self, e=None):
        state = self.widgets['detector_core_compound'].get()
        if state:
            for k,d in self.compound_params.items():
                self.show_label_widget(self.widgets[d['id']])
        else:
            for k,d in self.compound_params.items():
                self.hide_label_widget(self.widgets[d['id']])

    def plot_peak(self, xs, ys):
        try:
            self.markers['peak'].remove()
        except:
            pass
        try:
            self.markers['peak'] = app.trace_display.ax.scatter(xs, ys, marker='o', color=self.peak_color,
                                                            s=self.peak_size**2, picker=True, animated=False)
        except:
            pass

    def plot_decay(self, xs, ys):
        try:
            self.markers['decay'].remove()
        except:
            pass
        try:
            self.markers['decay'], = app.trace_display.ax.plot(xs, ys, marker='x', color=self.decay_color,
                                                          markersize=self.decay_size, linestyle='None',
                                                          animated=False)
        except:
            pass

    def plot_highlight(self, xs, ys):
        try:
            self.markers['highlight'].remove()
        except Exception as e:
            print(e)
            pass
        try:
            self.markers['highlight'], = app.trace_display.ax.plot(xs, ys, marker='o', c=self.highlight_color,
                                                                   markersize=self.highlight_size, linestyle='None',
                                                                   animated=False, alpha=0.5)
        except Exception as e:
            print(e)
            pass
        if xs is None:
            print(self.markers['highlight'].get_xdata())
    def plot_start(self, xs, ys):
        try:
            self.markers['start'].remove()
        except:
            pass
        try:
            self.markers['start'], = app.trace_display.ax.plot(xs, ys, marker='x', color=self.start_color,
                                                          markersize=self.start_size, linestyle='None',
                                                          animated=False)
        except:
            pass

    def record_param_change(self, pname, pvalue):
        self.changed = True
        self.changes[pname] = pvalue

    def report_results(self):
        if len(app.interface.recordings) == 0:
            messagebox.showerror('Error', 'Please open a recording file first')
            return None
        if self.mini_df.shape[0] == 0:
            app.results_display.report({
                'filename': app.interface.recordings[0].filename,
                'analysis': 'mini',
                'num_minis': 0,
                'channel': app.interface.recordings.channel
            })
            return None
        mini_df = self.mini_df[self.mini_df['channel'] == app.interface.channel]
        if mini_df.shape[0] == 0:
            app.results_display.report({
                'filename': app.interface.recordings[0].filename,
                'analysis': 'mini',
                'num_minis': 0,
                'channel': app.interface.recordings.channel
            })
            return None
        data = {
            'filename': app.interface.recordings[0].filename,
            'analysis': 'mini',
            'num_minis': mini_df.shape[0]
        }
        if 'amp' in self.module_table.columns:
            data['amp'] = mini_df['amp'].mean()
            data['amp_unit'] = mini_df['amp_unit'].iloc[0]
            data['amp_std'] = mini_df['amp'].std()
        if 'decay_const' in self.module_table.columns:
            data['decay_const'] = mini_df['decay_const'].mean()
            data['decay_unit'] = mini_df['decay_unit'].iloc[0]
            data['decay_std'] = mini_df['decay_const'].std()
        if 'rise_const' in self.module_table.columns:
            data['rise_const'] = mini_df['rise_const'].mean()
            data['rise_unit'] = mini_df['rise_unit'].iloc[0]
            data['decay_std'] = mini_df['rise_const'].std()
        if 'halfwidth' in self.module_table.columns:
            data['halfwidth'] = mini_df['halfwidth'].mean()
            data['halfwidth_unit'] = mini_df['halfwidth_unit'].iloc[0]
            data['halfwidth_std'] = mini_df['halfwidth'].std()
        if 'baseline' in self.module_table.columns:
            data['baseline'] = mini_df['baseline'].mean()
            data['baseline_unit'] = mini_df['baseline_unit'].iloc[0]
            data['baseline_std'] = mini_df['baseline'].std()
        if 'channel' in self.module_table.columns:
            data['channel'] = app.interface.recordings[0].channel
        if 'compound' in self.module_table.columns:
            data['num_compound'] = mini_df['compound'].sum()
        # calculate frequency
        data['Hz'] = mini_df.shape[0]/(mini_df['t'].max() - mini_df['t'].min())

        app.results_display.report(data)
    def save_minis(self, filename, overwrite=True):
        if overwrite:
            mode = 'w'
        else:
            mode = 'x'
        filename = writer.format_save_filename(filename, overwrite)
        with open(filename, mode) as f:
            f.write(f'@filename: {app.interface.recordings[0].filename}\n')
            f.write(f'@version: {app.config.version}\n')
            f.write(self.mini_df.to_csv(index=False))
        self.saved = True
        app.clear_progress_bar()

    def save_minis_dialogue(self, event=None):
        if len(app.interface.recordings) == 0:
            messagebox.showerror('Error', 'Please open a recording file first')
            return None
        if self.mini_df.shape[0] == 0:
            if not messagebox.askyesno('Warning', 'No minis to save. Proceed?'):
                return None
        if not self.mini_filename:
            initialfilename = os.path.splitext(app.interface.recordings[0].filename)[0]

        filename = filedialog.asksaveasfilename(filetypes=[('mini file', '*.mini'),('csv file', '*.csv'), ('All files', '*.*')],
                                     defaultextension='.mini',
                                     initialfile=initialfilename)
        if not filename:
            return None
        try:
            self.save_minis(filename, overwrite=True)
            self.saved = True
            return filename
        except Exception as e:
            messagebox.showerror('Error', f'Could not write data to file.\n Error: {e}')
            return None

    def export_minis_dialogue(self, event=None):
        if len(app.interface.recordings) == 0:
            messagebox.showerror('Error', 'Please open a recording file first')
            return None
        if self.mini_df.shape[0] == 0:
            if not messagebox.askyesno('Warning', 'No minis to export. Proceed?'):
                return None
        if not self.mini_filename:
            initialfilename = os.path.splitext(app.interface.recordings[0].filename)[0]+self.name

        filename = filedialog.asksaveasfilename(filetypes=[('csv file', '*.csv')],
                                     defaultextension='.csv',
                                     initialfile=initialfilename)
        if not filename:
            return None
        try:
            self.module_table.export(filename, mode='w')
            app.clear_progress_bar()
            return filename
        except Exception as e:
            messagebox.showerror('Error', f'Could not write data to file.\n Error: {e}')
            app.clear_progress_bar()
            return None

    def open_minis(self, filename):
        if len(app.interface.recordings) == 0:
            messagebox.showerror('Error', 'Please open a recording file first')
            return None
        # handle undo later
        filetype = os.path.splitext(filename)[1]
        if filetype not in ('.mini','.csv','.temp','.minipy'):
            if not messagebox.askyesno('Warning', f'{filetype} is not a recognized filetype. The file may not be read properly. Proceed?'):
                return
        filetype = os.path.splitext(filename)[1]
        if filetype in ('.csv', '.temp', '.event', '.mini'):
            df = self.open_mini_csv(filename)
        elif filetype == '.minipy':
            df = self.open_minipy(filename)
        df = df.replace({np.nan: None})

        self.mini_df = df

        self.update_module_table()
        self.update_event_markers()

        self.saved = True
        app.clear_progress_bar()

    def open_mini_csv(self,filename):
        df = pd.read_csv(filename, comment='@')
        return df

    def open_minipy(self,filename):
        """
        open mini files from Minipy (ancestral version)
        """
        channel = 0
        minis = []
        header_idx = {}
        with open(filename, 'r') as f:
            lines = f.readlines()
            for l in lines:
                info = l.strip().split(',')
                if info[0] == "@Trace":
                    recording_filename = info[1]
                elif info[0] == '@Channel':
                    channel = int(info[1])
                elif info[0] == '@Header':
                    for i, h in enumerate(info):
                        header_idx[h] = i
                    xs = app.interface.recordings[0].get_xs(mode='continuous', channel=channel)
                    ys = app.interface.recordings[0].get_ys(mode='continuous', channel=channel)
                elif info[0] == '@Data':
                    mini = {
                        't': float(info[header_idx['x']]),
                        'peak_coord_x': float(info[header_idx['x']]),
                        'peak_coord_y': float(info[header_idx['y']]),
                        'amp': float(info[header_idx['Vmax']]) * float(info[header_idx['direction']]),
                        'baseline': float(info[header_idx['baseline']]),
                        'compound': False,
                        'decay_A': float(info[header_idx['Vmax']]),
                        'decay_const': float(info[header_idx['tau']]) * 1000,
                        'decay_baseline': 0,
                        'decay_coord_x': float(info[header_idx['tau_x']]),
                        'decay_coord_y': float(info[header_idx['tau_y']]),
                        'decay_max_points': int(
                            float(app.widgets['detector_core_decay_max_interval'].get()) / 1000 * app.interface.recordings[
                                0].sampling_rate),
                        'failure': None,
                        'lag': int(info[header_idx['lag']]),
                        'rise_const': float(info[header_idx['rise_time']]) * 1000,
                        'start_coord_x': float(info[header_idx['left_x']]),
                        'start_coord_y': float(info[header_idx['left_y']]),
                        'amp_unit': app.interface.recordings[0].channel_units[channel],
                        'baseline_unit': app.interface.recordings[0].channel_units[channel],
                        'decay_unit': 'ms',
                        'halfwidth_unit': 'ms',
                        'rise_unit': 'ms',
                        'channel': channel,
                        'delta_x': 0,
                        'direction': int(info[header_idx['direction']]),
                        'end_coord_x': float(info[header_idx['right_x']]),
                        'end_coord_y': float(info[header_idx['right_y']]),
                        'max_amp': np.inf,
                        'min_amp': 0.0,
                        'max_rise': np.inf,
                        'min_rise': 0.0,
                        'max_decay': np.inf,
                        'min_decay': 0.0,
                        'max_hw': np.inf,
                        'min_hw': 0.0,
                        'max_s2n': np.inf,
                        'min_s2n': 0.0,
                        'stdev_unit': app.interface.recordings[0].channel_units[channel],
                        'success': True,
                    }
                    pass
                    mini['start_idx'] = int(analyzer2.search_index(mini['start_coord_x'], xs,
                                                                   rate=app.interface.recordings[0].sampling_rate))
                    mini['baseline_idx'] = mini['start_idx']
                    mini['base_idx_L'] = mini['start_idx'] - mini['lag']
                    mini['base_idx_R'] = mini['start_idx']
                    mini['decay_idx'] = int(analyzer2.search_index(mini['start_coord_x'] + mini['decay_const'], xs,
                                                                   rate=app.interface.recordings[0].sampling_rate))
                    mini['peak_idx'] = int(analyzer2.search_index(mini['peak_coord_x'], xs,
                                                                  rate=app.interface.recordings[0].sampling_rate))
                    mini['decay_start_idx'] = mini['peak_idx']
                    mini['end_idx'] = analyzer2.search_index(mini['end_coord_x'], xs,
                                                             rate=app.interface.recordings[0].sampling_rate)
                    mini['stdev'] = np.std(ys[mini['base_idx_L']:mini['base_idx_R']])

                    # try finding halfwidth
                    hw_start_idx, hw_end_idx = app.interface.al.find_mini_halfwidth(amp=mini['amp'],
                                                                                    xs=xs[mini['baseline_idx']:mini[
                                                                                        'end_idx']],
                                                                                    ys=ys[mini['baseline_idx']:mini[
                                                                                        'end_idx']],
                                                                                    peak_idx=mini['peak_idx'] - mini[
                                                                                        'baseline_idx'],
                                                                                    baseline=mini['baseline'],
                                                                                    direction=mini['direction'])
                    if hw_start_idx is not None and hw_end_idx is None:
                        if app.widgets['detector_core_extrapolate_hw'].get():
                            t = np.log(0.5) * (-1) * mini['decay_const'] / 1000
                            hw_end_idx = analyzer2.search_index(xs[mini['peak_idx']] + t, xs[mini['baseline_idx']:],
                                                                app.interface.recordings[0].sampling_rate)
                    if hw_start_idx is None or hw_end_idx is None:
                        mini['halfwidth'] = 0  # could not be calculated
                    else:
                        mini['halfwidth_start_idx'] = hw_start_idx + mini['baseline_idx']
                        mini['halfwidth_end_idx'] = hw_end_idx + mini['baseline_idx']
                        mini['halfwidth'] = (xs[int(mini['halfwidth_end_idx'])] - xs[
                            int(mini['halfwidth_start_idx'])]) * 1000
                        mini['halfwidth_start_coord_x'] = xs[mini['halfwidth_start_idx']]
                        mini['halfwidth_end_coord_x'] = xs[mini['halfwidth_end_idx']]
                        mini['halfwidth_start_coord_y'] = mini['halfwidth_end_coord_y'] = mini['baseline'] + 0.5 * mini[
                            'amp']

                    minis.append(mini)
            if len(minis) > 0:
                df = pd.DataFrame.from_dict(minis)
                return df
            return pd.DataFrame()  # empty

    def open_minis_dialogue(self, event=None):
        if not self.saved and self.mini_df.shape[0]>0:
            choice = messagebox.askyesnocancel('Warning', 'Save mini data?')
            if choice is None:
                return
            if choice:
                self.save_minis_dialogue()

        if len(app.interface.recordings) == 0:
            messagebox.showerror('Error', 'Please open a recording file first')
            return None
        filename = filedialog.askopenfilename(filetype=[('mini data files', '*.mini *.minipy *.csv'), ('All files', "*.*")],
                                              defaultextension='.mini')
        if filename:
            self.open_minis(filename)
        app.clear_progress_bar()

    def select_all(self, event=None):
        self.module_table.select_all()
    def select_from_event_pick(self, event=None):
        if not self.has_focus():
            return None
        self.event_pick = True # use this to avoid invoking other mouse-related events
        xdata, ydata = event.artist.get_offsets()[event.ind][0]
        if app.interpreter.multi_select:
            self.module_table.selection_toggle([round(xdata, app.interface.recordings[0].x_sigdig)])
        else:
            self.module_table.selection_set([round(xdata, app.interface.recordings[0].x_sigdig)])

    def select_from_table(self, selection):
        if not self.is_enabled():
            return None
        # pass a list of str for 't' column (index for table)
        selection = [float(i) for i in selection] # convert to float
        if selection:
            xs = self.extract_column('peak_coord_x', selection)
            ys = self.extract_column('peak_coord_y', selection)
            if len(selection) == 1:
                app.trace_display.center_plot_on(xs, ys)
            elif len(selection) > 1:
                app.trace_display.center_plot_area(min(xs), max(xs), min(ys), max(ys))
        else:
            xs = None
            ys = None
        self.plot_highlight(xs, ys) # get peak coordinates
        app.trace_display.draw_ani()

    def select_from_rect(self, event=None):
        if not self.has_focus():
            return None

        xlim = (app.interpreter.drag_coord_start[0], app.interpreter.drag_coord_end[0])
        xlim = (min(xlim), max(xlim))
        ylim = (app.interpreter.drag_coord_start[1], app.interpreter.drag_coord_end[1])
        ylim = (min(ylim), max(ylim))

        if self.mini_df.shape[0] == 0:
            return None
        df = self.mini_df[self.mini_df['channel'] == app.interface.channel]
        df = df[(df['t'] > xlim[0]) & (df['t'] < xlim[1])
                & (df['peak_coord_y'] > ylim[0]) & (df['peak_coord_y'] < ylim[1])]

        self.module_table.selection_set(list(df['t']))
    def select_clear(self, event=None):
        if not self.has_focus():
            return None
        self.module_table.unselect()
    def update_event_markers(self, event=None):
        if not self.is_visible():
            return None
        self.plot_peak(self.extract_column('peak_coord_x'), self.extract_column('peak_coord_y'))
        self.plot_decay(self.extract_column('decay_coord_x'), self.extract_column('decay_coord_y'))
        self.plot_start(self.extract_column('start_coord_x'), self.extract_column('start_coord_y'))
        try:
            hxs = self.markers['highlight'].get_xdata()
            hys = self.markers['highlight'].get_ydata()
            print(hxs, hys)
            self.plot_highlight(hxs, hys)
        except:
            pass

        app.trace_display.draw_ani()
        # app.trace_display.canvas.draw()

    def update_module_table(self):
        self.module_table.set(self.extract_channel_subset())

    def update_module_display(self, table=False):
        super().update_module_display()
        if self.status_var.get():
            self.update_event_markers()
        else:
            for m in self.markers:
                try:
                    self.markers[m].remove()
                except:
                    pass
            app.trace_display.draw_ani()

    def _load_layout(self):
        self.insert_title(
            text="Mini Analysis"
        )
        self.find_all_button = self.insert_button(
            text='Find all',
            command=self.find_mini_all
        )
        self.insert_button(
            text='Delete all',
            command=lambda undo=True: self.delete_all(undo)
        )
        self.insert_button(
            text='Find in\nwindow',
            command=self.find_mini_range
        )
        self.insert_button(
            text='Delete in\nwindow',
            command=lambda undo=True: self.delete_in_window(undo)
        )
        self.insert_button(
            text='Report stats'
        )

        self.insert_title(
            text='Core parameters'
        )
        self.insert_label_optionmenu(
            name='detector_core_direction',
            label='Direction',
            options=['positive', 'negative']
        )

        self.core_params = {
            'manual_radius': {'id': 'detector_core_search_radius',
                              'label': 'Search radius in % of visible x-axis (Manual)', 'validation': 'float',
                              'conversion': float},
            'auto_radius': {'id': 'detector_core_auto_radius',
                            'label': 'Search window in ms (Auto)', 'validation': 'float', 'conversion': float},
            'delta_x_ms': {'id': 'detector_core_deltax_ms',
                           'label': 'Points before peak to estimate baseline (ms)',
                           'validation': 'float/zero',
                           'conversion': float},
            'lag_ms': {'id': 'detector_core_lag_ms',
                       'label': 'Window of data points averaged to find start of mini (ms):',
                       'validation': 'float', 'conversion': float}
        }
        for k, d in self.core_params.items():
            self.insert_label_entry(
                name=d['id'],
                label=d['label'],
                validate_type=d['validation']
            )
            self.widgets[d['id']].bind('<Return>', self._apply_parameters, add='+')
            self.widgets[d['id']].bind('<FocusOut>', self._apply_parameters, add='+')
            self.parameters[d['id']] = self.widgets[d['id']].get()
            self.changes[d['id']] = self.widgets[d['id']].get()
        self.insert_label_checkbox(
            name='detector_core_extrapolate_hw',
            label='Use decay to extrapolate halfwidth',
            onvalue='1',
            offvalue=""
        )
        self.insert_title(
            text='Decay fitting options'
        )
        self.insert_label_optionmenu(
            name='detector_core_decay_algorithm',
            label='Decay calculation method:',
            options=['Curve fit', '% amplitude'],
            command=self.populate_decay_algorithms
        )
        self.decay_params = {
            'decay_p_amp': {
                'id': 'detector_core_decay_p_amp',
                'label': 'Percent peak to mark as decay constant (%)',
                'validation': 'float',
                'conversion': float,
                'algorithm': ['% amplitude']
            },
            'decay_ss_min': {
                'id': 'detector_core_decay_ss_min',
                'label': 'Minimum decay constant (ms)',
                'validation': 'float',
                'conversion': float,
                'algorithm': ['Sum of squares']
            },
            'decay_ss_max': {
                'id': 'detector_core_decay_ss_max',
                'label': 'Max decay constant (ms)',
                'validation': 'float',
                'conversion': float,
                'algorithm': ['Sum of squares']
            },
            'decay_ss_interval': {
                'id': 'detector_core_decay_ss_interval',
                'label': 'Decay constant estimation step (ms)',
                'validation': 'float/auto',
                'conversion': float,
                'algorithm': ['Sum of squares']
            },
            'decay_best_guess': {
                'id': 'detector_core_decay_best_guess',
                'label': 'Starting seed for exponential decay fit (ms)',
                'validation': 'float',
                'conversion': float,
                'algorithm': ['Curve fit']
            },
            'decay_max_interval': {
                'id': 'detector_core_decay_max_interval',
                'label': 'Maximum x-interval considered for decay (ms)',
                'validation': 'float',
                'conversion': float,
                'algorithm': ['Curve fit', 'Sum of squares', '% amplitude']
            }
        }
        for k, d in self.decay_params.items():
            entry = self.insert_label_entry(
                name=d['id'],
                label=d['label'],
                validate_type=d['validation']
            )
            entry.master.master.grid_remove()
            entry.bind('<Return>', self._apply_parameters, add='+')
            entry.bind('<FocusOut>', self._apply_parameters, add='+')
            self.parameters[d['id']] = entry.get()
            self.changes[d['id']] = entry.get()
        self.populate_decay_algorithms(self.widgets['detector_core_decay_algorithm'].get())

        self.insert_title(
            text='Compound mini options'
        )
        self.insert_label_checkbox(
            name='detector_core_compound',
            label='Analyze compound minis',
            onvalue='1',
            offvalue='',
            command=self.populate_compound_params
        )
        self.compound_params = {
            # 'extrapolation_length': {'id': 'detector_core_extrapolation_length',
            #                   'label': 'Number of points after previous peak to extrapolate decay', 'validation': 'int',
            #                   'conversion': int},
            'p_valley': {'id': 'detector_core_p_valley',
                         'label': 'Minimum valley size in % of peak amplitude', 'validation': 'float',
                         'conversion': float},
            'max_compound_interval': {'id': 'detector_core_max_compound_interval',
                                      'label': 'Maximum interval between two peaks to use compound mini analysis (ms)',
                                      'validation': 'float', 'conversion': float},
            'min_peak2peak_ms': {'id': 'detector_core_min_peak2peak',
                                 'label': 'Ignore minis closer than (ms):', 'validation': 'float'},

        }
        for k, d in self.compound_params.items():
            entry = self.insert_label_entry(
                name=d['id'],
                label=d['label'],
                validate_type=d['validation']
            )
            entry.bind('<Return>', self._apply_parameters, add='+')
            entry.bind('<FocusOut>', self._apply_parameters, add='+')
            self.parameters[d['id']] = entry.get()
            self.changes[d['id']] = entry.get()
        self.populate_compound_params()

        self.insert_button(
            text='Apply',
            command=self._apply_parameters
        )

        self.insert_button(
            text='Default',
            command=self.default_core_params
        )

        ############## filtering parameters ###############

        self.insert_title(
            text='Filtering parameters'
        )
        self.filter_params = {
            'min_amp': {'id': 'detector_filter_min_amp',
                        'label': 'Minimum amplitude (absolute value) (y-axis unit):',
                        'validation': 'float/None', 'conversion': float},
            'max_amp': {'id': 'detector_filter_max_amp',
                        'label': 'Maximum amplitude (absolute value) (y-axis unit):',
                        'validation': 'float/None', 'conversion': float},
            'min_decay': {'id': 'detector_filter_min_decay',
                          'label': 'Minimum decay constant (tau) (ms)', 'validation': 'float/None',
                          'conversion': float},
            'max_decay': {'id': 'detector_filter_max_decay', 'label': 'Maximum decay constant (tau) (ms)',
                          'validation': 'float/None', 'conversion': float},
            'min_hw': {'id': 'detector_filter_min_hw', 'label': 'Minimum halfwidth (ms)', 'validation': 'float/None',
                       'conversion': float},
            'max_hw': {'id': 'detector_filter_max_hw', 'label': 'Maximum halfwidth (ms)', 'validation': 'float/None',
                       'conversion': float},
            'min_rise': {'id': 'detector_filter_min_rise', 'label': 'Minimum rise constant (ms)',
                         'validation': 'float/None', 'conversion': float},
            'max_rise': {'id': 'detector_filter_max_rise', 'label': 'Maximum rise constant (ms)',
                         'validation': 'float/None', 'conversion': float},
            'min_drr': {'id': 'detector_filter_min_dr', 'label': 'Minimum decay:rise ratio', 'validation': 'float/None',
                        'conversion': float},
            'max_drr': {'id': 'detector_filter_max_dr', 'label': 'Maximum decay:rise ratio', 'validation': 'float/None',
                        'conversion': float},
            'min_s2n': {'id': 'detector_filter_min_s2n', 'label': 'Minimum amp:std ratio', 'validation': 'float/None',
                        'conversion': float},
            'max_s2n': {'id': 'detector_filter_max_s2n', 'label': 'Maximum amp:std ratio', 'validation': 'float/None',
                        'conversion': float}
        }
        for k, d in self.filter_params.items():
            entry = self.insert_label_entry(
                name=d['id'],
                label=d['label'],
                validate_type=d['validation']
            )
            entry.bind('<Return>', self._apply_parameters, add='+')
            entry.bind('<FocusOut>', self._apply_parameters, add='+')
            self.parameters[d['id']] = entry.get()
            self.changes[d['id']] = entry.get()

        self.insert_button(
            text='Confirm',
            command=self._apply_parameters
        )

        self.insert_button(
            text='Default',
            command=lambda filter='detector_filter': self.set_to_default(filter)
        )
        self.insert_button(
            text='Apply filter\n(all)',
            command=self.filter_all,
        )
        self.insert_button(
            text='Apply filter\n(window)',
            command=self.filter_window
        )

        self.data_display_options = [
            ('data_display_time', 'Peak time'),
            ('data_display_amplitude', 'Amplitude'),
            ('data_display_decay', 'Decay constant'),
            # ('data_display_decay_func', 'Decay function'),
            ('data_display_rise', 'Rise duration'),
            ('data_display_halfwidth', 'Halfwidth'),
            ('data_display_baseline', 'Baseline'),
            # ('data_display_start', 'Start time'),
            # ('data_display_end', 'End time'),
            ('data_display_channel', 'Channel'),
            ('data_display_std', 'Stdev'),
            ('data_display_direction', 'Direction'),
            ('data_display_compound', 'Compound')
        ]

        for option in self.data_display_options:
            self.insert_label_checkbox(
                name=option[0],
                label=option[1],
                command=self._apply_column_options,
                onvalue='1',
                offvalue=""
            )
        self.mini_header2config = {
            't': 'data_display_time',
            'amp': 'data_display_amplitude',
            'amp_unit': 'data_display_amplitude',
            'decay_const': 'data_display_decay',
            'decay_unit': 'data_display_decay',
            # ('decay_func', 'data_display_decay_func'),
            # ('decay_t', 'data_display_decay_time'),
            'rise_const': 'data_display_rise',
            'rise_unit': 'data_display_rise',
            'halfwidth': 'data_display_halfwidth',
            'halfwidth_unit': 'data_display_halfwidth',
            'baseline': 'data_display_baseline',
            'baseline_unit': 'data_display_baseline',
            'channel': 'data_display_channel',
            'stdev': 'data_display_std',
            'stdev_unit': 'data_display_std',
            'direction': 'data_display_direction',
            'compound': 'data_display_compound'
        }

        self.insert_button(
            text='Show All',
            command=self._columns_show_all
        )
        self.insert_button(
            text='Hide All',
            command=self._columns_hide_all
        )

    def _load_binding(self):
        # event bindings:
        app.root.bind('<<LoadCompleted>>', self._apply_column_options, add='+')
        app.root.bind('<<OpenRecording>>', lambda save=False: self.delete_clear(save), add="+")
        app.root.bind('<<DrawRect>>', self.select_from_rect, add="+")
        app.root.bind('<<ChangeChannel>>', self.change_channel, add="")
        app.root.bind('<<Plot>>', self.update_event_markers, add='+')

        app.trace_display.canvas.mpl_connect('button_release_event', self.canvas_mouse_release)
        app.trace_display.canvas.mpl_connect('pick_event', self.select_from_event_pick)
        for key in app.config.key_delete:
            app.trace_display.canvas.get_tk_widget().bind(key, self.delete_from_canvas, add='+')
        for key in app.config.key_deselect:
            app.trace_display.canvas.get_tk_widget().bind(key, self.select_clear, add='+')
        for key in app.config.key_select_all:
            app.trace_display.canvas.get_tk_widget().bind(key, self.select_all, add='+')


    def _modify_GUI(self):
        # menubar
        file_menu = app.menubar.make_file_menu_cascade(self.menu_label)
        file_menu.add_command(label='Open mini file', command=self.open_minis_dialogue)
        file_menu.add_command(label='Save minis as...', command=self.save_minis_dialogue)
        file_menu.add_command(label='Export table', command=self.export_minis_dialogue)

        # style tab
        style_tab = app.modules_dict['style']['control_panel']
        style_tab.optionframe.insert_separator()
        style_tab.insert_title(
            text='Mini Analysis plot style'
        )
        panel = style_tab.make_panel(separator=False)
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_columnconfigure(1, weight=1)
        panel.grid_columnconfigure(2, weight=1)

        row = 0
        ttk.Label(panel, text='size', justify=Tk.CENTER).grid(column=style_tab.size_column, row=row,
                                                                              sticky='news')
        ttk.Label(panel, text='color', justify=Tk.CENTER).grid(column=style_tab.color_column, row=row,
                                                                               sticky='news')
        def place_VarEntry(name, column, row, frame, width=None, validate_type=""):
            self.widgets[name] = widget.VarEntry(frame, name=name, width=width, validate_type=validate_type,
                                          value=self.values.get(name, None), default=self.default.get(name, None))
            self.widgets[name].grid(column=column, row=row, sticky='news')

        row += 1
        ttk.Label(panel, text='Peak marker').grid(column=style_tab.label_column, row=row, sticky='news')
        place_VarEntry(name='style_mini_size', column=style_tab.size_column, row=row, frame=panel,
                            width=style_tab.size_width, validate_type='float')
        place_VarEntry(name='style_mini_color', column=style_tab.color_column, row=row, frame=panel,
                            width=style_tab.color_width, validate_type='color')
        row += 1
        ttk.Label(panel, text='Start marker').grid(column=style_tab.label_column, row=row, sticky='news')
        place_VarEntry(name='style_start_size', column=style_tab.size_column, row=row, frame=panel,
                       width=style_tab.size_width, validate_type='float')
        place_VarEntry(name='style_start_color', column=style_tab.color_column, row=row, frame=panel,
                       width=style_tab.color_width, validate_type='color')

        row += 1
        ttk.Label(panel, text='Decay marker').grid(column=style_tab.label_column, row=row, sticky='news')
        place_VarEntry(name='style_decay_size', column=style_tab.size_column, row=row, frame=panel,
                       width=style_tab.size_width, validate_type='float')
        place_VarEntry(name='style_decay_color', column=style_tab.color_column, row=row, frame=panel,
                       width=style_tab.color_width, validate_type='color')

        row += 1
        ttk.Label(panel, text='Highlight marker').grid(column=style_tab.label_column, row=row, sticky='news')
        place_VarEntry(name='style_highlight_size', column=style_tab.size_column, row=row, frame=panel,
                       width=style_tab.size_width, validate_type='float')
        place_VarEntry(name='style_highlight_color', column=style_tab.color_column, row=row, frame=panel,
                       width=style_tab.color_width, validate_type='color')

        def _apply_styles(event=None):
            app.interface.focus()
            self.peak_size = float(self.widgets['style_mini_size'].get())
            self.peak_color = self.widgets['style_mini_color'].get()
            self.start_size = float(self.widgets['style_start_size'].get())
            self.start_color = self.widgets['style_start_color'].get()
            self.decay_size = float(self.widgets['style_decay_size'].get())
            self.decay_color = self.widgets['style_decay_color'].get()
            self.highlight_size = float(self.widgets['style_highlight_size'].get())
            self.highlight_color = self.widgets['style_highlight_color'].get()

            # for key in ['decay', 'start', 'highlight']:
            #     try:
            #         self.markers[key].set_color(self.widgets[f'style_{key}_color'].get())
            #         self.markers[key].set_markersize(float(self.widgets[f'style_{key}_size'].get()))
            #     except Exception as e:
            #         print(e)
            #         pass
            # try:
            #     self.markers['peak'].set_color(self.widgets['style_peak_color'].get())
            #     self.markers['peak'].set_sizes(float(self.widgets['style_peak_size'].get())**2)
            # except:
            #     pass
            #
            # app.trace_display.draw_ani()
            self.update_event_markers()

        def _apply_default(event=None):
            app.interface.focus()
            self.set_to_default(filter='style_')

        for w in self.widgets:
            if 'style' in w:
                self.widgets[w].bind('<Return>', _apply_styles, add='+')
        style_tab.insert_button(text='Apply', command= _apply_styles)
        style_tab.insert_button(text='Default', command= _apply_default)