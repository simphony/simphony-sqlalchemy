"""Test the Sqlite Wrapper with the CITY ontology."""

import os
import uuid
import unittest2 as unittest
import sqlalchemy
from osp.wrappers.sqlalchemy import SqlAlchemySession

try:
    from osp.core.namespaces import city
except ImportError:
    from osp.core.ontology import Parser
    from osp.core.namespaces import _namespace_registry
    Parser(_namespace_registry._graph).parse("city")
    _namespace_registry.update_namespaces()
    city = _namespace_registry.city

USER = os.environ.get("POSTGRES_USER") or "postgres"
PWD = os.environ.get("POSTGRES_PASSWORD") or "123-postgres"
DB = os.environ.get("POSTGRES_DB") or "postgres"
HOST = os.environ.get("POSTGRES_HOST") or "127.0.0.1"
PORT = 5432
URL = "postgresql://%s:%s@%s:%s/%s" % (USER, PWD, HOST, PORT, DB)


CUDS_TABLE = SqlAlchemySession.CUDS_TABLE
ENTITIES_TABLE = SqlAlchemySession.ENTITIES_TABLE
TYPES_TABLE = SqlAlchemySession.TYPES_TABLE
NAMESPACES_TABLE = SqlAlchemySession.NAMESPACES_TABLE
RELATIONSHIP_TABLE = SqlAlchemySession.RELATIONSHIP_TABLE
DATA_TABLE_PREFIX = SqlAlchemySession.DATA_TABLE_PREFIX


def data_tbl(suffix):
    """Prepend data table prefix."""
    return DATA_TABLE_PREFIX + suffix


