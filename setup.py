from setuptools import setup, find_packages

__packagename__='statsanalyzer'

with open('requirements.txt') as f:
    reqs = f.read().splitlines()

print(reqs)

setup(
    name = 'statsanalyzer',
    version='1.0',
    description='A Python tool for capturing Postgres performance metrics',
    url='https://github.com/samimseih/statsanalyzer',
    author='Sami Imseih',
    author_email='samimseih@gmail.com',
    license='MIT',
    python_requires='>=3.7,<3.9',
    install_requires=reqs,
    packages=['statsanalyzer'],
    package_data={
        'statsanalyzer': ['*']
   }
)
