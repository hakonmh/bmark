# Bmark

Python benchmarking tool.

It's mostly used for benchmarking [FeatherStore](https://github.com/hakonmh/featherstore),
but can be used to benchmark any Python code.

## Installation

Bmark is available on [PyPI](https://pypi.org/project/bmark-py/):

```console
python -m pip install bmark-py
```

## Basic usage

First let's setup a class to be benchmarked, all methods except `run()` are
optional.

```python
import os
import bmark
import pandas as pd

read_bench = bmark.Benchmark()

@read_bench()  # Remember the parantheses
class read_csv(bmark.Benched):

    def __init__(self, shape, engine):
        self.name = f'pd.read_csv(engine={engine})'
        self.rows, self.cols = shape
        self._path = '_benchmarks'
        self.file_path = os.path.join(self._path, 'table.csv')
        self.engine = engine
        super().__init__()

    def run(self):
        """Code to be benchmarked"""
        pd.read_csv(self.file_path, engine=self.engine)

    def setup(self):
        """Setup for the entire duration of the timer"""
        data = {f'c{i}': range(self.rows) for i in range(self.cols)}
        self.df = pd.DataFrame(data)
        if not os.path.exists(self._path):
            os.makedirs(self._path)

    def teardown(self):
        """Final teardown after all the timings are done"""
        os.rmdir(self._path)

    def __enter__(self):
        """Called before each loop in the timer"""
        self.df.to_csv(self.file_path)
        return self  # Important

    def __exit__(self, *args):
        """Called after each loop in the timer"""
        os.remove(self.file_path)
```

We initialize a benchmark with `bmark.Benchmark()`. We can the register classes
to be benchmarked by using the `Benchmark` object as a decorator (as show above).

Each time we initialize a registered class it'll get added as an item to be
benchmarked:

```python
shape = (100_000, 10)
read_csv(shape, engine='c')
read_csv(shape, engine='python')
read_csv(shape, engine='pyarrow')

header = f'Read CSV benchmark {shape}'
read_bench.run(header, r=5, n=5, sort=True)

>>                 Read CSV benchmark (100000, 10)
 Name                        │ Hits │    Best │   Worst │ Comparison
─────────────────────────────┼──────┼─────────┼─────────┼────────────
 pd.read_csv(engine=pyarrow) │   25 │ 16.2 ms │ 20.5 ms │      1.00x
 pd.read_csv(engine=c)       │   25 │ 74.2 ms │  106 ms │      4.58x
 pd.read_csv(engine=python)  │   25 │  803 ms │  862 ms │     49.54x

Runtimes: total 46.5 s, benchmark 23.4 s, other 23.2 s
```

We can also populate benchmarks by passing all the objects we want benchmarked
in a list directly into the `bmark.Benchmark` constructor:

```python
shape = (500_000, 20)
items = (
    read_csv(shape, engine='c'),
    read_csv(shape, engine='python'),
    read_csv(shape, engine='pyarrow')
)
header = f'Read CSV benchmark {shape}'
bmark.Benchmark(items).run(header, r=1, n=5, sort=True)

>>           Read CSV benchmark (500000, 20)
 Name                        │ Hits │   Time │ Comparison
─────────────────────────────┼──────┼────────┼────────────
 pd.read_csv(engine=pyarrow) │    5 │ 112 ms │      1.00x
 pd.read_csv(engine=c)       │    5 │ 655 ms │      5.85x
 pd.read_csv(engine=python)  │    5 │ 7.49 s │     66.98x

Runtimes: total 1min 21s, benchmark 41.3 s, other 40.2 s
```

For a more in-depth example, see the FeatherStore
[benchmarking suite](https://github.com/hakonmh/featherstore/tree/master/benchmarks).
