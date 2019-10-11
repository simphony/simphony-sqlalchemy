import os
import cuds.classes
from cuds.classes import CUBA
from cuds.utils import pretty_print
from cudsqlalchemy.sqlalchemy_wrapper_session import \
    SqlAlchemyWrapperSession

try:
    # Construct the Datastructure.
    c = cuds.classes.City("Freiburg")
    p1 = cuds.classes.Citizen(name="Peter")
    p2 = cuds.classes.Citizen(name="Hans")
    p3 = cuds.classes.Citizen(name="Michel")
    n = cuds.classes.Neighbourhood("Zähringen")
    s = cuds.classes.Street("Le street")
    b = cuds.classes.Building("Theater")
    a = cuds.classes.Address(postal_code=79123, name='Le street', number=12)
    c.add(p1, p2, p3, rel=cuds.classes.HasInhabitant)
    c.add(n).add(s).add(b).add(a)

    print("Connect to DB via transport session")
    with SqlAlchemyWrapperSession("sqlite:///test.db") as session:
        wrapper = cuds.classes.CityWrapper(session=session)
        wrapper.add(c)
        wrapper.session.commit()

    print("Reconnect and check if data is still there")
    with SqlAlchemyWrapperSession("sqlite:///test.db") as session:
        wrapper = cuds.classes.CityWrapper(session=session)
        city = wrapper.get(cuba_key=CUBA.CITY)[0]
        pretty_print(city)

    print("Reconnect and make some changes")
    with SqlAlchemyWrapperSession("sqlite:///test.db") as session:
        wrapper = cuds.classes.CityWrapper(session=session)
        city = wrapper.get(cuba_key=CUBA.CITY)[0]
        city.name = "Paris"
        wrapper.session.commit()

    print("Reconnect and check if changes were successful")
    with SqlAlchemyWrapperSession("sqlite:///test.db") as session:
        wrapper = cuds.classes.CityWrapper(session=session)
        city = wrapper.get(cuba_key=CUBA.CITY)[0]
        pretty_print(city)

    print("Delete the city")
    with SqlAlchemyWrapperSession("sqlite:///test.db") as session:
        wrapper = cuds.classes.CityWrapper(session=session)
        city = wrapper.get(cuba_key=CUBA.CITY)[0]
        wrapper.remove(city)
        wrapper.session.prune()
        wrapper.session.commit()

    print("Reconnect and check if deletion was successful")
    with SqlAlchemyWrapperSession("sqlite:///test.db") as session:
        wrapper = cuds.classes.CityWrapper(session=session)
        print("All cities:", wrapper.get(cuba_key=CUBA.CITY))

finally:
    if os.path.exists("test.db"):
        os.remove("test.db")
