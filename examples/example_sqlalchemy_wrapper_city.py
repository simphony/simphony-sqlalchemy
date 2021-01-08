"""Test the wrapper."""

import os
from osp.core.namespaces import City
from osp.core.utils import pretty_print
from osp.wrappers.sqlalchemy_wrapper_session import \
    SqlAlchemyWrapperSession

try:
    # Construct the Datastructure.
    c = City.City(name="Freiburg")
    p1 = City.Citizen(name="Peter")
    p2 = City.Citizen(name="Hans")
    p3 = City.Citizen(name="Michel")
    n = City.Neighborhood(name="Zähringen")
    s = City.Street(name="Le street")
    b = City.Building(name="Theater")
    a = City.Address(postalCode=79123, name='Le street', number=12)
    c.add(p1, p2, p3, rel=City.hasInhabitant)
    c.add(n).add(s).add(b).add(a)

    print("Connect to DB via transport session")
    with SqlAlchemyWrapperSession("sqlite:///test.db") as session:
        wrapper = City.CityWrapper(session=session)
        wrapper.add(c)
        wrapper.session.commit()

    print("Reconnect and check if data is still there")
    with SqlAlchemyWrapperSession("sqlite:///test.db") as session:
        wrapper = City.CityWrapper(session=session)
        city = wrapper.get(oclass=City.City)[0]
        pretty_print(city)

    print("Extract all CUDS objects of a certain CUBA class")
    with SqlAlchemyWrapperSession("sqlite:///test.db") as session:
        wrapper = City.CityWrapper(session=session)
        citizens = wrapper.session.load_by_oclass(oclass=City.Citizen)
        print("All citizens:")
        for citizen in citizens:
            pretty_print(citizen)

    print("Reconnect and make some changes")
    with SqlAlchemyWrapperSession("sqlite:///test.db") as session:
        wrapper = City.CityWrapper(session=session)
        city = wrapper.get(oclass=City.City)[0]
        city.name = "Paris"
        wrapper.session.commit()

    print("Reconnect and check if changes were successful")
    with SqlAlchemyWrapperSession("sqlite:///test.db") as session:
        wrapper = City.CityWrapper(session=session)
        city = wrapper.get(oclass=City.City)[0]
        pretty_print(city)

    print("Delete the city")
    with SqlAlchemyWrapperSession("sqlite:///test.db") as session:
        wrapper = City.CityWrapper(session=session)
        city = wrapper.get(oclass=City.City)[0]
        wrapper.remove(city)
        wrapper.session.prune()
        wrapper.session.commit()

    print("Reconnect and check if deletion was successful")
    with SqlAlchemyWrapperSession("sqlite:///test.db") as session:
        wrapper = City.CityWrapper(session=session)
        print("All cities:", wrapper.get(oclass=City.City))

finally:
    if os.path.exists("test.db"):
        os.remove("test.db")
