from tkinter import ttk, filedialog
import tkinter as Tk
import yaml
import pkg_resources
from PIL import Image
import os
from PyMini.utils import widget
from PyMini.Backend import interpreter, interface
from PyMini.config import config
from PyMini.Layout import detector_tab, style_tab, setting_tab, navigation_tab, \
    sweep_tab, graph_panel, continuous_tab, adjust_tab, evoked_tab, batch_popup, menubar,\
    compare_tab
from PyMini.DataVisualizer import data_display, log_display, evoked_data_display, results_display, trace_display, param_guide
import importlib

# debugging
import tracemalloc
import time




event_filename = None
widgets = {}

##################################################
#                    Methods                     #
##################################################

def _on_close():
    """
    The function is called when the program is closing (pressing X)
    Uses the config module to write out user-defined parameters
    :return: None
    """
    global widgets
    # if widgets['config_autosave'].get():
    # try:
    dump_user_setting()
    # except:
    #     Tk.messagebox.showinfo(title='Error', message='Error while writing out user preferences.\n Please select a new filename.')
    #     f = setting_tab.save_config_as()
    #     if f:
    #         widgets['config_user_path'].set(f)

    dump_config_var(key='key_', filename=config.config_keymap_path, title='Keymap')
    dump_system_setting()
    root.destroy()
    app_root.destroy()

def get_value(key, tab=None):
    try:
        v = widgets[key].get()
        return v
    except Exception as e:
        pass

def get_widget(key, tab=None):
    try:
        return widgets[key]
    except:
        pass


def set_value(key, value, tab=None):
    widgets[key].set(value)
    try:
        widgets[key].set(value)
        return
    except:
        raise
        None


# def change_label(key, value, tab=None):
#     try:
#         tabs[tab].change_label(key, value)
#         return True
#     except:
#         for t in tabs:
#             try:
#                 tabs[t].change_label(key, value)
#                 return True
#             except:
#                 pass
#     return False

