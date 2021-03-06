'''
Created on 22.12.2018

@author: prudnik
'''

from setuptools import setup, find_packages

requires = [
    'flask',
    'flask-sqlalchemy',
    'psycopg2',
]

setup(
    name='flask_todo',
    version='0.0',
    description='A To-Do List built with Flask',
    author='prudnik',
    author_email='peterrudnik@googlemail.com',
    keywords='web flask',
    packages=find_packages(),
    include_package_data=True,
    install_requires=requires
)
