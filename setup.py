"""Install the wrapper."""

from setuptools import setup, find_packages

from packageinfo import VERSION, NAME

# Read description
with open('README.md', 'r') as readme:
    README_TEXT = readme.read()


# main setup configuration class
setup(
    name=NAME,
    version=VERSION,
    author='Material Informatics Team, Fraunhofer IWM.',
    url='www.simphony-project.eu',
    description='The SQLAlchemy wrapper for SimPhoNy',
    keywords='simphony, cuds, Fraunhofer IWM, sqlalchemy',
    long_description=README_TEXT,
    install_requires=[
        'osp-core>=3.0.0',
        'sqlalchemy',
        'psycopg2-binary'
    ],
    tests_require=[
        "unittest2",
    ],
    packages=find_packages(),
    test_suite='tests',
    entry_points={
        'wrappers': 'simphony_sqlalchemy = osp.wrappers.'
                    'sqlalchemy_wrapper_session:SqlAlchemyWrapperSession'
    }
)