def load(splash):
    # debugging:
    global t0
    t0 = time.time()
    global app_root
    app_root = splash
    # tracemalloc.start()
    config.load()
    global root
    global loaded
    loaded = False
    root = Tk.Toplevel()
    root.withdraw()
    root.title('SimplyFire v{}'.format(config.version))
    IMG_DIR = pkg_resources.resource_filename('PyMini', 'img/')
    root.iconbitmap(os.path.join(IMG_DIR, 'logo_bw.ico'))
    if config.zoomed:
        root.state('zoomed')
    root.bind('<Control-o>', lambda e:menubar.ask_open_recording())
    global menu
    menu = Tk.Menu(root)
    root.config(menu=menu)
    root.grid_rowconfigure(0, weight=1)
    root.grid_columnconfigure(0, weight=1)

    frame = Tk.Frame(root, bg='red')
    frame.grid(column=0, row=0, sticky='news')

    # root.bind(config.key_reset_focus, lambda e: data_display.table.focus_set())


    global arrow_img
    arrow_img = Image.open(os.path.join(IMG_DIR, 'arrow.png'))

    global widgets
    global pw
    pw = Tk.PanedWindow(
        root,
        orient=Tk.HORIZONTAL,
        showhandle=True,
        sashrelief=Tk.SUNKEN,
        handlesize=config.default_pw_handlesize
    )

    pw.grid(column=0, row=0, sticky='news')


    ##################################################
    #                   DATA PANEL                   #
    ##################################################

    # set up frame
    right = Tk.Frame(pw, background = 'pink')
    right.grid(column=0, row=0, sticky='news')
    right.columnconfigure(0, weight=1)
    right.rowconfigure(0, weight=1)

    dp_notebook = ttk.Notebook(right)
    dp_notebook.grid(column=0, row=0, sticky='news')

    global pw_2
    pw_2 = Tk.PanedWindow(
        right,
        orient=Tk.VERTICAL,
        showhandle=True,
        sashrelief=Tk.SUNKEN,
        handlesize=config.default_pw_handlesize
    )


    # must set up a graph object that can 'refresh' and 'plot' etc
    global gp
    gp = graph_panel.load(root)
    root.update_idletasks()
    pw_2.add(gp)
    pw_2.paneconfig(gp, height=config.gp_height)

    global data_notebook
    data_notebook = ttk.Notebook(pw_2)



    pw_2.add(data_notebook)
    dp_notebook.add(pw_2, text='trace')

    log_frame = log_display.load(root)
    dp_notebook.add(log_frame, text='log')

    results_frame = results_display.load(root)
    dp_notebook.add(results_frame, text='results', sticky='news')


    ##################################################
    #                 CONTROL PANEL                  #
    ##################################################

    # set up frame
    global cp
    cp = Tk.Frame(pw, background='blue')
    cp.grid(column=0, row=0, sticky='news')
    cp.grid_rowconfigure(0, weight=1)
    cp.grid_columnconfigure(0, weight=1)

    global cp_notebook
    cp_notebook = ttk.Notebook(cp)
    cp_notebook.grid(column=0, row=0, sticky='news')

    #############################################################
    # Insert custom tabs here to include in the control panel
    #############################################################
    global cp_tab_details

    # cp_tab_details = {
    #     'mini': {'module': detector_tab, 'text': 'Analysis', 'partner': ['evoked'], 'name':'detector_rab'},
    #     'evoked': {'module': evoked_tab, 'text': 'Analysis', 'partner': ['mini'], 'name':'evoked_tab'},
    #     'continuous': {'module': continuous_tab, 'text': 'View', 'partner': ['overlay', 'compare'], 'name':'continuous_tab'},
    #     'overlay': {'module': sweep_tab, 'text': 'View', 'partner': ['continuous', 'compare'], 'name':'sweep_tab'},
    #     'compare':{'module': compare_tab, 'text': 'View', 'partner': ['continuous', 'overlay'], 'name':'compare_tab'},
    #     'adjust': {'module': adjust_tab, 'text': 'Adjust', 'partner': [], 'name':'adjust_tab'},
    #     'navigation': {'module': navigation_tab, 'text': 'Navi', 'partner': [], 'name':'navigation_tab'},
    #     'style':{'module': style_tab, 'text': 'Style', 'partner': [], 'name':'style_tab'},
    #     'setting':{'module': setting_tab, 'text': 'Setting', 'partner': [], 'name':'setting_tab'}
    # }
    #
    # for i, t in enumerate(cp_tab_details):
    #     cp_tab_details[t]['tab'] = cp_tab_details[t]['module'].load(cp)
    #     cp_notebook.add(cp_tab_details[t]['tab'], text=cp_tab_details[t]['text'])
    #     cp_tab_details[t]['index'] = i
    #     globals()[cp_tab_details[t]['name']] = cp_tab_details[t]['module']

    # root.bind('<Configure>', print)

    # test = StyleTab(left, __import__(__name__), interface)
    # cp_notebook.add(test, text='test')

    for k, v in graph_panel.widgets.items():
        widgets[k] = v
    # get reference to widgets
    # for module in [detector_tab, evoked_tab, adjust_tab, navigation_tab, style_tab, setting_tab, graph_panel]:
    #     for k, v in module.widgets.items():
    #         widgets[k] = v
    # setting_tab.set_fontsize(widgets['font_size'].get())
    # # set focus rules
    for key in widgets:
        if type(widgets[key]) == widget.VarEntry:
            widgets[key].bind('<Return>', lambda e: interface.focus(), add='+')
        if type(widgets[key]) == widget.VarCheckbutton:
            widgets[key].bind('<ButtonRelease>', lambda e: interface.focus(), add='+')
        if type(widgets[key]) == widget.VarOptionmenu:
            widgets[key].bind('<ButtonRelease>', lambda e: interface.focus(), add='+')
        if type(widgets[key]) == widget.VarCheckbutton:
            widgets[key].bind('<ButtonRelease>', lambda e: interface.focus(), add='+')

    # set up font adjustment bar
    # fb = font_bar.load(left, config.font_size)
    # widgets['font_size'] = font_bar.font_scale
    # fb.grid(column=0, row=1, sticky='news')

    # set up progress bar
    global pb
    # pb = progress_bar.ProgressBar(left)
    pb = ttk.Progressbar(cp, length=100,
                         mode='determinate',
                         orient=Tk.HORIZONTAL)
    pb.grid(column=0, row=2, stick='news')

    # finis up the pw setting:

    pw.grid(column=0, row=0, sticky='news')
    pw.add(cp)
    pw.add(right)

    # adjust frame width
    root.update()
    pw.paneconfig(cp, width=int(config.cp_width))

    ##################################################
    #                    MENU BAR                    #
    ##################################################

    # set up menubar
    menubar.load(menu)

    # menubar.analysis_menu.add_command(label='Batch Processing', command=batch_popup.load)

    globals()['menubar'] = menubar

    for k, v in menubar.widgets.items():
        widgets[k] = v
    global control_panel_dict
    control_panel_dict = {}

    global data_notebook_dict
    data_notebook_dict = {}

    global modules_dict
    modules_dict = {}

    with open(os.path.join(config.CONFIG_DIR, 'modules.yaml')) as f:
        module_list = yaml.safe_load(f)['modules']
        for module_name in module_list:
            load_module(module_name)


            # except Exception as e:
            #     print(e)
            #     pass
        # # only show one tab at a time
        # global data_tab_details
        # data_tab_details = {
        #     'mini': {'module': data_display, 'text': 'Mini Data'},
        #     'evoked': {'module': evoked_data_display, 'text': 'Evoked Data'}
        # }
        # for i, t in enumerate(data_tab_details):
        #     data_tab_details[t]['tab'] = data_tab_details[t]['module'].load(root)
        #     data_notebook.add(data_tab_details[t]['tab'], text=data_tab_details[t]['text'])
        #     data_tab_details[t]['index'] = i
    # set up closing sequence

    root.protocol('WM_DELETE_WINDOW', _on_close)

    # set up event bindings
    interpreter.initialize()
    root.deiconify()
    # # finalize the data viewer - table
    root.geometry(config.geometry)
    root.update()
    # data_display.fit_columns()
    # evoked_data_display.fit_columns()
    for key, datatab in data_notebook_dict.items():
        datatab.fit_columns()
        data_notebook.tab(datatab, state='hidden')
    for key, cptab in control_panel_dict.items():
        cp_notebook.tab(cptab, state='hidden')
    for modulename in config.start_module:
        try:
            menubar.window_menu.invoke(control_panel_dict[modulename].menu_label)
        except: # module removed from module-list
            pass
    try:
        data_notebook.select(data_notebook_dict[config.start_module[0]])
    except:
        pass
    try:
        cp_notebook.select(control_panel_dict[config.start_module[0]])
    except:
        pass

    ## root2 = root
    loaded = True
    root.event_generate('<<LoadCompleted>>')

    root.focus_force()
    interface.focus()
    splash.withdraw()
    return None

