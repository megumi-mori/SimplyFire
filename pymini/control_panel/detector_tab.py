from config import config
from utils.scrollable_option_frame import ScrollableOptionFrame
import pymini
from utils import widget


def load(parent):
    ##################################################
    #                    Methods                     #
    ##################################################

    def _apply_detector():
        pymini.plot_area.focus()

    def _apply_column():
        pymini.data_table.show_columns()

    def _adjust_data_col_width():
        pymini.data_table.fit_columns()

    def _show_all():
        for key in frame.get_keys(filter='data_display_'):
            frame.widgets[key].set(1)
        pymini.data_table.show_columns()

    def _hide_all():
        for key in frame.get_keys(filter='data_display_'):
            frame.widgets[key].set('')
        pymini.data_table.show_columns()

    def _hide_partner(partner):
        frame.set_value(partner, '')
        _apply_column()

    def _link_partner(wname, partner):
        frame.set_value(partner, frame.get_value(wname))
        _apply_column()

    # frame = ScrollableOptionFrame(parent)

    ##################################################
    #          Populate detector option tab          #
    ##################################################
    """
    Populates the detector tab in the control panel.
    :param frame:
    :return:
    """
    frame = ScrollableOptionFrame(parent)

    ##################################################
    #              Detector parameters               #
    ##################################################
    frame.insert_title(
        name='detector',
        text='Detector Parameters'
    )
    frame.insert_label_optionmenu(
        name='detector_direction',
        label='Direction',
        value=config.detector_direction,
        default=config.default_detector_direction,
        options=['positive', 'negative']
    )
    frame.insert_label_entry(
        name='detector_min_amp',
        label='Minimum amplitude (nA):',
        value=config.detector_min_amp,
        default=config.default_detector_min_amp,
        validate_type='float'
    )
    frame.insert_label_entry(
        name='detector_points_baseline',
        label='Number of data points averaged to find the start/end of an event:',
        value=config.detector_points_baseline,
        default=config.default_detector_points_baseline,
        validate_type='int'
    )
    frame.insert_label_entry(
        name='detector_points_search',
        label='Number of data points to search for a peak',
        value=config.detector_points_search,
        default=config.default_detector_points_search,
        validate_type='int'
    )
    frame.insert_label_entry(
        name='detector_min_decay',
        label='Minimum decay constant (tau) (ms)',
        value=config.detector_min_decay,
        default=config.default_detector_min_decay,
        validate_type='float'
    )
    frame.insert_label_entry(
        name='detector_min_auc',
        label='Minimum area under the curve',
        value=config.detector_min_auc,
        default=config.default_detector_min_auc,
        validate_type='float'
    )
    frame.insert_label_entry(
        name='detector_max_points_baseline',
        label='Maximum data points to consider before peak to find the baseline',
        value=config.detector_max_points_baseline,
        default=config.default_detector_max_points_baseline,
        validate_type='int'
    )
    frame.insert_label_entry(
        name='detector_max_points_decay',
        label='Maximum data points after peak to consider for decay',
        value=config.detector_max_points_decay,
        default=config.default_detector_max_points_decay,
        validate_type='int'
    )
    frame.insert_label_entry(
        name='detector_manual_pixel_offset',
        label='Pixel offset for manually picking events',
        value=config.detector_manual_pixel_offset,
        default=config.default_detector_manual_pixel_offset,
        validate_type='int'
    )
    frame.insert_label_checkbox(
        name='detector_update_events',
        label='Update graph after each event detection (will slow down search)',
        value=config.detector_update_events,
        default=config.default_detector_update_events,
    )
    frame.insert_button(
        text='Apply',
        command=pymini.plot_area.focus
    )
    frame.insert_button(
        text='Default paramters',
        command=frame.default
    )
    frame.insert_button(
        text='Find all',
        command=None  # link this later
    )
    frame.insert_button(
        text='Delete all',
        command=None  # link this later
    )
    frame.insert_button(
        text='Find in window',
        command=None  # link this later
    )

    frame.insert_button(
        text='Delete in window',
        command=None  # link this later
    )

    ##################################################
    #                  Data Export                   #
    ##################################################
    frame.insert_title(
        name='data_export',
        text='Data Export'
    )
    frame.insert_label_checkbox(
        name='data_export_all',
        label='Export all visible and hidden data?',
        value=config.data_export_all,
        default=config.default_data_export_all,
        # command=None #Link this to exporting data sets
    )

    ##################################################
    #                  Data Display                  #
    ##################################################
    # all column display options for the data table must start with "data_display_"

    frame.insert_title(
        name='dataframe',
        text='Data Table Display'
    )

    frame.insert_label_checkbox(
        name='data_display_time',
        label='Peak time',
        value=config.data_display_time,
        default=config.default_data_display_time,
        command=_apply_column,
        onvalue="1",
        offvalue=""
    )
    frame.insert_label_checkbox(
        name='data_display_amplitude',
        label='Amplitude',
        value=config.data_display_amplitude,
        default=config.default_data_display_amplitude,
        command=lambda w='data_display_amplitude',
                       p='data_display_amp_unit': _link_partner(w, p),
        onvalue="1",
        offvalue=""
    )
    frame.widgets['data_display_amp_unit'] = widget.VarWidget(
        value=config.data_display_amp_unit,
        default=config.default_data_display_amp_unit,
    )
    frame.insert_label_checkbox(
        name='data_display_decay_constant',
        label='Decay constant',
        value=config.data_display_decay_constant,
        default=config.default_data_display_decay_constant,
        command=lambda w='data_display_decay_constant',
                       p='data_display_decay_unit': _link_partner(w, p),
        onvalue="1",
        offvalue=""
    )
    frame.widgets['data_display_decay_unit'] = widget.VarWidget(
        value=config.data_display_decay_unit,
        default=config.default_data_display_decay_unit,
    )
    frame.insert_label_checkbox(
        name='data_display_decay_time',
        label='Decay time point',
        value=config.data_display_decay_time,
        default=config.default_data_display_decay_time,
        command=_apply_column,
        onvalue="1",
        offvalue=""
    )
    frame.insert_label_checkbox(
        name='data_display_rise_constant',
        label='Rise duration',
        value=config.data_display_rise_constant,
        command=lambda w='data_display_rise_constant',
                       p='data_display_rise_unit': _link_partner(w, p),
        onvalue="1",
        offvalue=""
    )
    frame.widgets['data_display_rise_unit'] = widget.VarWidget(
        value=config.data_display_rise_unit,
        default=config.default_data_display_rise_unit,
    )
    frame.insert_label_checkbox(
        name='data_display_halfwidth',
        label='Rise unit',
        value=config.data_display_halfwidth,
        default=config.default_data_display_halfwidth,
        command=lambda w='data_display_halfwidth',
                       p='data_display_halfwidth_unit': _link_partner(w, p),
        onvalue="1",
        offvalue=""
    )
    frame.widgets['data_display_halfwidth_unit'] = widget.VarWidget(
        value=config.data_display_halfwidth_unit,
        default=config.default_data_display_halfwidth_unit,
    )
    frame.insert_label_checkbox(
        name='data_display_baseline',
        label='Baseline',
        value=config.data_display_baseline,
        default=config.default_data_display_baseline,
        command=lambda w='data_display_baseline',
                       p='data_display_baseline_unit': _link_partner(w, p),
        onvalue="1",
        offvalue=""
    )
    frame.widgets['data_display_baseline_unit'] = widget.VarWidget(
        value=config.data_display_baseline_unit,
        default=config.default_data_display_baseline_unit,
    )
    frame.insert_label_checkbox(
        name='data_display_end',
        label='Start time',
        value=config.data_display_end,
        default=config.default_data_display_end,
        command=_apply_column,
        onvalue="1",
        offvalue=""
    )
    frame.insert_label_checkbox(
        name='data_display_start',
        label='End time',
        value=config.data_display_start,
        default=config.default_data_display_start,
        command=_apply_column,
        onvalue="1",
        offvalue=""
    )
    frame.insert_label_checkbox(
        name='data_display_channel',
        label='Channel',
        value=config.data_display_channel,
        default=config.default_data_display_channel,
        command=_apply_column,
        onvalue="1",
        offvalue=""
    )
    frame.insert_button(
        text='Show All',
        command=_show_all
    )
    frame.insert_button(
        text='Hide All',
        command=_hide_all
    )
    frame.insert_button(
        text='Fit columns',
        command=_adjust_data_col_width
    )

    return frame
