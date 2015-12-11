from distutils.core import setup

setup(
    name='pyrules',
    version='0.2',
    packages=['pyrules2', 'pyrules2.googlemaps'],
    package_dir={'': 'src'},
    url='https://github.com/mr-niels-christensen/pyrules',
    license='MIT',
    author='Niels Christensen',
    author_email='nhc@mayacs.com',
    description='pyrules is a pure-Python library for implementing discrete rule-based models.  ',
    install_requires=[
        'frozendict==0.5',
        'googlemaps==2.4',
    ]
)