def load_module(module_name):
    global modules_dict
    if modules_dict.get(module_name, None):
        return
    modules_dict[module_name] = {}
    # load modules
    module_path = os.path.join(pkg_resources.resource_filename('PyMini', 'Modules'), module_name)
    # try:
    with open(os.path.join(module_path, 'config.yaml'), 'r') as config_file:
        module_config = yaml.safe_load(config_file)
    if module_config.get('dependencies', None):
        # has dependencies
        for req_module_name in module_config['dependencies']:
            load_module(req_module_name)
    tab = None
    for component, details in module_config['GUI_components'].items():
        if details['location'] == 'load':
            module_loader = importlib.import_module(f'PyMini.Modules.{module_name}.{component}')
            module_loader.load()
            modules_dict[module_name][component] = tab
        if details['location'] == 'control_panel':
            module_tab = importlib.import_module(f'PyMini.Modules.{module_name}.{component}')
            tab = module_tab.ModuleControl()
            cp_notebook.add(tab, text=tab.tab_label)
            # cp_notebook.tab(tab.frame, state='hidden')
            control_panel_dict[tab.name] = tab
            modules_dict[module_name]['control_panel'] = tab
            modules_dict[module_name][component] = tab
        if details['location'] == 'data_notebook':
            module_table = importlib.import_module(f'PyMini.Modules.{module_name}.{component}')
            table = module_table.ModuleTable()
            data_notebook.add(table, text=table.tab_label)
            modules_dict[module_name]['data_notebook'] = table
            modules_dict[module_name][component] = tab
            # data_notebook.tab(table.frame, state='hidden')
            data_notebook_dict[table.name] = table
            table.connect_to_control(tab)
