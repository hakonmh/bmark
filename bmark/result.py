import datetime
import os
import json
from prettytable import PrettyTable
from IPython.core.magics.execution import _format_time
from bmark.plot import plot_bar


class BenchmarkResult:

    def __init__(self, header, timings, total_runtime):
        self.timings = timings
        self._now = datetime.datetime.now()
        self._str = _BenchmarkResultString(header, timings, total_runtime)
        self._header = header

    def keys(self):
        return [t.name for t in self.timings]

    def items(self):
        return {t.name: t for t in self.timings}

    def values(self):
        return [v.average for v in self.timings]

    def __getitem__(self, key):
        index = self.keys().index(key)
        return self.timings[index].timings

    def __str__(self):
        return str(self._str)

    def log(self, dir_path, tag=''):
        """Writes the benchmark results to logfiles.

        Parameters
        ----------
        dir_path : str
            Path to the directory you want to store the file
        tag : str, optional
            An optional tag for the benchmark result, like a version number or
            similar, by default ''
        """
        for timing in self.timings:
            file_path = os.path.join(dir_path, timing.name) + '.log'

            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
            if not os.path.exists(file_path):
                with open(file_path, 'w') as f:
                    json.dump(('date', 'tag', 'timing'), f, default=str)
                    f.write('\n')
            with open(file_path, 'a') as f:
                json.dump((self._now, tag, timing.best), f, default=str)
                f.write('\n')

    def plot(self):
        """Plots a barchart of the items benchmarked"""
        plot_bar(self._header, self.timings)


class _BenchmarkResultString:

    def __init__(self, header, timings, total_runtime):
        table = self._make_table(header, repeats=timings[0].repeat)
        self.data = self._populate_table(table, timings)
        footer = self._format_footer(timings, total_runtime)
        self.str = f"{self.data}\n\n{footer}\n"

    def _format_footer(self, timings, total_runtime):
        bench_time = sum(sum(t.all_runs) for t in timings)
        setup_and_teardown_time = total_runtime - bench_time
        total_runtime = _format_time(total_runtime)
        bench_time = _format_time(bench_time)
        setup_and_teardown_time = _format_time(setup_and_teardown_time)
        footer = f"\033[1mRuntimes: total {total_runtime}, benchmark "\
            f"{bench_time}, other {setup_and_teardown_time}\033[0m"
        return footer

    def __str__(self):
        return self.str

    def _make_table(self, header, repeats):
        table = PrettyTable(align='r', border=False, preserve_internal_border=True,
                            junction_char='┼', vertical_char='│', horizontal_char='─')
        table.title = f'\033[1m{header}\033[0m'  # Bold text
        if repeats == 1:
            table.field_names = ["Name", "Hits", "Time", "Comparison"]
        else:
            table.field_names = ["Name", "Hits", "Best", "Worst", "Comparison"]
        table.align['Name'] = 'l'
        return table

    def _populate_table(self, table, timings):
        rows = self._format_rows(timings)
        table.add_rows(rows)
        return table

    def _format_rows(self, timings):
        repeats = timings[0].repeat
        rows = []
        fastest = min(t.best for t in timings)

        for result in timings:
            name = result.name
            hits = result.loops * result.repeat
            time = _format_time(result.best)
            comparison = self._format_comparison(result.best, vs=fastest)
            worst = _format_time(result.worst)
            if repeats == 1:
                row = [name, hits, time, comparison]
            else:
                row = [name, hits, time, worst, comparison]

            rows.append(row)
        return rows

    def _format_comparison(self, x, vs):
        return format(x / vs, '0.2f') + 'x'
