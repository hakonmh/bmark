def plot(path, by='date'):
    """
    path=[*logfiles]: gives multiple charts on same canvas
    by=name: Barchart, Y-axis is ms scaled, X-axis is name
    by=date: Line chart, Y-axis is ms scaled, X-axis is date
    """
    data = _read_log(path)
    if by == 'date':
        _plot_by_date(data)
    elif by == 'name':
        _plot_by_name(data)


def _read_log(path):
    raise NotImplementedError


def _plot_by_date(data):
    raise NotImplementedError


def _plot_by_name(data):
    raise NotImplementedError
