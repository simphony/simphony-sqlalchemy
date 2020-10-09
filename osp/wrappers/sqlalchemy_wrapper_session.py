# Copyright (c) 2014-2019, Adham Hashibon, Materials Informatics Team,
# Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

import sqlalchemy
import rdflib
from osp.core.ontology.cuba import rdflib_cuba
from osp.core.session.db.sql_util import EqualsCondition, \
    AndCondition, JoinCondition
from osp.core.session.db.sql_wrapper_session import SqlWrapperSession


class SqlAlchemyWrapperSession(SqlWrapperSession):

    def __init__(self, url, **kwargs):
        super().__init__(engine=sqlalchemy.create_engine(url),
                         **kwargs)
        self._connection = self._engine.connect()
        self._transaction = None
        self._metadata = sqlalchemy.MetaData(self._connection)
        self._metadata.reflect(self._engine)

    def __str__(self):
        return "SqlAlchemy Wrapper with engine %s" % self._engine

    # OVERRIDE
    def close(self):
        self._connection.close()
        self._engine.dispose()

    # OVERRIDE
    def _init_transaction(self):
        self._transaction = self._connection.begin()

    # OVERRIDE
    def _rollback_transaction(self):
        self._transaction.rollback()
        self._transaction = None

    # OVERRIDE
    def _commit(self):
        self._transaction.commit()

    # OVERRIDE
    def _db_select(self, query):
        tables = {a: self._get_sqlalchemy_table(t).alias(a)
                  for a, t in query.tables.items()}
        sqlalchemy_columns = [getattr(tables[a].c, c)
                              for a, c in query.columns]
        condition = self._get_sqlalchemy_condition(query.condition, tables)
        s = sqlalchemy.sql.select(sqlalchemy_columns).where(condition)
        c = self._connection.execute(s)
        return c

    # OVERRIDE
    def _db_create(self, table_name, columns, datatypes,
                   primary_key, generate_pk, foreign_key, indexes):
        if table_name in self._metadata.tables:
            return
        columns = [
            sqlalchemy.Column(
                c,
                self._to_sqlalchemy_datatype(datatypes[c]),
                *([sqlalchemy.ForeignKey(".".join(foreign_key[c]))]
                  if c in foreign_key else []),
                primary_key=primary_key and c in primary_key,
                autoincrement=generate_pk)
            for c in columns]
        t = sqlalchemy.Table(table_name, self._metadata, *columns)
        for index in indexes:
            sqlalchemy.Index("idx_%s_%s" % (table_name, "_".join(index)),
                             *[getattr(t.c, x) for x in index])
        self._metadata.create_all()

    def _db_drop(self, table_name):
        self._get_sqlalchemy_table(table_name).drop()

    # OVERRIDE
    def _db_insert(self, table_name, columns, values, datatypes):
        table = self._get_sqlalchemy_table(table_name)
        stmt = table.insert().values(**{
            column: value
            for column, value in zip(columns, values)
        })
        try:
            result = self._connection.execute(stmt)
            if result.inserted_primary_key:
                return result.inserted_primary_key[0]
        except sqlalchemy.exc.IntegrityError:
            return

    # OVERRIDE
    def _db_update(self, table_name, columns, values, condition, datatypes):
        table = self._get_sqlalchemy_table(table_name)
        condition = self._get_sqlalchemy_condition(condition)
        stmt = table.update() \
            .where(condition) \
            .values(**{
                column: value
                for column, value in zip(columns, values)
            })
        self._connection.execute(stmt)

    # OVERRIDE
    def _db_delete(self, table_name, condition):
        table = self._get_sqlalchemy_table(table_name)
        condition = self._get_sqlalchemy_condition(condition)
        stmt = table.delete() \
            .where(condition)
        self._connection.execute(stmt)

    # OVERRIDE
    def _get_table_names(self, prefix):
        return set(filter(lambda x: x.startswith(prefix),
                          self._metadata.tables.keys()))

    def _get_sqlalchemy_condition(self, condition, tables=None):
        """Transform the given condition to a SqlAlchemy condition.

        :param condition: The condition to transform
        :type condition: Union[AndCondition, EqualsCondition]
        :raises NotImplementedError: Unknown condition type.
        :return: SqlAlchemy condition.
        :rtype: expression
        """
        # sqlalchemy_columns = [getattr(table.c, column) for column in columns]
        if condition is None:
            return True
        if isinstance(condition, JoinCondition):
            if tables:
                table1 = tables[condition.table_name1]
                table2 = tables[condition.table_name2]
            else:
                table1 = self._get_sqlalchemy_table(condition.table_name1)
                table2 = self._get_sqlalchemy_table(condition.table_name2)
            column1 = getattr(table1.c, condition.column1)
            column2 = getattr(table2.c, condition.column2)
            return column1 == column2
        if isinstance(condition, EqualsCondition):
            value = condition.value
            if tables:
                table = tables[condition.table_name]
            else:
                table = self._get_sqlalchemy_table(condition.table_name)
            column = getattr(table.c, condition.column)
            return column == value
        if isinstance(condition, AndCondition):
            return sqlalchemy.sql.and_(
                *[self._get_sqlalchemy_condition(c, tables)
                  for c in condition.conditions]
            )

        raise NotImplementedError("Unsupported condition")

    def _to_sqlalchemy_datatype(self, rdflib_datatype):
        """Convert the given Cuds datatype to a datatype of sqlalchemy.

        :param rdflib_datatype: The given cuds_object datatype.
        :type rdflib_datatype: URIRef
        :raises NotImplementedError: Unsupported datatype given.
        :return: A sqlalchemy datatype.
        :rtype: str
        """

        if rdflib_datatype is None:
            return sqlalchemy.String()
        if rdflib_datatype == "UUID":
            return sqlalchemy.String(36)
        if rdflib_datatype == rdflib.XSD.integer:
            return sqlalchemy.Integer
        if rdflib_datatype == rdflib.XSD.boolean:
            return sqlalchemy.Boolean
        if rdflib_datatype == rdflib.XSD.float:
            return sqlalchemy.Float
        if rdflib_datatype == rdflib.XSD.string:
            return sqlalchemy.String()
        if str(rdflib_datatype).startswith(
                str(rdflib_cuba["datatypes/STRING-"])):
            return sqlalchemy.String(int(str(rdflib_datatype).split(":")[-1]))
        else:
            raise NotImplementedError(f"Unsupported data type "
                                      f"{rdflib_datatype}!")

    def _get_sqlalchemy_table(self, table_name):
        """Get the sqlalchemy table, either from metadata or load it.

        :param table_name: The name of the table to get.
        :type table_name: str
        :return: The sqlalchemy table
        :rtype: Table
        """
        if table_name in self._metadata.tables:
            return self._metadata.tables[table_name]
        return sqlalchemy.Table(table_name,
                                self._metadata,
                                autoload=True,
                                autoload_with=self._connection)