def get_tab_focus():
    focus = {}
    focus['control_panel'] = cp_notebook.select()
    focus['data_panel'] = data_notebook.select()
    return focus

def get_module(module_name, component=None):
    module = modules_dict.get(module_name, None)
    if not module:
        return None
    if component:
        return module.get(component, None)
    else:
        return module

def get_cp_frame(name):
    return control_panel_dict[name]

def get_cp_module(name):
    return control_panel_dict[name]

def get_data_module(name):
    return data_notebook_dict[name]

def get_data_frame(name):
    return data_notebook_dict[name]

def get_data_table(name):
    return data_notebook_dict[name]

def advance_progress_bar(value, mode='determinate'):
    if mode == 'determinate':
        pb['value'] += value
    else:
        pb['value'] = (pb['value'] + value) % 100
    pb.update()
def set_progress_bar(value):
    global pb
    pb['value'] = value
    pb.update()

def clear_progress_bar():
    global pb
    pb['value'] = 0
    pb.update()

def dump_user_setting(filename=None):
    global widgets
    ignore = ['config_', '_log', 'temp_']
    print('Writing out configuration variables....')
    if filename is None:
        # filename = widgets['config_user_path'].var.get().strip()
        filename = os.path.join(pkg_resources.resource_filename('PyMini', 'config'), 'test_user_config.yaml')
    with open(filename, 'w') as f:
        print('writing dump user config {}'.format(filename))
        f.write("#################################################################\n")
        f.write("# PyMini user configurations\n")
        f.write("#################################################################\n")
        f.write("\n")
        # pymini.pb.initiate()
        d = {}
        for key in widgets.keys():
            try:
                for ig in ignore:
                    if ig in key:
                        break
                else:
                    d[key] = widgets[key].get()
            except:
                d[key] = widgets[key].get()
        global cp
        if loaded:
            d['zoomed'] = root.state() == 'zoomed'
            if not root.state() == 'zoomed':
                d['cp_width'] = cp.winfo_width()
                d['gp_height'] = gp.winfo_height()
                d['geometry'] = root.geometry().split('+')[0]

        # d['compare_color_list'] = config.compare_color_list
        # d['compare_color_list'][:len(compare_tab.trace_list)] = [c['color_entry'].get() for c in compare_tab.trace_list]
        d['start_module'] = []
        for modulename in control_panel_dict:
            d[modulename] = control_panel_dict[modulename].get_widget_dict()
            if control_panel_dict[modulename].status_var.get():
                d['start_module'].append(modulename)
        print('save output:')
        f.write(yaml.safe_dump(d))
        # pymini.pb.clear()

        # f.write(yaml.safe_dump(user_vars))
    print('Completed')

def dump_system_setting():
    print('Saving config options....')
    with open(config.config_system_path, 'w') as f:
        print('dumping system config {}'.format(config.config_system_path))
        f.write("#################################################################\n")
        f.write("# PyMini system configurations\n")
        f.write("#################################################################\n")
        f.write("\n")

        # f.write(yaml.safe_dump(dict([(key, widgets[key].get()) for key in widgets if 'config' in key])))
        f.write(yaml.safe_dump(dict([(n, getattr(config, n)) for n in config.user_vars if 'config' in n])))
    print('Completed')

def dump_config_var(key, filename, title=None):
    print('Saving "{}" config values...'.format(key))
    print(filename)
    with open(filename, 'w') as f:
        f.write("#################################################################\n")
        f.write("# PyMini {} configurations\n".format(title))
        f.write("#################################################################\n")
        f.write("\n")
        f.write(yaml.safe_dump(dict([(n, getattr(config, n)) for n in config.user_vars if key in n])))
    print('Completed')

def load_config(e=None):
    f = filedialog.askopenfile()
    if not f:
        return None
    configs = yaml.safe_load(f)
    for c, v in configs.items():
        try:
            widgets[c].set(v)
        except:
            pass

def print_time_lapse(msg=""):
    global t0
    try:
        print(f"{msg}: {time.time() - t0}")
    except:
        print(msg)
        pass
    t0 = time.time()