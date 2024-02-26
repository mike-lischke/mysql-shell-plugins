# Copyright (c) 2021, 2024 Oracle and/or its affiliates.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License, version 2.0,
# as published by the Free Software Foundation.
#
# This program is designed to work with certain software (including
# but not limited to OpenSSL) that is licensed under separate terms, as
# designated in a particular file or component or in included license
# documentation.  The authors of MySQL hereby grant you an additional
# permission to link the program and your derivative works with the
# separately licensed software that they have either included with
# the program or referenced in the documentation.
#
# This program is distributed in the hope that it will be useful,  but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See
# the GNU General Public License, version 2.0, for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin St, Fifth Floor, Boston, MA 02110-1301 USA

import gui_plugin.core.Error as Error
from gui_plugin.core.dbms.DbSessionTasks import BaseObjectTask, DbQueryTask
from gui_plugin.core.Error import MSGException


class MySQLOneFieldTask(DbQueryTask):
    def process_result(self):
        data = None
        if self.resultset.has_data():
            row = self.resultset.fetch_one()
            data = row[0]

        self.dispatch_result("PENDING", data=data)


class MySQLBaseObjectTask(BaseObjectTask):
    def process_result(self):
        _err_msg = f"The {self.type} '{self.name}' does not exist."
        if self.resultset.has_data():
            row = self.resultset.fetch_one()

            if not row:
                self.dispatch_result("ERROR", message=_err_msg)
            else:
                self.dispatch_result("PENDING", data=self.format(row))
        else:
            self.dispatch_result("ERROR", message=_err_msg)


class MySQLTableObjectTask(BaseObjectTask):
    def format(self, row):
        if row:
            return {"name": row[0]}

        return {"name": ""}

    def process_result(self):
        if self._sql_index == 0:
            _err_msg = f"The table '{self.name}' does not exist."
            if self.resultset.has_data():
                row = self.resultset.fetch_one()

                if not row:
                    self._break = True
                    self.dispatch_result("ERROR", message=_err_msg)
                else:
                    self.dispatch_result("PENDING", data=self.format(row))
            else:
                self._break = True
                self.dispatch_result("ERROR", message=_err_msg)
        else:
            # Process result set
            buffer_size = self.options.get("row_packet_size", 25)

            values = {"columns": []}

            try:
                # Loop over all rows
                for row in self.session.row_generator():
                    if self.session.is_killed():
                        raise MSGException(
                            Error.DB_QUERY_KILLED, "Query killed")

                    # Return chunks of buffer_size a time, if buffer_size is 0
                    # or -1, do not return chunks but only the full result set
                    if buffer_size > 0 and len(values["columns"]) >= buffer_size:
                        # Call the callback
                        self.dispatch_result("PENDING", data=values)
                        values = {"columns": []}

                    values['columns'].append(row[0])
                    self._row_count += 1
            except Exception as e:
                self.dispatch_result("ERROR", message=str(e))
                return

            # Call the callback
            if values['columns']:
                self.dispatch_result("PENDING", data=values)

class MySQLColumnObjectTask(BaseObjectTask):
    def format(self, row):
        return {
            "name": row.get_field("name"),
            "type": row.get_field("type"),
            "not_null": row.get_field("not_null"),
            "default": row.get_field("default"),
            "is_pk": row.get_field("is_pk"),
            "auto_increment": row.get_field("auto_increment"),
        }

    def process_result(self):
        _err_msg = f"The {self.type} '{self.name}' does not exist."
        if self.resultset.has_data():
            row = self.resultset.fetch_one()

            if not row:
                self.dispatch_result("ERROR", message=_err_msg)
            else:
                self.dispatch_result("PENDING", data=self.format(row))
        else:
            self.dispatch_result("ERROR", message=_err_msg)

class MySQLColumnsMetadataTask(DbQueryTask):
    def format(self, row):
        return {
            "schema": row.get_field("schema"),
            "table": row.get_field("table"),
            "name": row.get_field("name"),
            "type": row.get_field("type"),
            "not_null": row.get_field("not_null"),
            "default": row.get_field("default"),
            "is_pk": row.get_field("is_pk"),
            "auto_increment": row.get_field("auto_increment"),
        }

    def process_result(self):
        buffer_size = self.options.get("row_packet_size", 25)
        columns_details = []
        send_empty = True
        if self.resultset.has_data():
            row = self.resultset.fetch_one()
            while row:
                columns_details.append(self.format(row))
                row = self.resultset.fetch_one()

                # Return chunks of buffer_size a time, if buffer_size is 0
                # or -1, do not return chunks but only the full result set
                if not row or (buffer_size > 0 and len(columns_details) >= buffer_size):
                    self.dispatch_result("PENDING", data=columns_details)
                    columns_details = []
                    send_empty = False

        if send_empty or len(columns_details) > 0:
            self.dispatch_result("PENDING", data=columns_details)

class MySQLOneFieldListTask(DbQueryTask):
    def process_result(self):
        buffer_size = self.options.get("row_packet_size", 25)
        name_list = []
        send_empty = True
        if self.resultset.has_data():
            row = self.resultset.fetch_one()
            while row:
                name_list.append(row[0])
                row = self.resultset.fetch_one()

                # Return chunks of buffer_size a time, if buffer_size is 0
                # or -1, do not return chunks but only the full result set
                if not row or (buffer_size > 0 and len(name_list) >= buffer_size):
                    self.dispatch_result("PENDING", data=name_list)
                    name_list = []
                    send_empty = False

        if send_empty or len(name_list) > 0:
            self.dispatch_result("PENDING", data=name_list)
