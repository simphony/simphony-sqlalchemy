[![pipeline status](https://gitlab.cc-asp.fraunhofer.de/simphony/wrappers/sqlalchemy-wrapper/badges/master/pipeline.svg)](https://gitlab.cc-asp.fraunhofer.de/simphony/wrappers/sqlalchemy-wrapper/commits/master)
[![coverage report](https://gitlab.cc-asp.fraunhofer.de/simphony/wrappers/sqlalchemy-wrapper/badges/master/coverage.svg)](https://gitlab.cc-asp.fraunhofer.de/simphony/wrappers/sqlalchemy-wrapper/commits/master)

# SQLAlchemy Wrapper

Wrapper for SQLAlchemy developed by the SimPhoNy group at Fraunhofer IWM.

Copyright (c) 2014-2019, Adham Hashibon and Materials Informatics Team at Fraunhofer IWM.
All rights reserved.
Redistribution and use are limited to the scope agreed with the end user.
No parts of this software may be used outside of this context.
No redistribution is allowed without explicit written permission.

## Requirements

The SQLAlchemy wrapper is built on top of the [OSP core](https://gitlab.cc-asp.fraunhofer.de/simphony/osp-core) package.
The following table describes the version compatability between these two packages.

| __SQLAlchemy wrapper__ | __OSP core__ |
|   :---:   |   :---:  |
|   1.0.0   |   3.1.x-beta  |
|   2.0.0   |   3.2.x-beta  |

The releases of OSP core are available [here](https://gitlab.cc-asp.fraunhofer.de/simphony/osp-core/-/releases).

##### Additional required packages
- sqlalchemy
- psycopg2

## Installation

The package requires python 3 (tested for 3.6), installation is based on setuptools.

```py
# build and install
python setup.py install
```

or

```py
# build for in-place development
python3 setup.py develop
```

## Testing

Testing is included in setuptools:

```py
# run tests automatically
python3 setup.py test
```

## Documentation

TODO

## Directory structure

- sqlalchemy_wrapper -- sqlite wrapper files.
- tests -- unittesting of the code.
- doc -- documentation related files.
- examples - examples of usage.
