# Copyright (c) 2018, Adham Hashibon and Materials Informatics Team
# at Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

import os
import sqlite3
import uuid
import unittest2 as unittest
from osp.wrappers.sqlalchemy_wrapper_session import \
    SqlAlchemyWrapperSession

try:
    from osp.core.namespaces import city
except ImportError:
    from osp.core.ontology import Parser
    CITY = Parser().parse("city")


class TestSqliteAlchemyCity(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        os.remove("test.db")

    def test_insert(self):
        """Test inserting in the sqlite table."""
        c = city.City(name="Freiburg")
        p1 = city.Citizen(name="Peter")
        p2 = city.Citizen(name="Georg")
        c.add(p1, p2, rel=city.hasInhabitant)

        with SqlAlchemyWrapperSession("sqlite:///test.db") as session:
            wrapper = city.CityWrapper(session=session)
            wrapper.add(c)
            session.commit()

        check_state(self, c, p1, p2)

    def test_update(self):
        """Test updating the sqlite table."""
        c = city.City(name="Paris")
        p1 = city.Citizen(name="Peter")
        c.add(p1, rel=city.hasInhabitant)

        with SqlAlchemyWrapperSession("sqlite:///test.db") as session:
            wrapper = city.CityWrapper(session=session)
            cw = wrapper.add(c)
            session.commit()

            p2 = city.Citizen(name="Georg")
            cw.add(p2, rel=city.hasInhabitant)
            cw.name = "Freiburg"
            session.commit()

        check_state(self, c, p1, p2)

    def test_update_first_level(self):
        """Test updating the sqlite table."""
        c = city.City(name="Paris")

        with SqlAlchemyWrapperSession("sqlite:///test.db") as session:
            wrapper = city.CityWrapper(session=session)
            cw = wrapper.add(c)
            session.commit()

            wrapper.remove(cw.uid)
            session.commit()

        with sqlite3.connect("test.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM %s WHERE first_level = 1;"
                           % SqlAlchemyWrapperSession.MASTER_TABLE)
            result = set(cursor.fetchall())
            self.assertEqual(len(result), 0)

    def test_delete(self):
        """Test to delete cuds_objects from the sqlite table"""
        c = city.City(name="Freiburg")
        p1 = city.Citizen(name="Peter")
        p2 = city.Citizen(name="Georg")
        p3 = city.Citizen(name="Hans")
        c.add(p1, p2, p3, rel=city.hasInhabitant)

        with SqlAlchemyWrapperSession("sqlite:///test.db") as session:
            wrapper = city.CityWrapper(session=session)
            cw = wrapper.add(c)
            session.commit()

            cw.remove(p3.uid)
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

        with SqlAlchemyWrapperSession("sqlite:///test.db") as session:
            wrapper = city.CityWrapper(session=session)
            wrapper.add(c)
            session.commit()

        with SqlAlchemyWrapperSession("sqlite:///test.db") as session:
            wrapper = city.CityWrapper(session=session)
            self.assertEqual(set(session._registry.keys()),
                             {c.uid, wrapper.uid})
            self.assertEqual(wrapper.get(c.uid).name, "Freiburg")
            self.assertEqual(
                session._registry.get(c.uid)._neighbors[city.hasInhabitant],
                {p1.uid: p1.oclass, p2.uid: p2.oclass,
                 p3.uid: p3.oclass})
            self.assertEqual(
                session._registry.get(c.uid)._neighbors[city.isPartOf],
                {wrapper.uid: wrapper.oclass})

    def test_load_by_oclass(self):
        c = city.City(name="Freiburg")
        p1 = city.Citizen(name="Peter")
        p2 = city.Citizen(name="Anna")
        p3 = city.Citizen(name="Julia")
        c.add(p1, p2, p3, rel=city.hasInhabitant)
        p1.add(p3, rel=city.hasChild)
        p2.add(p3, rel=city.hasChild)

        with SqlAlchemyWrapperSession("sqlite:///test.db") as session:
            wrapper = city.CityWrapper(session=session)
            wrapper.add(c)
            session.commit()

        with SqlAlchemyWrapperSession("sqlite:///test.db") as session:
            wrapper = city.CityWrapper(session=session)
            cs = wrapper.get(c.uid)
            r = session.load_by_oclass(city.City)
            self.assertIs(next(r), cs)
            r = session.load_by_oclass(city.Citizen)
            self.assertEqual(set(r), {p1, p2, p3})
            r = session.load_by_oclass(city.Person)
            self.assertEqual(set(r), {p1, p2, p3})

        with SqlAlchemyWrapperSession("sqlite:///test.db") as session:
            wrapper = city.CityWrapper(session=session)
            cs = wrapper.get(c.uid)
            r = session.load_by_oclass(city.Street)
            self.assertRaises(StopIteration, next, r)

    def test_load_missing(self):
        """Test if missing objects are loaded automatically."""
        c = city.City(name="Freiburg")
        p1 = city.Citizen(name="Peter")
        p2 = city.Citizen(name="Anna")
        p3 = city.Citizen(name="Julia")
        c.add(p1, p2, p3, rel=city.hasInhabitant)
        p1.add(p3, rel=city.hasChild)
        p2.add(p3, rel=city.hasChild)

        with SqlAlchemyWrapperSession("sqlite:///test.db") as session:
            wrapper = city.CityWrapper(session=session)
            wrapper.add(c)
            session.commit()

        with SqlAlchemyWrapperSession("sqlite:///test.db") as session:
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
                {p1.uid: p1.oclass, p2.uid: p2.oclass}
            )
            self.assertEqual(
                p2w._neighbors[city.hasChild],
                {p3.uid: p3.oclass}
            )
            self.assertEqual(
                p2w._neighbors[city.INVERSE_OF_hasInhabitant],
                {c.uid: c.oclass}
            )

    def test_clear_database(self):
        c = city.City(name="Freiburg")
        p1 = city.Citizen(name="Peter")
        p2 = city.Citizen(name="Anna")
        p3 = city.Citizen(name="Julia")
        c.add(p1, p2, p3, rel=city.hasInhabitant)
        p1.add(p3, rel=city.hasChild)
        p2.add(p3, rel=city.hasChild)

        with SqlAlchemyWrapperSession("sqlite:///test.db") as session:
            wrapper = city.CityWrapper(session=session)
            wrapper.add(c)
            session.commit()
            session._clear_database()

        check_db_cleared(self, "test.db")

    def test_add_item_already_in_db(self):
        """Test to add object from db somewhere else"""
        with SqlAlchemyWrapperSession("sqlite:///test.db") as session:
            w = city.CityWrapper(session=session)
            c = city.City(name="Freiburg")
            p = city.Citizen(name="Matthias")
            c.add(p, rel=city.hasInhabitant)
            w.add(c)
            session.commit()

        with SqlAlchemyWrapperSession("sqlite:///test.db") as session:
            w = city.CityWrapper(session=session)
            # get the citizen
            pw = next(session.load_by_oclass(city.Citizen))
            c = city.City(name="Paris")
            cw = w.add(c)
            # add the citizen somewhere else
            cw.add(pw, rel=city.hasInhabitant)
            session.commit()  # should not throw an error