class TestSqliteCityPostgres(unittest.TestCase):
    """Test the postgres wrapper with the city ontology."""

    def tearDown(self):
        """Remove the database file."""
        engine = sqlalchemy.create_engine(URL)
        with engine.connect() as connection:
            metadata = sqlalchemy.MetaData(connection)
            metadata.reflect(engine)
            metadata.drop_all()

    def test_insert(self):
        """Test inserting in the postgres table."""
        c = city.City(name="Freiburg")
        p1 = city.Citizen(name="Peter")
        p2 = city.Citizen(name="Georg")
        c.add(p1, p2, rel=city.hasInhabitant)

        with SqlAlchemySession(URL) as session:
            wrapper = city.CityWrapper(session=session)
            wrapper.add(c)
            wrapper.session.commit()

        check_state(self, c, p1, p2)

    def test_update(self):
        """Test updating the postgres table."""
        c = city.City(name="Paris")
        p1 = city.Citizen(name="Peter")
        c.add(p1, rel=city.hasInhabitant)

        with SqlAlchemySession(URL) as session:
            wrapper = city.CityWrapper(session=session)
            cw = wrapper.add(c)
            session.commit()

            p2 = city.Citizen(name="Georg")
            cw.add(p2, rel=city.hasInhabitant)
            cw.name = "Freiburg"
            session.commit()

        check_state(self, c, p1, p2)

    def test_delete(self):
        """Test to delete cuds_objects from the postgres table."""
        c = city.City(name="Freiburg")
        p1 = city.Citizen(name="Peter")
        p2 = city.Citizen(name="Georg")
        p3 = city.Citizen(name="Hans")
        c.add(p1, p2, p3, rel=city.hasInhabitant)

        with SqlAlchemySession(URL) as session:
            wrapper = city.CityWrapper(session=session)
            cw = wrapper.add(c)
            session.commit()

            cw.remove(p3.uid)
            session._notify_read(wrapper)
            session.prune()
            session.commit()

        check_state(self, c, p1, p2)

    def test_init(self):
        """Test of first level of children are loaded automatically."""
        c = city.City(name="Freiburg")
        p1 = city.Citizen(name="Peter")
        p2 = city.Citizen(name="Anna")
        p3 = city.Citizen(name="Julia")
        c.add(p1, p2, p3, rel=city.hasInhabitant)
        p1.add(p3, rel=city.hasChild)
        p2.add(p3, rel=city.hasChild)

        with SqlAlchemySession(URL) as session:
            wrapper = city.CityWrapper(session=session)
            wrapper.add(c)
            session.commit()

        with SqlAlchemySession(URL) as session:
            wrapper = city.CityWrapper(session=session)
            self.assertEqual(set(session._registry.keys()),
                             {c.uid, wrapper.uid})
            self.assertEqual(wrapper.get(c.uid).name, "Freiburg")
            self.assertEqual(
                session._registry.get(c.uid)._neighbors[city.hasInhabitant],
                {p1.uid: p1.oclasses, p2.uid: p2.oclasses,
                 p3.uid: p3.oclasses})
            self.assertEqual(
                session._registry.get(c.uid)._neighbors[city.isPartOf],
                {wrapper.uid: wrapper.oclasses})

    def test_load_missing(self):
        """Test if missing objects are loaded automatically."""
        c = city.City(name="Freiburg")
        p1 = city.Citizen(name="Peter")
        p2 = city.Citizen(name="Anna")
        p3 = city.Citizen(name="Julia")
        c.add(p1, p2, p3, rel=city.hasInhabitant)
        p1.add(p3, rel=city.hasChild)
        p2.add(p3, rel=city.hasChild)

        with SqlAlchemySession(URL) as session:
            wrapper = city.CityWrapper(session=session)
            wrapper.add(c)
            session.commit()

        with SqlAlchemySession(URL) as session:
            wrapper = city.CityWrapper(session=session)
            self.assertEqual(set(session._registry.keys()),
                             {c.uid, wrapper.uid})
            cw = wrapper.get(c.uid)
            p1w = cw.get(p1.uid)
            p2w = cw.get(p2.uid)
            p3w = p1w.get(p3.uid)
            self.assertEqual(
                set(session._registry.keys()),
                {c.uid, wrapper.uid, p1.uid, p2.uid, p3.uid})
            self.assertEqual(p1w.name, "Peter")
            self.assertEqual(p2w.name, "Anna")
            self.assertEqual(p3w.name, "Julia")
            self.assertEqual(
                p3w._neighbors[city.isChildOf],
                {p1.uid: p1.oclasses, p2.uid: p2.oclasses}
            )
            self.assertEqual(
                p2w._neighbors[city.hasChild],
                {p3.uid: p3.oclasses}
            )
            self.assertEqual(
                p2w._neighbors[city.INVERSE_OF_hasInhabitant],
                {c.uid: c.oclasses}
            )

    def test_load_by_oclass(self):
        """Test loading by oclass."""
        c = city.City(name="Freiburg")
        p1 = city.Citizen(name="Peter")
        p2 = city.Citizen(name="Anna")
        p3 = city.Citizen(name="Julia")
        c.add(p1, p2, p3, rel=city.hasInhabitant)
        p1.add(p3, rel=city.hasChild)
        p2.add(p3, rel=city.hasChild)

        with SqlAlchemySession(URL) as session:
            wrapper = city.CityWrapper(session=session)
            wrapper.add(c)
            session.commit()

        with SqlAlchemySession(URL) as session:
            wrapper = city.CityWrapper(session=session)
            cs = wrapper.get(c.uid)
            r = session.load_by_oclass(city.City)
            self.assertIs(next(r), cs)
            r = session.load_by_oclass(city.Citizen)
            self.assertEqual(set(r), {p1, p2, p3})
            r = session.load_by_oclass(city.Person)
            self.assertEqual(set(r), {p1, p2, p3})

        with SqlAlchemySession(URL) as session:
            wrapper = city.CityWrapper(session=session)
            cs = wrapper.get(c.uid)
            r = session.load_by_oclass(city.Street)
            self.assertRaises(StopIteration, next, r)

    def test_expiring(self):
        """Test expring CUDS objects."""
        c = city.City(name="Freiburg")
        p1 = city.Citizen(name="Peter")
        p2 = city.Citizen(name="Anna")
        p3 = city.Citizen(name="Julia")
        c.add(p1, p2, p3, rel=city.hasInhabitant)
        p1.add(p3, rel=city.hasChild)
        p2.add(p3, rel=city.hasChild)

        with SqlAlchemySession(URL) as session:
            wrapper = city.CityWrapper(session=session)
            cw = wrapper.add(c)
            p1w, p2w, p3w = cw.get(p1.uid, p2.uid, p3.uid)
            session.commit()

            # p1w is no longer expired after the following assert
            self.assertEqual(p1w.name, "Peter")
            self.assertEqual(p2w.name, "Anna")

            update_db(DB, c, p1, p2, p3)

            self.assertEqual(p2w.name, "Anna")
            self.assertEqual(cw.name, "Paris")  # expires outdated neighbor p2w
            self.assertEqual(p2w.name, "Jacob")
            self.assertEqual(p1w.name, "Peter")
            session.expire_all()
            self.assertEqual(p1w.name, "Maria")
            self.assertEqual(set(cw.get()), {p1w})
            self.assertEqual(p2w.get(), list())
            self.assertFalse(hasattr(p3w, "name"))
            self.assertNotIn(p3w.uid, session._registry)

    def test_refresh(self):
        """Test refreshing CUDS objects."""
        c = city.City(name="Freiburg")
        p1 = city.Citizen(name="Peter")
        p2 = city.Citizen(name="Anna")
        p3 = city.Citizen(name="Julia")
        c.add(p1, p2, p3, rel=city.hasInhabitant)
        p1.add(p3, rel=city.hasChild)
        p2.add(p3, rel=city.hasChild)

        with SqlAlchemySession(URL) as session:
            wrapper = city.CityWrapper(session=session)
            cw = wrapper.add(c)
            p1w, p2w, p3w = cw.get(p1.uid, p2.uid, p3.uid)
            session.commit()

            self.assertEqual(cw.name, "Freiburg")
            self.assertEqual(p1w.name, "Peter")
            self.assertEqual(p2w.name, "Anna")
            self.assertEqual(p3w.name, "Julia")
            self.assertEqual(session._expired, {wrapper.uid})

            update_db(DB, c, p1, p2, p3)

            session.refresh(cw, p1w, p2w, p3w)
            self.assertEqual(cw.name, "Paris")
            self.assertEqual(p1w.name, "Maria")
            self.assertEqual(set(cw.get()), {p1w})
            self.assertEqual(p2w.get(), list())
            self.assertFalse(hasattr(p3w, "name"))
            self.assertNotIn(p3w.uid, session._registry)

    def test_clear_database(self):
        """Test clearing the database."""
        # db is empty (no error occurs)
        with SqlAlchemySession(URL) as session:
            wrapper = city.CityWrapper(session=session)
            session._clear_database()
        with SqlAlchemySession(URL) as session:
            wrapper = city.CityWrapper(session=session)
            wrapper.session.commit()
            session._clear_database()

        # db is not empty
        c = city.City(name="Freiburg")
        p1 = city.Citizen(name="Peter")
        p2 = city.Citizen(name="Anna")
        p3 = city.Citizen(name="Julia")
        c.add(p1, p2, p3, rel=city.hasInhabitant)
        p1.add(p3, rel=city.hasChild)
        p2.add(p3, rel=city.hasChild)

        with SqlAlchemySession(URL) as session:
            wrapper = city.CityWrapper(session=session)
            wrapper.add(c)
            session.commit()
            session._clear_database()

        check_db_cleared(self, DB)

    def test_multiple_users(self):
        """Test what happens if multiple users access the database."""
        with SqlAlchemySession(URL) as session1:
            wrapper1 = city.CityWrapper(session=session1)
            city1 = city.City(name="Freiburg")
            wrapper1.add(city1)
            session1.commit()

            with SqlAlchemySession(URL) as session2:
                wrapper2 = city.CityWrapper(session=session2)
                wrapper2.add(city.City(name="Offenburg"))
                session2.commit()

                cw = wrapper1.add(city.City(name="Karlsruhe"))
                self.assertEqual(session1._expired, {city1.uid})
                self.assertEqual(session1._buffers, [
                    [{cw.uid: cw}, {wrapper1.uid: wrapper1}, dict()],
                    [dict(), dict(), dict()]
                ])
                session1.commit()


