import os
import json
from datetime import datetime

from IPython.core.magics.execution import _format_time
import pandas as pd

from bokeh import plotting
from bokeh.models import ColumnDataSource, CrosshairTool, Span, HoverTool, Select
from bokeh.layouts import column
from bokeh.server.server import Server


def plot_log(path):
    """Plots timeseries chart of benchmark log(s) to see benchmark results over time.

    You can choose to plot either:

    * a single logfile by providing the path to a single log file
    * multiple logfiles by providing the path to a folder of logfiles, giving
    you a chart with a dropdown selector to switch between results

    Parameters
    ----------
    path : str
        path to logfile or directory of logfiles
    """
    if os.path.isdir(path):
        dfs = {}
        for bench_name in os.listdir(path):
            header = bench_name.rstrip('.log')
            file_path = os.path.join(path, bench_name)
            data = read_log(file_path)
            df = pd.DataFrame.from_records(data[1:], columns=data[0], index='date')
            df = df.sort_index()
            dfs[header] = df
        plot_multiple(dfs)
    else:
        if '.log' in path:
            header = os.path.split(path)[-1].rstrip('.log')
        else:
            header = os.path.split(path)[-1]
            path += '.log'
        data = read_log(path)
        df = pd.DataFrame.from_records(data[1:], columns=data[0], index='date')
        plot_single(header, df)


def read_log(path):
    vaules = []
    with open(path, 'r') as f:
        header = True
        for line in f.readlines():
            val = json.loads(line)
            if header:
                header = False
            else:
                val[0] = datetime.strptime(val[0], "%Y-%m-%d %H:%M:%S.%f")
            vaules.append(val)
    return vaules


def plot_single(header, df):
    header = header.rstrip('.log')
    fig = _make_fig(header)
    line, _ = _plot_shaded_line(fig, df)
    _rescale_fig(fig, line)
    _add_crosshair(fig)
    _add_hover(fig, line)
    plotting.show(fig)


def plot_multiple(dfs):
    app = _PlotMulti(dfs)
    server = Server({'/': app}, num_procs=1)
    server.start()
    server.io_loop.add_callback(server.show, "/")
    server.io_loop.start()


class _PlotMulti:

    def __init__(self, dfs) -> None:
        self.dfs = dfs

    def __call__(self, doc):
        keys = list(self.dfs.keys())
        fig = _make_fig(keys[0])
        doc.theme = 'dark_minimal'

        lines = dict()
        for key in self.dfs:
            lines[key] = _plot_shaded_line(fig, self.dfs[key])
        line, fill = lines[keys[0]]
        _set_all_lines_invisible(lines)
        _set_line_visible(line, fill)
        _rescale_fig(fig, line)

        _add_crosshair(fig)
        _add_hover(fig, lines[keys[0]][0])
        selector = _add_selector(fig, lines)
        layout = column(fig, selector, sizing_mode='stretch_both')

        doc.add_root(layout)


def _make_fig(header):
    fig = plotting.figure(title=header, sizing_mode="stretch_width",
                          x_axis_label='Date', x_axis_type="datetime",
                          y_axis_label='Benchmark result', y_axis_type="datetime",
                          x_range=(0, 0), y_range=(0, 0),  # Disable auto-ranging
                          )
    plotting.curdoc().theme = 'dark_minimal'
    return fig


def _plot_shaded_line(fig, df):
    plot_source = ColumnDataSource(data=dict(date=df.index,
                                             timing=df["timing"] * 10e2,
                                             _timing_formatted=df["timing"].apply(_format_time),
                                             tag=df['tag']))
    line = fig.line('date', 'timing', source=plot_source, line_width=2, line_join='bevel', color='darkgreen')
    fill = fig.varea('date', y1=0, y2='timing', source=plot_source, level='underlay',
                     fill_alpha=0.20, fill_color='darkgreen')
    return line, fill


def _add_crosshair(fig):
    width = Span(dimension="width", line_dash="dashed", line_width=1, line_color='white', line_alpha=0.8)
    height = Span(dimension="height", line_dash="dashed", line_width=1, line_color='white', line_alpha=0.8)
    fig.add_tools(CrosshairTool(overlay=[width, height]))


def _add_hover(fig, line):
    hover = HoverTool(
        tooltips=[
            ("Date", '@date{%Y-%m-%d %T}'),
            ("Result", '@_timing_formatted'),
            ('Tag', '@tag')
        ],
        formatters={'@date': 'datetime'},
        renderers=[line],
        mode='vline',
        line_policy='nearest',
        point_policy='snap_to_data',
        attachment='above')
    fig.add_tools(hover)


def _set_all_lines_invisible(lines):
    for key in lines:
        line, fill = lines[key]
        line.visible = False
        fill.visible = False


def _set_line_visible(line, fill):
    line.visible = True
    fill.visible = True


def _rescale_fig(fig, line):
    df = line.data_source.to_df()
    fig.x_range.update(start=df.index[0], end=df.index[-1])
    fig.y_range.update(start=0, end=df['timing'].max() * 1.2)


def _add_selector(fig, lines):
    def callback(attr, old, new):
        nonlocal lines, fig
        line, fill = lines[new]

        _set_all_lines_invisible(lines)
        _rescale_fig(fig, line)
        _set_line_visible(line, fill)

        fig.tools.pop()  # Drop hover
        _add_hover(fig, line)

    keys = list(lines.keys())
    selector = Select(title="Benchmarks", options=keys, value=keys[0], css_classes=['selector'])
    selector.on_change('value', callback)
    return selector
