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
import cuds.classes
from sqlalchemy_wrapper.sqlalchemy_wrapper_session import \
    SqlAlchemyWrapperSession


class TestSqliteAlchemyCity(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        os.remove("test.db")

    def test_insert(self):
        """Test inserting in the sqlite table."""
        c = cuds.classes.City(name="Freiburg")
        p1 = cuds.classes.Citizen(name="Peter")
        p2 = cuds.classes.Citizen(name="Georg")
        c.add(p1, p2, rel=cuds.classes.HasInhabitant)

        with SqlAlchemyWrapperSession("sqlite:///test.db") as session:
            wrapper = cuds.classes.CityWrapper(session)
            wrapper.add(c)
            session.commit()

        check_state(self, c, p1, p2)

    def test_update(self):
        """Test updating the sqlite table."""
        c = cuds.classes.City("Paris")
        p1 = cuds.classes.Citizen(name="Peter")
        c.add(p1, rel=cuds.classes.HasInhabitant)

        with SqlAlchemyWrapperSession("sqlite:///test.db") as session:
            wrapper = cuds.classes.CityWrapper(session)
            cw = wrapper.add(c)
            session.commit()

            p2 = cuds.classes.Citizen(name="Georg")
            cw.add(p2, rel=cuds.classes.HasInhabitant)
            cw.name = "Freiburg"
            session.commit()

        check_state(self, c, p1, p2)

    def test_delete(self):
        """Test to delete cuds_objects from the sqlite table"""
        c = cuds.classes.City("Freiburg")
        p1 = cuds.classes.Citizen(name="Peter")
        p2 = cuds.classes.Citizen(name="Georg")
        p3 = cuds.classes.Citizen(name="Hans")
        c.add(p1, p2, p3, rel=cuds.classes.HasInhabitant)

        with SqlAlchemyWrapperSession("sqlite:///test.db") as session:
            wrapper = cuds.classes.CityWrapper(session)
            cw = wrapper.add(c)
            session.commit()

            cw.remove(p3.uid)
            session.prune()
            session.commit()

        check_state(self, c, p1, p2)

    def test_init(self):
        """Test of first level of children are loaded automatically."""
        c = cuds.classes.City("Freiburg")
        p1 = cuds.classes.Citizen(name="Peter")
        p2 = cuds.classes.Citizen(name="Anna")
        p3 = cuds.classes.Citizen(name="Julia")
        c.add(p1, p2, p3, rel=cuds.classes.HasInhabitant)
        p1.add(p3, rel=cuds.classes.HasChild)
        p2.add(p3, rel=cuds.classes.HasChild)

        with SqlAlchemyWrapperSession("sqlite:///test.db") as session:
            wrapper = cuds.classes.CityWrapper(session=session)
            wrapper.add(c)
            session.commit()

        with SqlAlchemyWrapperSession("sqlite:///test.db") as session:
            wrapper = cuds.classes.CityWrapper(session=session)
            self.assertEqual(set(session._registry.keys()),
                             {c.uid, wrapper.uid})
            self.assertEqual(wrapper.get(c.uid).name, "Freiburg")
            self.assertEqual(
                session._registry.get(c.uid)[cuds.classes.HasInhabitant],
                {p1.uid: p1.cuba_key, p2.uid: p2.cuba_key,
                 p3.uid: p3.cuba_key})
            self.assertEqual(
                session._registry.get(c.uid)[cuds.classes.IsPartOf],
                {wrapper.uid: wrapper.cuba_key})

    def test_load_by_cuba_key(self):
        c = cuds.classes.City("Freiburg")
        p1 = cuds.classes.Citizen(name="Peter")
        p2 = cuds.classes.Citizen(name="Anna")
        p3 = cuds.classes.Citizen(name="Julia")
        c.add(p1, p2, p3, rel=cuds.classes.HasInhabitant)
        p1.add(p3, rel=cuds.classes.HasChild)
        p2.add(p3, rel=cuds.classes.HasChild)

        with SqlAlchemyWrapperSession("sqlite:///test.db") as session:
            wrapper = cuds.classes.CityWrapper(session=session)
            wrapper.add(c)
            session.commit()

        with SqlAlchemyWrapperSession("sqlite:///test.db") as session:
            wrapper = cuds.classes.CityWrapper(session=session)
            cs = wrapper.get(c.uid)
            r = session.load_by_cuba_key(cuds.classes.City.cuba_key)
            self.assertIs(next(r), cs)
            r = session.load_by_cuba_key(cuds.classes.Citizen.cuba_key)
            self.assertEqual(set(r), {p1, p2, p3})

        with SqlAlchemyWrapperSession("sqlite:///test.db") as session:
            wrapper = cuds.classes.CityWrapper(session=session)
            cs = wrapper.get(c.uid)
            r = session.load_by_cuba_key(cuds.classes.Street.cuba_key)
            self.assertRaises(StopIteration, next, r)

    def test_load_missing(self):
        """Test if missing objects are loaded automatically."""
        c = cuds.classes.City("Freiburg")
        p1 = cuds.classes.Citizen(name="Peter")
        p2 = cuds.classes.Citizen(name="Anna")
        p3 = cuds.classes.Citizen(name="Julia")
        c.add(p1, p2, p3, rel=cuds.classes.HasInhabitant)
        p1.add(p3, rel=cuds.classes.HasChild)
        p2.add(p3, rel=cuds.classes.HasChild)

        with SqlAlchemyWrapperSession("sqlite:///test.db") as session:
            wrapper = cuds.classes.CityWrapper(session=session)
            wrapper.add(c)
            session.commit()

        with SqlAlchemyWrapperSession("sqlite:///test.db") as session:
            wrapper = cuds.classes.CityWrapper(session=session)
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
                p3w[cuds.classes.IsChildOf],
                {p1.uid: p1.cuba_key, p2.uid: p2.cuba_key}
            )
            self.assertEqual(
                p2w[cuds.classes.HasChild],
                {p3.uid: p3.cuba_key}
            )
            self.assertEqual(
                p2w[cuds.classes.IsInhabitantOf],
                {c.uid: c.cuba_key}
            )

    def test_clear_database(self):
        c = cuds.classes.City("Freiburg")
        p1 = cuds.classes.Citizen(name="Peter")
        p2 = cuds.classes.Citizen(name="Anna")
        p3 = cuds.classes.Citizen(name="Julia")
        c.add(p1, p2, p3, rel=cuds.classes.HasInhabitant)
        p1.add(p3, rel=cuds.classes.HasChild)
        p2.add(p3, rel=cuds.classes.HasChild)

        with SqlAlchemyWrapperSession("sqlite:///test.db") as session:
            wrapper = cuds.classes.CityWrapper(session=session)
            wrapper.add(c)
            session.commit()
            session._clear_database()

        check_db_cleared(self, "test.db")

    def test_add_item_already_in_db(self):
        """Test to add object from db somewhere else"""
        with SqlAlchemyWrapperSession("sqlite:///test.db") as session:
            w = cuds.classes.CityWrapper(session=session)
            c = cuds.classes.City("Freiburg")
            p = cuds.classes.Citizen(name="Matthias")
            c.add(p, rel=cuds.classes.HasInhabitant)
            w.add(c)
            session.commit()

        with SqlAlchemyWrapperSession("sqlite:///test.db") as session:
            w = cuds.classes.CityWrapper(session=session)
            # get the citizen
            pw = next(session.load_by_cuba_key(cuds.classes.Citizen.cuba_key))
            c = cuds.classes.City("Paris")
            cw = w.add(c)
            # add the citizen somewhere else
            cw.add(pw, rel=cuds.classes.HasInhabitant)
            session.commit()  # should not throw an error