def check_state(test_case, c, p1, p2, table="test.db"):
    """Check if the sqlite tables are in the correct state."""
    with sqlite3.connect(table) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT uid, oclass, first_level FROM %s;"
                       % SqlAlchemyWrapperSession.MASTER_TABLE)
        result = set(cursor.fetchall())
        test_case.assertEqual(result, {
            (str(uuid.UUID(int=0)), "", 0),
            (str(c.uid), str(c.oclass), 1),
            (str(p1.uid), str(p1.oclass), 0),
            (str(p2.uid), str(p2.oclass), 0)
        })

        cursor.execute("SELECT origin, target, name, target_oclass FROM %s;"
                       % SqlAlchemyWrapperSession.RELATIONSHIP_TABLE)
        result = set(cursor.fetchall())
        test_case.assertEqual(result, {
            (str(c.uid), str(p1.uid), "city.hasInhabitant", "city.Citizen"),
            (str(c.uid), str(p2.uid), "city.hasInhabitant", "city.Citizen"),
            (str(p1.uid), str(c.uid), "city.INVERSE_OF_hasInhabitant",
             "city.City"),
            (str(p2.uid), str(c.uid), "city.INVERSE_OF_hasInhabitant",
             "city.City"),
            (str(c.uid), str(uuid.UUID(int=0)),
                "city.isPartOf", "city.CityWrapper")
        })

        cursor.execute("SELECT uid, name, coordinates___0, coordinates___1 "
                       "FROM CUDS_city___City;")
        result = set(cursor.fetchall())
        test_case.assertEqual(result, {
            (str(c.uid), "Freiburg", 0, 0)
        })


def check_db_cleared(test_case, table):
    with sqlite3.connect(table) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM %s;"
                       % SqlAlchemyWrapperSession.MASTER_TABLE)
        test_case.assertEqual(
            list(cursor), [('00000000-0000-0000-0000-000000000000', '', 0)])
        cursor.execute("SELECT * FROM %s;"
                       % SqlAlchemyWrapperSession.RELATIONSHIP_TABLE)
        test_case.assertEqual(list(cursor), list())
        cursor.execute("SELECT * FROM CUDS_city___Citizen")
        test_case.assertEqual(list(cursor), list())
        cursor.execute("SELECT * FROM CUDS_city___Citizen")
        test_case.assertEqual(list(cursor), list())


if __name__ == '__main__':
    unittest.main()
