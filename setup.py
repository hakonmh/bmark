from setuptools import setup, find_packages
import os

current_folder = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(current_folder, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='bmark-py',
    version='0.0.2',
    description='Benchmarking tool',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url=r'https://github.com/hakonmh/bmark',
    author='Håkon Magne Holmen',
    author_email='haakonholmen@hotmail.com',
    license='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ],
    python_requires='>=3.5',
    packages=find_packages(exclude=['tests', 'dev']),
    install_requires=[
        'pandas',
        'ipython'
        'prettytable>=3.5.0',
        'bokeh>=3.0.0',
    ],
)
