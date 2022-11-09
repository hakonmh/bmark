import abc
import time
import timeit
from IPython.core.magics.execution import TimeitResult
from bmark.result import BenchmarkResult


class Benched(abc.ABC):

    def __init__(self):
        """A base class for the things you want benchmarked"""
        if not hasattr(self, 'name'):
            self.name = self.__class__.__name__

    @abc.abstractmethod
    def run(self):
        """Code to be benchmarked"""
        pass

    def __enter__(self):
        """Called before each loop in the timer"""
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        """Called after each loop in the timer"""
        pass

    def setup(self):
        """Setup for the entire duration of the timer"""
        pass

    def teardown(self):
        """Final teardown after all the timings are done"""
        pass


class Benchmark:

    def __init__(self, items=None):
        """Initialize benchmark

        You can provide items to be benchmarked either by passing them here
        as a list or by decorating them with a Benchmark instance.

        Parameters
        ----------
        items : list[Benched], optional
            A list of items to be Benched, by default None
        """
        if items:
            self.funcs = list(items)
        else:
            self.funcs = list()
        self._setup_time = 0
        self._teardown_time = 0

    def __call__(self, action=''):
        def _decorator(cls_):
            if action == 'setup':
                self._setup = cls_
                return cls_
            elif action == 'teardown':
                self._teardown = cls_
                return cls_
            else:
                def closure(*args, **kwargs):
                    nonlocal cls_
                    func = cls_(*args, **kwargs)
                    self.funcs.append(func)
                    return func
                return closure
        return _decorator

    def run(self, header="Results", r=7, n=None, sort=False, quiet=False):
        """Run the benchmark and reset

        Parameters
        ----------
        header : str, optional
            Results table Header, by default "Results"
        r : int, optional
            Number of repeats, each consisting of 'n' loops, and take the best
            result.
        n : int, optional
            How many times to execute each function. If n is not provided, it
            will determined for each function so as to get sufficient accuracy.
        sort : bool, optional
            Orders table by best time if True, by default False
        quiet : bool, optional
            Do not print results if True, by default False.

        Returns
        -------
        BenchmarkResult
            Returns a results object that can be used to inspect, store, and
            plot the result.
        """
        _can_run_benchmark(self.funcs)
        start = time.time()
        timings = []
        for func in self.funcs:
            func.setup()
            result = _bench_it(func, r, n)
            timings.append(result)
            func.teardown()
        self.funcs = list()
        total_runtime = time.time() - start
        total_runtime = total_runtime + self._setup_time + self._teardown_time
        if sort:
            timings.sort(key=lambda t: t.best)

        results = BenchmarkResult(header, timings, total_runtime)

        if not quiet:
            print(results)
        return results

    def setup(self, *args, **kwargs):
        start = time.time()
        self._setup(*args, **kwargs)
        end = time.time()
        self._setup_time = end - start

    def teardown(self, *args, **kwargs):
        start = time.time()
        self._teardown(*args, **kwargs)
        end = time.time()
        self._teardown_time = end - start


def _can_run_benchmark(funcs):
    if len(funcs) == 0:
        raise RuntimeError('No functions to benchmark')
    funcs_are_benched = all(isinstance(f, Benched) for f in funcs)
    if not funcs_are_benched:
        raise TypeError("Functions must subclass bmark.Benched")


def _bench_it(func, repeat, number):
    name = func.name
    if not number:
        number = _determine_number(func)
    all_runs = _repeat(func, repeat, number)
    best = min(all_runs) / number
    worst = max(all_runs) / number
    result = TimeitResult(number, repeat, best, worst, all_runs, compile_time=0, precision=3)
    result.name = name
    return result


def _determine_number(func):
    # determine number so that 0.2 <= total time < 2.0
    stmt = "with func as f:\n    f.run()"
    timer = timeit.Timer(stmt, globals=locals())
    number = timer.autorange()[0]
    return number


def _repeat(func, repeat, number):
    all_runs = []
    for _ in range(repeat):
        runtime = 0
        runtime = _timeit(func, number)
        all_runs.append(runtime)
    return all_runs


def _timeit(func, number):
    runtime = 0
    for _ in range(number):
        with func as f:
            start = time.time()
            f.run()
            end = time.time()
        runtime += (end - start)
    return runtime
