import numpy as np
import pandas as pd
def update_aggregate(ys:np.ndarray,
                     sampling_rate:int,
                     peak_idx:list=None,
                     mini_df:pd.DataFrame=None,
                     average_mini:np.ndarray=None,
                     num_minis:int=0,
                     ms_from_peak:float=None):
    """
    ys: np.ndarray of the recording
    sampling_rate: int in Hz
    peak_idx: list of peak indices matching ys - prioritized if given
    mini_df: pandas DataFrame of mini data - must be formatted according to the mini_analysis plugin
        must be provided if peak_idx is None
        ignored if peak_idx is given
    average_mini: np.ndarray of the aggregate minis (can be zeros). Use to combine data from previous calculations
    num_minis: int = number of minis already used to calculate the average_mini. Used to properly weigh the new information
    ms_from_peak: float representing the time frame that should be sampled centered around the peak
    if ms_from_peak is None, must provide data_neg and data_post arrays (can be np.zeros)

    """
    if average_mini is None:
        if ms_from_peak is None:
            raise Exception("average_mini or ms_from_peak must be provided")
        average_mini = np.zeros(int(ms_from_peak * sampling_rate/1000 * 2 + 1))
    else:
        average_mini = average_mini * num_minis

    half_len = int((average_mini.shape[0]-1)/2)
    if peak_idx is not None:
        for p in peak_idx:
            if p > half_len and p + half_len + 1 < ys.shape[0]:
                average_mini += ys[int(p-half_len):int(p+half_len + 1)]

        return average_mini/len(peak_idx), num_minis + len(peak_idx)
    else:
        for i in range(len(mini_df)):
            p = mini_df.loc[i, 'peak_idx']
            baseline = mini_df.loc[i, 'baseline']
            if p > half_len and p + half_len + 1 < ys.shape[0]:
                average_mini += ys[int(p - half_len):int(p + half_len + 1)] - baseline
        return average_mini/len(mini_df), num_minis + len(mini_df)
