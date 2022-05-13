# Standard python and AWS imports:
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from matplotlib.dates import DateFormatter
from matplotlib import gridspec

def plot_timeseries(
    timeseries_df,
    tag_name, 
    start=None,
    end=None, 
    plot_rolling_avg=False, 
    labels_df=None, 
    predictions=None,
    tag_split=None,
    custom_grid=True,
    fig_width=18,
    prediction_titles=None,
    shutdown_ranges_df=None,
    evaluation_color=None,
    evaluation_alpha=0.5
):
    """
    This function plots a time series signal with a line plot and can combine
    this with labelled and predicted anomaly ranges.
    
    PARAMS
    ======
        timeseries_df: pandas.DataFrame
            A dataframe containing the time series to plot
        
        tag_name: string
            The name of the tag that we can add in the label
        
        start: string or pandas.Datetime (default: None)
            Starting timestamp of the signal to plot. If not provided, will use
            the whole signal
        
        end: string or pandas.Datetime (default: None)
            End timestamp of the signal to plot. If not provided, will use the
            whole signal
        
        plot_rolling_avg: boolean (default: False)
            If set to true, will add a rolling average curve on top of the
            line plot for the time series.
        
        labels_df: pandas.DataFrame (default: None)
            If provided, this is a dataframe with all the labelled anomalies.
            This will be rendered as a filled-in plots below the time series
            itself.
        
        predictions: pandas.DataFrame or list of pandas.DataFrame
            If provided, this is a dataframe with all the predicted anomalies.
            This will be rendered as a filled-in plots below the time series
            itself.
            
        tag_split: string or pandas.Datetime
            If provided, the line plot will plot the first part of the time
            series with a colour and the second part in grey. This can be
            used to show the split between training and evaluation period for
            instance.
        
        custom_grid: boolean (default: True)
            Will show a custom grid with month name mentionned for each quarter
            and lighter lines for the other month to prevent clutter on the
            horizontal axis.
        
        fig_width: integer (default: 18)
            Figure width.
        
        prediction_titles: list of strings (default: None)
            If we want to plot multiple predictions, we can set the titles for
            each of the prediction plot.
    
    RETURNS
    =======
        fig: matplotlib.pyplot.figure
            A figure where the plots are drawn
            
        ax: matplotlib.pyplot.Axis
            An axis where the plots are drawn
    """
    if start is None:
        start = timeseries_df.index.min()
    elif type(start) == str:
        start = pd.to_datetime(start)
        
    if end is None:
        end = timeseries_df.index.max()
    elif type(end) == str:
        end = pd.to_datetime(end)
        
    if (tag_split is not None) & (type(tag_split) == str):
        tag_split = pd.to_datetime(tag_split)

    # Prepare the figure:
    fig_height = 4
    height_ratios = [8]
    nb_plots = 1
    
    if labels_df is not None:
        fig_height += 1
        height_ratios += [1.5]
        nb_plots += 1
        
    if predictions is not None:
        if type(predictions) == pd.core.frame.DataFrame:
            fig_height += 1
            height_ratios += [1.5]
            nb_plots += 1
        elif type(predictions) == list:
            fig_height += 1 * len(predictions)
            height_ratios = height_ratios + [1.5] * len(predictions)
            nb_plots += len(predictions)
            
    fig = plt.figure(figsize=(fig_width, fig_height))
    gs = gridspec.GridSpec(nb_plots, 1, height_ratios=height_ratios, hspace=0.5)
    ax = []
    for i in range(nb_plots):
        ax.append(fig.add_subplot(gs[i]))
        
    # Plot the time series signal:
    data = timeseries_df[start:end].copy()
    if tag_split is not None:
        ax[0].plot(data.loc[start:tag_split, 'Value'], 
                   linewidth=0.5, 
                   alpha=0.5, 
                   label=f'{tag_name} - Training', 
                   color='tab:grey')
        
        if evaluation_color is not None:
            ax[0].plot(data.loc[tag_split:end, 'Value'], 
                       linewidth=0.5, 
                       alpha=evaluation_alpha,
                       color=evaluation_color,
                       label=f'{tag_name} - Evaluation')
            
        else:
            ax[0].plot(data.loc[tag_split:end, 'Value'], 
                       linewidth=0.5, 
                       alpha=0.8, 
                       label=f'{tag_name} - Evaluation')
    else:
        ax[0].plot(data['Value'], linewidth=0.5, alpha=0.8, label=tag_name)
    ax[0].set_xlim(start, end)
    
    # Plot a daily rolling average:
    if plot_rolling_avg == True:
        daily_rolling_average = data['Value'].rolling(window=60*24).mean()
        ax[0].plot(data.index, 
                   daily_rolling_average, 
                   alpha=0.5, 
                   color='white', 
                   linewidth=3)
        ax[0].plot(data.index, 
                   daily_rolling_average, 
                   label='Daily rolling leverage', 
                   color='tab:red', 
                   linewidth=1)

    # Configure custom grid:
    ax_id = 0
    if custom_grid:
        date_format = DateFormatter("%Y-%m")
        major_ticks = np.arange(start, end, 3, dtype='datetime64[M]')
        minor_ticks = np.arange(start, end, 1, dtype='datetime64[M]')
        ax[ax_id].xaxis.set_major_formatter(date_format)
        ax[ax_id].set_xticks(major_ticks)
        ax[ax_id].set_xticks(minor_ticks, minor=True)
        ax[ax_id].grid(which='minor', axis='x', alpha=0.8)
        ax[ax_id].grid(which='major', axis='x', alpha=1.0, linewidth=2)
        ax[ax_id].xaxis.set_tick_params(rotation=30)

    # Add the labels on a second plot:
    if labels_df is not None:
        ax_id += 1
        label_index = pd.date_range(
            start=data.index.min(), 
            end=data.index.max(), 
            freq='1min'
        )
        label_data = pd.DataFrame(index=label_index)
        label_data.loc[:, 'Label'] = 0.0

        for index, row in labels_df.iterrows():
            event_start = row['start']
            event_end = row['end']
            label_data.loc[event_start:event_end, 'Label'] = 1.0
            
        ax[ax_id].plot(label_data['Label'], color='tab:green', linewidth=0.5)
        ax[ax_id].set_xlim(start, end)
        ax[ax_id].fill_between(label_index, 
                               y1=label_data['Label'], 
                               y2=0, 
                               alpha=0.1, 
                               color='tab:green', 
                               label='Real anomaly range (label)')
        ax[ax_id].axes.get_xaxis().set_ticks([])
        ax[ax_id].axes.get_yaxis().set_ticks([])
        ax[ax_id].set_xlabel('Anomaly ranges (labels)', fontsize=12)
        
    # Add the labels (anomaly range) on a 
    # third plot located below the main ones:
    if predictions is not None:
        pred_index = pd.date_range(
            start=data.index.min(), 
            end=data.index.max(), 
            freq='1min')
        pred_data = pd.DataFrame(index=pred_index)
        
        if type(predictions) == pd.core.frame.DataFrame:
            ax_id += 1
            pred_data.loc[:, 'prediction'] = 0.0

            for index, row in predictions.iterrows():
                event_start = row['start']
                event_end = row['end']
                pred_data.loc[event_start:event_end, 'prediction'] = 1.0

            ax[ax_id].plot(pred_data['prediction'], 
                           color='tab:red',
                           linewidth=0.5)
            ax[ax_id].set_xlim(start, end)
            ax[ax_id].fill_between(pred_index, 
                                   y1=pred_data['prediction'],
                                   y2=0, 
                                   alpha=0.1, 
                                   color='tab:red')
            ax[ax_id].axes.get_xaxis().set_ticks([])
            ax[ax_id].axes.get_yaxis().set_ticks([])
            ax[ax_id].set_xlabel('Anomaly ranges (Prediction)', fontsize=12)
            
        elif type(predictions) == list:
            for prediction_index, p in enumerate(predictions):
                ax_id += 1
                pred_data.loc[:, 'prediction'] = 0.0

                for index, row in p.iterrows():
                    event_start = row['start']
                    event_end = row['end']
                    pred_data.loc[event_start:event_end, 'prediction'] = 1.0
                    
                if shutdown_ranges_df is not None:
                    for index, row in shutdown_ranges_df.iterrows():
                        shutdown_start = row['start']
                        shutdown_end = row['end']
                        pred_data.loc[shutdown_start:shutdown_end, 'prediction'] = 0.0
                
                ax[ax_id].plot(pred_data['prediction'], 
                               color='tab:red',
                               linewidth=0.5)
                ax[ax_id].set_xlim(start, end)
                ax[ax_id].fill_between(pred_index,
                                       y1=pred_data['prediction'],
                                       y2=0, 
                                       alpha=0.1, 
                                       color='tab:red')
                ax[ax_id].axes.get_xaxis().set_ticks([])
                ax[ax_id].axes.get_yaxis().set_ticks([])
                ax[ax_id].set_xlabel(
                    prediction_titles[prediction_index], 
                    fontsize=12
                )
        
    # Show the plot with a legend:
    ax[0].legend(fontsize=10, loc='upper right', framealpha=0.4)
        
    return fig, ax