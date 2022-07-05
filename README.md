# SQLAlchemy Wrapper

Wrapper for SQLAlchemy developed by the Materials Informatics team at Fraunhofer IWM. Tested with SQLite and Postgresql backends.

## Requirements

The SQLAlchemy wrapper is built on top of the [OSP core](https://github.com/simphony/osp-core) package.
The following table describes the version compatibility between these two packages.

| __SQLAlchemy wrapper__ |        __OSP core__        |
|:----------------------:|:--------------------------:|
|         1.0.0          |         3.1.x-beta         |
|         2.0.0          |         3.2.x-beta         |
|       2.1.[0-1]        |       3.3.[1-8]-beta       |
|         2.1.2          |         3.4.X-beta         |
|         2.2.0          |         3.5.X-beta         |
|         2.2.1          |         3.5.X-beta         |
|         2.2.X          | \>= 3.5.0-beta, < 4.0.0rc0 |

The releases of OSP core are available [here](https://github.com/simphony/osp-core/releases). Releases of OSP-core from version 3.7.0 are also available on [PyPI](https://pypi.org/project/osp-core/).

#### Additional required packages
- sqlalchemy
- psycopg2

The easiest way to run an sqlalchemy server is to use docker:
```sh
docker run -d -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=123-postgres -e POSTGRES_DB=postgres -e POSTGRES_HOST=db -p 5432:5432 --name postgres --restart=always postgres:11.7
```

## Installation

The package requires python 3 (tested for 3.7), installation is based on setuptools.

```py
# build and install
pip install .
```

or

```py
# build for in-place development
pip install -e .
```

## Testing

Testing is included in setuptools:

```py
# run tests automatically
python3 setup.py test
```

[//]: # (## Documentation)

[//]: # (TODO)

## Directory structure

- sqlalchemy_wrapper -- sqlite wrapper files.
- tests -- unittesting of the code.
- doc -- documentation related files.
- examples - examples of usage.
