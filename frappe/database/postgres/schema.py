import frappe
from frappe.database.schema import DBTable

class PostgresTable(DBTable):
	# def __init__(self, doctype, meta=None):
	# 	self.doctype = doctype
	# 	self.table_name = 'tab{}'.format(doctype)
	# 	self.meta = meta or frappe.get_meta(doctype)

	# def sync(self):
	# 	if frappe.db.table_exists(self.doctype):
	# 		print('\n\n\n'+self.doctype+'\n\n\n')
	# 		pass
	# 		#current_table = self.get_as_docfields()
	# 	else:
	# 		self.create_table()

	# def get_as_docfields(self):
	# 	docfields = []
	# 	columns = frappe.db.sql("""select table_name, column_name, data_type, column_default
	# 		from information_schema.columns where table_name='{0}'""".format(self.table_name), as_dict=1)
	# 	for column in columns:
	# 		docfields.append(dict(
	# 			fieldname = column.column_name,
	# 			column_type = column.data_type,
	# 			parent = column.table_name,
	# 			default = column.default
	# 		))
	# 	return docfields

	def create_table(self):
		# add_text = ''
		# create table
		frappe.db.sql("""CREATE TABLE "{name}" (
			"name" varchar({varchar_len}) NOT NULL,
			"creation" timestamp(6) DEFAULT NULL,
			"modified" timestamp(6) DEFAULT NULL,
			"modified_by" varchar({varchar_len}) DEFAULT NULL,
			"owner" varchar({varchar_len}) DEFAULT NULL,
			"docstatus" smallint NOT NULL DEFAULT 0,
			"parent" varchar({varchar_len}) DEFAULT NULL,
			"parentfield" varchar({varchar_len}) DEFAULT NULL,
			"parenttype" varchar({varchar_len}) DEFAULT NULL,
			"idx" bigint NOT NULL DEFAULT 0,
			{columns}
		)""".format(
			name=self.table_name,
			columns = self.get_column_definitions(),
			varchar_len = frappe.db.VARCHAR_LEN))

	# def get_column_definitions(self):
	# 	columns_definitions = []
	# 	for field in self.meta.fields:
	# 		columns_definitions.append(self.get_column_definition(field))

	# 	columns_definitions = filter(None, columns_definitions)
	# 	return ', '.join(columns_definitions)

	# def get_column_definition(self, field):
	# 	if field.fieldtype in frappe.db.type_map:
	# 		column_type, default_length = frappe.db.type_map[field.fieldtype]
	# 		length = field.length or default_length
	# 		return self.get_standard_definition(field, column_type, length)
	# 	else:
	# 		return None

	# def get_standard_definition(self, field, column_type, length=None):
	# 	print(field, column_type, length)
	#
	# '"{fieldname}" {column_type}{length} {null} {default}'.format(
	# 		fieldname = field.fieldname,
	# 		column_type = column_type,
	# 		length = '({})'.format(length) if length else '',
	# 		default = 'DEFAULT {}'.format(frappe.db.escape(field.default)) if field.default else '',
	# 		null = 'NOT NULL' if field.reqd else ''
	# 	))
	# 	return '"{fieldname}" {column_type}{length} {null} {default}'.format(
	# 		fieldname = field.fieldname,
	# 		column_type = column_type,
	# 		length = '({})'.format(length) if length and column_type != 'text' else '',
	# 		default = 'DEFAULT {}'.format(frappe.db.escape(field.default)) if field.default else '',
	# 		null = 'NOT NULL' if field.reqd else ''
	# 	)

	# def sync_doctype(self):
	#     pass

	# def get_columns(self):
	#     pass

	# def get_definition(self, fieldtype, precision):
	#     pass

	# def add_column(self, column_name, fieldtype, precision=None):
	#     if column_name in self.get_columns():
	#         # already exists
	#         return

	#     frappe.db.commit()
	#     frappe.db.sql("alter table `tab{0}` add column {1} {2}".format(self.table_name,
	#         column_name, self.get_definition(fieldtype, precision)))