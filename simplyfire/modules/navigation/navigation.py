"""
simplyfire - Customizable analysis of electrophysiology data
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
from simplyfire.modules.base_module import BaseModule
from simplyfire.modules.base_module_control import BaseModuleControl
from simplyfire import app

class Module(BaseModule):
    def __init__(self):
        super().__init__(
            name='navigation',
            menu_label='Navigation',
            tab_label='Navi',
            filename=__file__
        )

class ModuleControl(BaseModuleControl):
    def __init__(self, module):
        super().__init__(
            module=module,
            scrollbar=True
        )

        self._load_layout()
        self._load_binding()

    def apply_window(self, event=None):
        min_x = self.widgets['window_min_x'].get()
        if min_x == 'auto':
            min_x = app.trace_display.default_xlim[0]
        else:
            min_x = float(min_x)
        max_x = self.widgets['window_max_x'].get()
        if max_x == 'auto':
            max_x = app.trace_display.default_xlim[1]
        else:
            max_x = float(max_x)
        min_y = self.widgets['window_min_y'].get()
        if min_y == 'auto':
            min_y = app.trace_display.default_ylim[0]
        else:
            min_y = float(min_y)
        max_y = self.widgets['window_max_y'].get()
        if max_y == 'auto':
            max_y = app.trace_display.default_ylim[1]
        else:
            max_y = float(max_y)

        app.trace_display.set_axis_limit('x', (min_x, max_x))
        app.trace_display.set_axis_limit('y', (min_y, max_y))

        app.trace_display.draw_ani()
        app.interface.focus()

    def apply_navigation(self, event=None):
        app.interpreter.navigation_fps = int(self.widgets['navigation_fps'].get())
        app.inputs['navigation_fps'].set(int(self.widgets['navigation_fps'].get()))
        app.inputs['navigation_scroll_x_percent'].set(float(self.widgets['navigation_scroll_x_percent'].get()))
        app.inputs['navigation_zoom_x_percent'].set(float(self.widgets['navigation_zoom_x_percent'].get()))
        app.inputs['navigation_scroll_y_percent'].set(float(self.widgets['navigation_scroll_y_percent'].get()))
        app.inputs['navigation_zoom_y_percent'].set(float(self.widgets['navigation_zoom_y_percent'].get()))
        app.inputs['navigation_mirror_x_scroll'].set(int(self.widgets['navigation_mirror_x_scroll'].get()))
        app.inputs['navigation_mirror_y_scroll'].set(int(self.widgets['navigation_mirror_y_scroll'].get()))
        app.interface.focus()



    def get_current_lim(self, event=None):
        xlim = app.trace_display.get_axis_limits('x')
        ylim = app.trace_display.get_axis_limits('y')
        self.widgets['window_min_x'].set(xlim[0])
        self.widgets['window_max_x'].set(xlim[1])
        self.widgets['window_min_y'].set(ylim[0])
        self.widgets['window_max_y'].set(ylim[1])
        app.interface.focus()
    def get_current_xlim(self, event=None):
        xlim = app.trace_display.get_axis_limits('x')
        self.widgets['window_min_x'].set(xlim[0])
        self.widgets['window_max_x'].set(xlim[1])
        app.interface.focus()

    def get_current_ylim(self, event=None):
        ylim = app.trace_display.get_axis_limits('y')
        self.widgets['window_min_y'].set(ylim[0])
        self.widgets['window_max_y'].set(ylim[1])
        app.interface.focus()

    def on_open(self, event=None):
        if self.widgets['window_force_lim'].get():
            self.apply_window()

    def show_all(self, event=None):
        app.trace_display.set_axis_limit('x', app.trace_display.default_xlim)
        app.trace_display.set_axis_limit('y', app.trace_display.default_ylim)
        app.trace_display.draw_ani()

    def _load_layout(self):

        self.insert_title(text='Navigation')
        panel = self.make_panel(separator=True)
        label = self.make_label(panel, text='x-axis:')
        label.grid(column=0, row=0, sticky='news')
        entry = self.make_entry(panel, name='window_min_x')
        entry.grid(column=1, row=0, sticky='news')
        entry.bind('<Return>', self.apply_window, add='+')
        entry = self.make_entry(panel, name='window_max_x')
        entry.grid(column=2, row=0, sticky='news')
        entry.bind('<Return>', self.apply_window, add='+')
        button = self.make_button(panel, text='Get', command=self.get_current_xlim)
        button.grid(column=3, row=0, sticky='news')

        panel = self.make_panel(separator=True)
        label = self.make_label(panel, text='y-axis:')
        label.grid(column=0, row=0, sticky='news')
        entry = self.make_entry(panel, name='window_min_y')
        entry.grid(column=1, row=0, sticky='news')
        entry.bind('<Return>', self.apply_window, add='+')
        entry = self.make_entry(panel, name='window_max_y')
        entry.grid(column=2, row=0, sticky='news')
        entry.bind('<Return>', self.apply_window, add='+')
        button = self.make_button(panel, text='Get',command=self.get_current_ylim)
        button.grid(column=3, row=0, sticky='news')

        self.insert_label_checkbox(
            name='window_force_lim',
            text='Force axis limits on open',
            type=bool,
            onvalue=True,
            offvalue=False
        )

        self.insert_button(text='Apply', command=self.apply_window)
        self.insert_button(text='Default', command=lambda filter='window':self.set_to_default(filter=filter))
        self.insert_button(text='Show all', command=self.show_all)
        self.insert_button(text='Get current', command=self.get_current_lim)

        self.insert_separator()
        #############################
        entries = [
            ('navigation_fps', 'Smooth navigation speed (fps)', 'int'),
            ('navigation_scroll_x_percent', 'Scroll speed (percent x-axis)', 'float'),
            ('navigation_zoom_x_percent', 'Zoom speed (percent x-axis)', 'float'),
            ('navigation_scroll_y_percent', 'Scroll speed (percent y-axis)', 'float'),
            ('navigation_zoom_y_percent', 'Zoom speed (percent y-axis)', 'float'),
        ]
        for e in entries:
            entry = self.insert_label_entry(
                name=e[0],
                text=e[1],
                validate_type=e[2]
            )
            entry.bind('<Return>', self.apply_navigation, add='+')

        boxes = [
            ('navigation_mirror_x_scroll', 'Mirror x-axis scroll'),
            ('navigation_mirror_y_scroll', 'Mirror y-axis scroll'),
        ]
        for b in boxes:
            box = self.insert_label_checkbox(
                name=b[0],
                text=b[1],
                onvalue=-1,
                offvalue=1,
                type=int,
                command=self.apply_navigation
            )
        self.insert_button(text='Apply', command=self.apply_navigation)
        self.insert_button(text='Default', command=lambda filter='navigation':self.set_to_default(filter=filter))
    def _load_binding(self):
        self.listen_to_event('<<OpenedRecording>>', self.on_open)

        show_all_keys = getattr(app.config, 'key_show_all', self.defaults.get('key_show_all', []))
        for key in show_all_keys:
            app.trace_display.canvas.get_tk_widget().bind(key, self.show_all, add='+')