def check_state(test_case, c, p1, p2, db=DB):
    """Check if the postgres tables are in the correct state."""
    engine = sqlalchemy.create_engine(URL)
    with engine.connect() as conn:
        metadata = sqlalchemy.MetaData(conn)
        metadata.reflect(engine)

        tables = set(metadata.tables.keys())
        test_case.assertEqual(tables, set([
            RELATIONSHIP_TABLE, data_tbl("VECTOR-INT-2"), CUDS_TABLE,
            NAMESPACES_TABLE, ENTITIES_TABLE, TYPES_TABLE,
            data_tbl("XSD_boolean"), data_tbl("XSD_float"),
            data_tbl("XSD_integer"), data_tbl("XSD_string")]))

        ts = metadata.tables[CUDS_TABLE].alias("ts")
        tp = metadata.tables[ENTITIES_TABLE].alias("tp")
        to = metadata.tables[CUDS_TABLE].alias("to")
        x = metadata.tables[RELATIONSHIP_TABLE].alias("x")
        tsc, tpc, toc, xc = ts.c, tp.c, to.c, x.c
        stmt = sqlalchemy.select([tsc.uid, tpc.ns_idx, tpc.name, toc.uid]) \
            .select_from(x.join(ts, xc.s == tsc.cuds_idx)
                         .join(tp, xc.p == tpc.entity_idx)
                         .join(to, xc.o == toc.cuds_idx))
        result = set(map(tuple, conn.execute(stmt)))
        test_case.assertEqual(result, {
            (str(uuid.UUID(int=0)), 1, "hasPart", str(c.uid)),
            (str(c.uid), 1, "hasInhabitant", str(p1.uid)),
            (str(c.uid), 1, "hasInhabitant", str(p2.uid)),
            (str(p1.uid), 1, "INVERSE_OF_hasInhabitant", str(c.uid)),
            (str(p2.uid), 1, "INVERSE_OF_hasInhabitant", str(c.uid)),
            (str(c.uid), 1, "isPartOf", str(uuid.UUID(int=0)))
        })

        ns_tbl = metadata.tables[NAMESPACES_TABLE]
        stmt = sqlalchemy.select([ns_tbl.c.ns_idx, ns_tbl.c.namespace])
        result = set(map(tuple, conn.execute(stmt)))
        test_case.assertEqual(result, {
            (1, "http://www.osp-core.com/city#")
        })

        ts = metadata.tables[CUDS_TABLE].alias("ts")
        to = metadata.tables[ENTITIES_TABLE].alias("to")
        x = metadata.tables[TYPES_TABLE].alias("x")
        stmt = sqlalchemy.select([ts.c.uid, to.c.ns_idx, to.c.name]) \
            .select_from(x.join(ts, x.c.s == ts.c.cuds_idx)
                         .join(to, x.c.o == to.c.entity_idx))
        result = set(map(tuple, conn.execute(stmt)))
        test_case.assertEqual(result, {
            (str(c.uid), 1, 'City'),
            (str(p1.uid), 1, 'Citizen'),
            (str(p2.uid), 1, 'Citizen'),
            (str(uuid.UUID(int=0)), 1, 'CityWrapper')
        })

        ts = metadata.tables[CUDS_TABLE].alias("ts")
        tp = metadata.tables[ENTITIES_TABLE].alias("to")
        x = metadata.tables[data_tbl("XSD_string")].alias("x")
        stmt = sqlalchemy.select([ts.c.uid, tp.c.ns_idx, tp.c.name, x.c.o]) \
            .select_from(x.join(ts, x.c.s == ts.c.cuds_idx)
                         .join(tp, x.c.p == tp.c.entity_idx))
        result = set(map(tuple, conn.execute(stmt)))
        test_case.assertEqual(result, {
            (str(p1.uid), 1, 'name', 'Peter'),
            (str(c.uid), 1, 'name', 'Freiburg'),
            (str(p2.uid), 1, 'name', 'Georg')
        })

        x = metadata.tables[data_tbl("VECTOR-INT-2")].alias("x")
        stmt = sqlalchemy.select([ts.c.uid, tp.c.ns_idx, tp.c.name,
                                  x.c.o___0, x.c.o___1]) \
            .select_from(x.join(ts, x.c.s == ts.c.cuds_idx)
                         .join(tp, x.c.p == tp.c.entity_idx))
        result = set(map(tuple, conn.execute(stmt)))
        test_case.assertEqual(result, {
            (str(c.uid), 1, 'coordinates', 0, 0)
        })


