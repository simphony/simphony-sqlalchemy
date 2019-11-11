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
from osp.core import CITY
from osp.wrappers.sqlalchemy_wrapper_session import \
    SqlAlchemyWrapperSession


class TestSqliteAlchemyCity(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        os.remove("test.db")

    def test_insert(self):
        """Test inserting in the sqlite table."""
        c = CITY.CITY(name="Freiburg")
        p1 = CITY.CITIZEN(name="Peter")
        p2 = CITY.CITIZEN(name="Georg")
        c.add(p1, p2, rel=CITY.HAS_INHABITANT)

        with SqlAlchemyWrapperSession("sqlite:///test.db") as session:
            wrapper = CITY.CITY_WRAPPER(session=session)
            wrapper.add(c)
            session.commit()

        check_state(self, c, p1, p2)

    def test_update(self):
        """Test updating the sqlite table."""
        c = CITY.CITY(name="Paris")
        p1 = CITY.CITIZEN(name="Peter")
        c.add(p1, rel=CITY.HAS_INHABITANT)

        with SqlAlchemyWrapperSession("sqlite:///test.db") as session:
            wrapper = CITY.CITY_WRAPPER(session=session)
            cw = wrapper.add(c)
            session.commit()

            p2 = CITY.CITIZEN(name="Georg")
            cw.add(p2, rel=CITY.HAS_INHABITANT)
            cw.name = "Freiburg"
            session.commit()

        check_state(self, c, p1, p2)

    def test_update_first_level(self):
        """Test updating the sqlite table."""
        c = CITY.CITY(name="Paris")

        with SqlAlchemyWrapperSession("sqlite:///test.db") as session:
            wrapper = CITY.CITY_WRAPPER(session=session)
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
        c = CITY.CITY(name="Freiburg")
        p1 = CITY.CITIZEN(name="Peter")
        p2 = CITY.CITIZEN(name="Georg")
        p3 = CITY.CITIZEN(name="Hans")
        c.add(p1, p2, p3, rel=CITY.HAS_INHABITANT)

        with SqlAlchemyWrapperSession("sqlite:///test.db") as session:
            wrapper = CITY.CITY_WRAPPER(session=session)
            cw = wrapper.add(c)
            session.commit()

            cw.remove(p3.uid)
            session.prune()
            session.commit()

        check_state(self, c, p1, p2)

    def test_init(self):
        """Test of first level of children are loaded automatically."""
        c = CITY.CITY(name="Freiburg")
        p1 = CITY.CITIZEN(name="Peter")
        p2 = CITY.CITIZEN(name="Anna")
        p3 = CITY.CITIZEN(name="Julia")
        c.add(p1, p2, p3, rel=CITY.HAS_INHABITANT)
        p1.add(p3, rel=CITY.HAS_CHILD)
        p2.add(p3, rel=CITY.HAS_CHILD)

        with SqlAlchemyWrapperSession("sqlite:///test.db") as session:
            wrapper = CITY.CITY_WRAPPER(session=session)
            wrapper.add(c)
            session.commit()

        with SqlAlchemyWrapperSession("sqlite:///test.db") as session:
            wrapper = CITY.CITY_WRAPPER(session=session)
            self.assertEqual(set(session._registry.keys()),
                             {c.uid, wrapper.uid})
            self.assertEqual(wrapper.get(c.uid).name, "Freiburg")
            self.assertEqual(
                session._registry.get(c.uid)._neighbours[CITY.HAS_INHABITANT],
                {p1.uid: p1.is_a, p2.uid: p2.is_a,
                 p3.uid: p3.is_a})
            self.assertEqual(
                session._registry.get(c.uid)._neighbours[CITY.IS_PART_OF],
                {wrapper.uid: wrapper.is_a})

    def test_load_by_oclass(self):
        c = CITY.CITY(name="Freiburg")
        p1 = CITY.CITIZEN(name="Peter")
        p2 = CITY.CITIZEN(name="Anna")
        p3 = CITY.CITIZEN(name="Julia")
        c.add(p1, p2, p3, rel=CITY.HAS_INHABITANT)
        p1.add(p3, rel=CITY.HAS_CHILD)
        p2.add(p3, rel=CITY.HAS_CHILD)

        with SqlAlchemyWrapperSession("sqlite:///test.db") as session:
            wrapper = CITY.CITY_WRAPPER(session=session)
            wrapper.add(c)
            session.commit()

        with SqlAlchemyWrapperSession("sqlite:///test.db") as session:
            wrapper = CITY.CITY_WRAPPER(session=session)
            cs = wrapper.get(c.uid)
            r = session.load_by_oclass(CITY.CITY)
            self.assertIs(next(r), cs)
            r = session.load_by_oclass(CITY.CITIZEN)
            self.assertEqual(set(r), {p1, p2, p3})
            r = session.load_by_oclass(CITY.PERSON)
            self.assertEqual(set(r), {p1, p2, p3})

        with SqlAlchemyWrapperSession("sqlite:///test.db") as session:
            wrapper = CITY.CITY_WRAPPER(session=session)
            cs = wrapper.get(c.uid)
            r = session.load_by_oclass(CITY.STREET)
            self.assertRaises(StopIteration, next, r)

    def test_load_missing(self):
        """Test if missing objects are loaded automatically."""
        c = CITY.CITY(name="Freiburg")
        p1 = CITY.CITIZEN(name="Peter")
        p2 = CITY.CITIZEN(name="Anna")
        p3 = CITY.CITIZEN(name="Julia")
        c.add(p1, p2, p3, rel=CITY.HAS_INHABITANT)
        p1.add(p3, rel=CITY.HAS_CHILD)
        p2.add(p3, rel=CITY.HAS_CHILD)

        with SqlAlchemyWrapperSession("sqlite:///test.db") as session:
            wrapper = CITY.CITY_WRAPPER(session=session)
            wrapper.add(c)
            session.commit()

        with SqlAlchemyWrapperSession("sqlite:///test.db") as session:
            wrapper = CITY.CITY_WRAPPER(session=session)
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
                p3w._neighbours[CITY.IS_CHILD_OF],
                {p1.uid: p1.is_a, p2.uid: p2.is_a}
            )
            self.assertEqual(
                p2w._neighbours[CITY.HAS_CHILD],
                {p3.uid: p3.is_a}
            )
            self.assertEqual(
                p2w._neighbours[CITY.IS_INHABITANT_OF],
                {c.uid: c.is_a}
            )

    def test_clear_database(self):
        c = CITY.CITY(name="Freiburg")
        p1 = CITY.CITIZEN(name="Peter")
        p2 = CITY.CITIZEN(name="Anna")
        p3 = CITY.CITIZEN(name="Julia")
        c.add(p1, p2, p3, rel=CITY.HAS_INHABITANT)
        p1.add(p3, rel=CITY.HAS_CHILD)
        p2.add(p3, rel=CITY.HAS_CHILD)

        with SqlAlchemyWrapperSession("sqlite:///test.db") as session:
            wrapper = CITY.CITY_WRAPPER(session=session)
            wrapper.add(c)
            session.commit()
            session._clear_database()

        check_db_cleared(self, "test.db")

    def test_add_item_already_in_db(self):
        """Test to add object from db somewhere else"""
        with SqlAlchemyWrapperSession("sqlite:///test.db") as session:
            w = CITY.CITY_WRAPPER(session=session)
            c = CITY.CITY(name="Freiburg")
            p = CITY.CITIZEN(name="Matthias")
            c.add(p, rel=CITY.HAS_INHABITANT)
            w.add(c)
            session.commit()

        with SqlAlchemyWrapperSession("sqlite:///test.db") as session:
            w = CITY.CITY_WRAPPER(session=session)
            # get the citizen
            pw = next(session.load_by_oclass(CITY.CITIZEN))
            c = CITY.CITY(name="Paris")
            cw = w.add(c)
            # add the citizen somewhere else
            cw.add(pw, rel=CITY.HAS_INHABITANT)
            session.commit()  # should not throw an error