def check_state(test_case, c, p1, p2, table="test.db"):
    """Check if the sqlite tables are in the correct state."""
    with sqlite3.connect(table) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT uid, cuba, first_level FROM %s;"
                       % SqlAlchemyWrapperSession.MASTER_TABLE)
        result = set(cursor.fetchall())
        test_case.assertEqual(result, {
            (str(c.uid), c.cuba_key.value, 1),
            (str(p1.uid), p1.cuba_key.value, 0),
            (str(p2.uid), p2.cuba_key.value, 0)
        })

        cursor.execute("SELECT origin, target, name, target_cuba FROM %s;"
                       % SqlAlchemyWrapperSession.RELATIONSHIP_TABLE)
        result = set(cursor.fetchall())
        test_case.assertEqual(result, {
            (str(c.uid), str(p1.uid), "HAS_INHABITANT", "CITIZEN"),
            (str(c.uid), str(p2.uid), "HAS_INHABITANT", "CITIZEN"),
            (str(p1.uid), str(c.uid), "IS_INHABITANT_OF", "CITY"),
            (str(p2.uid), str(c.uid), "IS_INHABITANT_OF", "CITY"),
            (str(c.uid), str(uuid.UUID(int=0)),
                "IS_PART_OF", "CITY_WRAPPER")
        })

        cursor.execute("SELECT uid, name, coordinates___0, coordinates___1 "
                       "FROM CUDS_CITY;")
        result = set(cursor.fetchall())
        test_case.assertEqual(result, {
            (str(c.uid), "Freiburg", 0, 0)
        })


def check_db_cleared(test_case, table):
    with sqlite3.connect(table) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM %s;"
                       % SqlAlchemyWrapperSession.MASTER_TABLE)
        test_case.assertEqual(list(cursor), list())
        cursor.execute("SELECT * FROM %s;"
                       % SqlAlchemyWrapperSession.RELATIONSHIP_TABLE)
        test_case.assertEqual(list(cursor), list())
        cursor.execute("SELECT * FROM CUDS_CITIZEN")
        test_case.assertEqual(list(cursor), list())
        cursor.execute("SELECT * FROM CUDS_CITY")
        test_case.assertEqual(list(cursor), list())


if __name__ == '__main__':
    unittest.main()