def check_db_cleared(test_case, db_file):
    """Check whether the database has been cleared successfully."""
    engine = sqlalchemy.create_engine(URL)
    with engine.connect() as conn:
        metadata = sqlalchemy.MetaData(conn)
        metadata.reflect(engine)

        tbl = metadata.tables[CUDS_TABLE]
        result = conn.execute(tbl.select())
        test_case.assertEqual(list(result), list())
        tbl = metadata.tables[ENTITIES_TABLE]
        result = conn.execute(tbl.select())
        test_case.assertEqual(list(result), list())
        tbl = metadata.tables[TYPES_TABLE]
        result = conn.execute(tbl.select())
        test_case.assertEqual(list(result), list())
        tbl = metadata.tables[NAMESPACES_TABLE]
        result = conn.execute(tbl.select())
        test_case.assertEqual(list(result), list())
        tbl = metadata.tables[RELATIONSHIP_TABLE]
        result = conn.execute(tbl.select())
        test_case.assertEqual(list(result), list())

        # DATA TABLES
        table_names = filter(lambda x: x.startswith(DATA_TABLE_PREFIX),
                             metadata.tables.keys())
        for table_name in table_names:
            tbl = metadata.tables[table_name]
            result = conn.execute(tbl.select())
            test_case.assertEqual(list(result), list())


