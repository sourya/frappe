from __future__ import unicode_literals

import frappe
import psycopg2
import psycopg2.extensions
from six import string_types
from frappe.utils import cstr
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

from frappe.database.database import Database
from frappe.database.postgres.schema import PostgresTable

# cast decimals as floats
DEC2FLOAT = psycopg2.extensions.new_type(
    psycopg2.extensions.DECIMAL.values,
    'DEC2FLOAT',
    lambda value, curs: float(value) if value is not None else None)

psycopg2.extensions.register_type(DEC2FLOAT)

class PostgresDatabase(Database):
	ProgrammingError = psycopg2.ProgrammingError
	OperationalError = psycopg2.OperationalError
	InternalError = psycopg2.InternalError
	SQLError = psycopg2.ProgrammingError
	DataError = psycopg2.DataError
	InterfaceError = psycopg2.InterfaceError
	REGEX_CHARACTER = '~'

	def setup_type_map(self):
		self.type_map = {
			'Currency':		('decimal', '18,6'),
			'Int':			('bigint', None),
			'Long Int':		('bigint', None), # convert int to bigint if length is more than 11
			'Float':		('decimal', '18,6'),
			'Percent':		('decimal', '18,6'),
			'Check':		('smallint', None),
			'Small Text':	('text', ''),
			'Long Text':	('text', ''),
			'Code':			('text', ''),
			'Text Editor':	('text', ''),
			'Date':			('date', ''),
			'Datetime':		('timestamp', None),
			'Time':			('time', '6'),
			'Text':			('text', ''),
			'Data':			('varchar', self.VARCHAR_LEN),
			'Link':			('varchar', self.VARCHAR_LEN),
			'Dynamic Link':	('varchar', self.VARCHAR_LEN),
			'Password':		('varchar', self.VARCHAR_LEN),
			'Select':		('varchar', self.VARCHAR_LEN),
			'Read Only':	('varchar', self.VARCHAR_LEN),
			'Attach':		('text', ''),
			'Attach Image':	('text', ''),
			'Signature':	('text', ''),
			'Color':		('varchar', self.VARCHAR_LEN),
			'Barcode':		('text', ''),
			'Geolocation':	('text', '')
		}

	def get_connection(self):
		# warnings.filterwarnings('ignore', category=psycopg2.Warning)
		conn = psycopg2.connect('host={} dbname={}'.format(self.host, self.user))
		conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT) # TODO: Remove this
		# conn = psycopg2.connect('host={} dbname={} user={} password={}'.format(self.host,
		# 	self.user, self.user, self.password))

		return conn

	def escape(self, s, percent=True):
		"""Excape quotes and percent in given string."""
		# NOTE separating % escape, because % escape should only be done when using LIKE operator
		# or when you use python format string to generate query that already has a %s
		# for example: sql("select name from `tabUser` where name=%s and {0}".format(conditions), something)
		# defaulting it to True, as this is the most frequent use case
		# ideally we shouldn't have to use ESCAPE and strive to pass values via the values argument of sql
		if percent:
			s = s.replace("%", "%%")

		s = s.encode('utf-8')

		return str(psycopg2.extensions.QuotedString(s))

	def get_database_size(self):
		''''Returns database size in MB'''
		db_size = frappe.db.sql("SELECT (pg_database_size(%s) / 1024 / 1024) as database_size",
			self.db_name, as_dict=True)
		return db_size[0].get('database_size')

	def sql(self, *args, **kwargs):
		# replace ` with " for definitions
		query = args[0]
		query = query.replace('`', '"')

		# select from requires ""
		if re.search('from tab', query, flags=re.IGNORECASE):
			query = re.sub('from tab([a-zA-Z]*)', r'from "tab\1"', query, flags=re.IGNORECASE)
		# kwargs['debug'] = True
		return super(PostgresDatabase, self).sql(query, *args, **kwargs)

	def get_tables(self):
		return [d[0] for d in self.sql("""select table_name
			from information_schema.tables
			where table_catalog='{0}'
				and table_type = 'BASE TABLE'
				and table_schema='public'""".format(frappe.conf.db_name))]

	# column type
	def is_type_number(self, code):
		return code == psycopg2.NUMBER

	def is_type_datetime(self, code):
		return code == psycopg2.DATETIME

	# exception type
	def is_deadlocked(self, e):
		return e.pgcode == '40P01'

	def is_timedout(self, e):
		# http://initd.org/psycopg/docs/extensions.html?highlight=datatype#psycopg2.extensions.QueryCanceledError
		return isinstance(e, psycopg2.extensions.QueryCanceledError)

	def is_table_missing(self, e):
		return e.pgcode == '42P01'

	def is_missing_column(self, e):
		return e.pgcode == '42703'

	def is_access_denied(self, e):
		return e.pgcode == '42501'

	def cant_drop_field_or_key(self, e):
		return e.pgcode.startswith('23')

	def is_duplicate_entry(self, e):
		return e.pgcode == '23505'

	def is_primary_key_violation(self, e):
		return e.pgcode == '23505' and '_pkey' in cstr(e.args[0])

	def is_unique_key_violation(self, e):
		return e.pgcode == '23505' and '_key' in cstr(e.args[0])

	def is_duplicate_fieldname(self, e):
		return e.pgcode == '42701'

	def create_auth_table(self):
		frappe.db.sql_ddl("""create table if not exists "__Auth" (
				"doctype" VARCHAR(140) NOT NULL,
				"name" VARCHAR(255) NOT NULL,
				"fieldname" VARCHAR(140) NOT NULL,
				"password" VARCHAR(255) NOT NULL,
				"encrypted" INT NOT NULL DEFAULT 0,
				PRIMARY KEY ("doctype", "name", "fieldname")
			)""")

	def create_global_search_table(self):
		if not '__global_search' in frappe.db.get_tables():
			frappe.db.sql('''create table "__global_search"(
				doctype varchar(100),
				name varchar({0}),
				title varchar({0}),
				content text,
				route varchar({0}),
				published int not null default 0,
				unique (doctype, name))'''.format(frappe.db.VARCHAR_LEN))

	def create_user_settings_table(self):
		frappe.db.sql_ddl("""create table if not exists "__UserSettings" (
			"user" VARCHAR(180) NOT NULL,
			"doctype" VARCHAR(180) NOT NULL,
			"data" TEXT,
			UNIQUE ("user", "doctype")
			)""")

	def create_help_table(self):
		self.sql('''CREATE TABLE "help"(
				"path" varchar(255),
				"content" text,
				"title" text,
				"intro" text,
				"full_path" text)''')
		self.sql('''CREATE INDEX IF NOT EXISTS "help_index" ON "help" ("path")''')

	def updatedb(self, doctype, meta=None):
		"""
		Syncs a `DocType` to the table
		* creates if required
		* updates columns
		* updates indices
		"""
		res = frappe.db.sql("select issingle from `tabDocType` where name='{}'".format(doctype))
		if not res:
			raise Exception('Wrong doctype {0} in updatedb'.format(doctype))

		if not res[0][0]:
			db_table = PostgresTable(doctype, meta)
			db_table.validate()

			frappe.db.commit()
			db_table.sync()
			frappe.db.begin()

	def get_on_duplicate_update(self, key='name'):
		if isinstance(key, list):
			key = '", "'.join(key)
		return 'ON CONFLICT ("{key}") DO UPDATE SET '.format(
			key=key
		)

	def check_transaction_status(self, query):
		pass

	def has_index(self, table_name, index_name):
		return frappe.db.sql("""SELECT 1 FROM pg_indexes WHERE tablename='{table_name}'
			and indexname='{index_name}' limit 1""".format(table_name=table_name, index_name=index_name))

	def add_index(self, doctype, fields, index_name=None):
		"""Creates an index with given fields if not already created.
		Index name will be `fieldname1_fieldname2_index`"""
		index_name = index_name or self.get_index_name(fields)
		table_name = 'tab' + doctype

		frappe.db.commit()
		frappe.db.sql("""CREATE INDEX IF NOT EXISTS "{}" ON `{}`("{}")""".format(index_name, table_name, '", "'.join(fields)))

	def add_unique(self, doctype, fields, constraint_name=None):
		if isinstance(fields, string_types):
			fields = [fields]
		if not constraint_name:
			constraint_name = "unique_" + "_".join(fields)

		if not frappe.db.sql("""select CONSTRAINT_NAME from information_schema.TABLE_CONSTRAINTS
			where table_name=%s and constraint_type='UNIQUE' and CONSTRAINT_NAME=%s""",
			('tab' + doctype, constraint_name)):
				frappe.db.commit()
				frappe.db.sql("""alter table `tab%s`
					add constraint %s unique (%s)""" % (doctype, constraint_name, ", ".join(fields)))

	def get_table_columns_description(self, table_name):
		"""Returns list of column and its description"""
		# pylint: disable=W1401
		return self.sql('''select
			a.column_name as name,
			case a.data_type
				when 'character varying' then concat('varchar(', a.character_maximum_length ,')')
				when 'timestamp without time zone' then 'timestamp'
				else a.data_type
			END as type,
			count(b.indexdef) as Index,
			coalesce(a.column_default, NULL) as default,
			bool_or(b.unique) as unique
			from information_schema.columns a
			left join
			(SELECT indexdef, tablename, indexdef like '%UNIQUE INDEX%' as unique FROM pg_indexes where tablename='{table_name}') b
			on substring(b.indexdef, '\(.*\)') like concat('%', a.column_name, '%')
			where a.table_name = '{table_name}'
			group by a.column_name, a.data_type, a.column_default, a.character_maximum_length;'''
			.format(table_name=table_name), as_dict=1)

	def get_database_list(self, target):
		return [d[0] for d in self.sql("SELECT datname FROM pg_database;")]