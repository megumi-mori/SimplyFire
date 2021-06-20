from config import config
from utils.scrollable_option_frame import ScrollableOptionFrame
import pymini


def load(parent):
    ##################################################
    #                    Methods                     #
    ##################################################
    def _apply_column():
        pymini.table_panel.show_columns()

    def _adjust_data_col_width():
        pymini.table_panel.fit_columns()

    def _show_all():
        for key in frame.get_keys(filter='data_display_'):
            frame.widgets[key].set(1)
        pymini.table_panel.show_columns()

    def _hide_all():
        for key in frame.get_keys(filter='data_display_'):
            frame.widgets[key].set('')
        pymini.table_panel.show_columns()




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
        name = 'detector',
        text='Detector Parameters'
    )
    frame.insert_label_optionmenu(
        name='direction',
        label='Direction',
        value=config.direction,
        default=config.default_direction,
        options=['positive', 'negative']
    )
    frame.insert_label_entry(
        name='min_amp',
        label='Minimum amplitude (nA):',
        value=config.min_amp,
        default=config.default_min_amp,
        validate_type='float'
    )
    frame.insert_label_entry(
        name='points_baseline',
        label='Number of data points to average for baseline:',
        value=config.points_baseline,
        default=config.default_points_baseline,
        validate_type='int'
    )
    frame.insert_label_entry(
        name='points_search',
        label='Number of data points to search for a peak',
        value=config.points_search,
        default=config.default_points_search,
        validate_type='int'
    )
    frame.insert_label_entry(
        name='min_decay',
        label='Minimum decay constant (tau) (ms)',
        value=config.min_decay,
        default=config.default_min_decay,
        validate_type='float'
    )
    frame.insert_label_entry(
        name='min_auc',
        label='Minimum area under the curve',
        value=config.min_auc,
        default=config.default_min_auc,
        validate_type='float'
    )
    frame.insert_label_entry(
        name='max_points_baseline',
        label='Maximum data points to consider before peak to find the baseline',
        value=config.max_points_baseline,
        default=config.default_max_points_baseline,
        validate_type='int'
    )
    frame.insert_label_entry(
        name='max_points_decay',
        label='Maximum data points after peak to consider for decay',
        value=config.max_points_decay,
        default=config.default_max_points_decay,
        validate_type='int'
    )
    frame.insert_label_entry(
        name='manual_pixel_offset',
        label='Pixel offset for manually picking events',
        value=config.manual_pixel_offset,
        default=config.default_manual_pixel_offset,
        validate_type='int'
    )
    frame.insert_label_checkbox(
        name='update_events',
        label='Update graph after each event detection (will slow down search)',
        value=config.update_events,
        default=config.default_update_events,
    )
    frame.insert_button(
        text='Default Paramters',
        command=frame.default
    )

    frame.insert_button(text='hello, world!')
    frame.insert_button(text='hello, world!')
    frame.isolate_button()
    frame.insert_button(text='hello, world!')

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

    frame.insert_title(
        name='dataframe',
        text='Data Display'
    )


    frame.insert_label_checkbox(
        name='data_display_time',
        label='Event peak time',
        value=config.data_display_time,
        default=config.default_data_display_time,
        command=_apply_column,
        onvalue="1",
        offvalue=""
    )
    frame.insert_label_checkbox(
        name='data_display_amplitude',
        label='Event amplitude',
        value=config.data_display_amplitude,
        default=config.default_data_display_amplitude,
        command=_apply_column,
        onvalue="1",
        offvalue=""
    )
    frame.insert_label_checkbox(
        name='data_display_amp_unit',
        label='Event amplitude unit',
        value=config.data_display_amp_unit,
        command=_apply_column,
        onvalue='1',
        offvalue=""
    )
    frame.insert_label_checkbox(
        name='data_display_decay',
        label='Event decay constant',
        value=config.data_display_decay,
        default=config.default_data_display_decay,
        command=_apply_column,
        onvalue="1",
        offvalue=""
    )
    frame.insert_label_checkbox(
        name='data_display_decay_time',
        label='Event decay time point',
        value=config.data_display_decay_time,
        default=config.default_data_display_decay_time,
        command=_apply_column,
        onvalue="1",
        offvalue=""
    )
    frame.insert_label_checkbox(
        name='data_display_rise',
        label='Event rise duration',
        value=config.data_display_rise,
        default=config.default_data_display_rise,
        command=_apply_column,
        onvalue="1",
        offvalue=""
    )
    frame.insert_label_checkbox(
        name='data_display_baseline',
        label='Event start time',
        value=config.data_display_baseline,
        default=config.default_data_display_baseline,
        command=_apply_column,
        onvalue="1",
        offvalue=""
    )
    frame.insert_label_checkbox(
        name='data_display_channel',
        label='Event data channel',
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