def update_db(db, c, p1, p2, p3):
    """Make some changes to the data in the database."""
    engine = sqlalchemy.create_engine(URL)
    with engine.begin() as conn:
        metadata = sqlalchemy.MetaData(conn)
        metadata.reflect(engine)

        tbl = metadata.tables[CUDS_TABLE]
        stmt = sqlalchemy.select([tbl.c.uid, tbl.c.cuds_idx])
        m = dict(map(lambda x: (uuid.UUID(hex=x[0]), x[1]),
                     conn.execute(stmt)))
        tbl = metadata.tables[ENTITIES_TABLE]
        stmt = sqlalchemy.select([tbl.c.name, tbl.c.entity_idx])
        e = dict(map(tuple, conn.execute(stmt)))

        stmts = list()
        tbl = metadata.tables[data_tbl('XSD_string')]
        stmts += [
            tbl.update().where((tbl.c.s == m[c.uid])
                               & (tbl.c.p == e["name"])).values(o="Paris"),
            tbl.update().where((tbl.c.s == m[p1.uid])
                               & (tbl.c.p == e["name"])).values(o="Maria"),
            tbl.update().where((tbl.c.s == m[p2.uid])
                               & (tbl.c.p == e["name"])).values(o="Jacob")
        ]

        tbl = metadata.tables[RELATIONSHIP_TABLE]
        stmts += [
            tbl.delete().where(
                (tbl.c.s == m[p3.uid]) | (tbl.c.o == m[p3.uid])
                | (tbl.c.s == m[p2.uid]) | (tbl.c.o == m[p2.uid]))
        ]
        tbl = metadata.tables[data_tbl('XSD_string')]
        stmts += [tbl.delete().where(tbl.c.s == m[p3.uid])]
        tbl = metadata.tables[data_tbl('XSD_integer')]
        stmts += [tbl.delete().where(tbl.c.s == m[p3.uid])]
        tbl = metadata.tables[TYPES_TABLE]
        stmts += [tbl.delete().where(tbl.c.s == m[p3.uid])]
        tbl = metadata.tables[CUDS_TABLE]
        stmts += [tbl.delete().where(tbl.c.cuds_idx == m[p3.uid])]

        for stmt in stmts:
            conn.execute(stmt)


if __name__ == '__main__':
    unittest.main()