def check_state(test_case, c, p1, p2, table="test.db"):
    """Check if the sqlite tables are in the correct state."""
    with sqlite3.connect(table) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT uid, oclass, first_level FROM %s;"
                       % SqlAlchemyWrapperSession.MASTER_TABLE)
        result = set(cursor.fetchall())
        test_case.assertEqual(result, {
            (str(c.uid), str(c.is_a), 1),
            (str(p1.uid), str(p1.is_a), 0),
            (str(p2.uid), str(p2.is_a), 0)
        })

        cursor.execute("SELECT origin, target, name, target_oclass FROM %s;"
                       % SqlAlchemyWrapperSession.RELATIONSHIP_TABLE)
        result = set(cursor.fetchall())
        test_case.assertEqual(result, {
            (str(c.uid), str(p1.uid), "CITY.HAS_INHABITANT", "CITY.CITIZEN"),
            (str(c.uid), str(p2.uid), "CITY.HAS_INHABITANT", "CITY.CITIZEN"),
            (str(p1.uid), str(c.uid), "CITY.IS_INHABITANT_OF", "CITY.CITY"),
            (str(p2.uid), str(c.uid), "CITY.IS_INHABITANT_OF", "CITY.CITY"),
            (str(c.uid), str(uuid.UUID(int=0)),
                "CITY.IS_PART_OF", "CITY.CITY_WRAPPER")
        })

        cursor.execute("SELECT uid, name, coordinates___0, coordinates___1 "
                       "FROM CUDS_CITY___CITY;")
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
        cursor.execute("SELECT * FROM CUDS_CITY___CITIZEN")
        test_case.assertEqual(list(cursor), list())
        cursor.execute("SELECT * FROM CUDS_CITY___CITY")
        test_case.assertEqual(list(cursor), list())


if __name__ == '__main__':
    unittest.main()
