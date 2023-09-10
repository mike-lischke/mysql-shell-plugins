# Copyright (c) 2023, Oracle and/or its affiliates.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License, version 2.0,
# as published by the Free Software Foundation.
#
# This program is also distributed with certain software (including
# but not limited to OpenSSL) that is licensed under separate terms, as
# designated in a particular file or component or in included license
# documentation.  The authors of MySQL hereby grant you an additional
# permission to link the program and your derivative works with the
# separately licensed software that they have included with MySQL.
# This program is distributed in the hope that it will be useful,  but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See
# the GNU General Public License, version 2.0, for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin St, Fifth Floor, Boston, MA 02110-1301 USA

import mrs_plugin.lib as lib
import antlr4
from mrs_plugin.lib.mrs_parser import MRSListener
from mrs_plugin.lib.mrs_parser import MRSParser
from mrs_plugin.lib.MrsDdlExecutorInterface import MrsDdlExecutorInterface


class MrsDdlListener(MRSListener):

    def __init__(self, mrs_ddl_executor: MrsDdlExecutorInterface, session):
        self.mrs_ddl_executor = mrs_ddl_executor
        self.session = session
        self.mrs_object = {}

    def get_uuid(self):
        return lib.core.convert_id_to_string(
            lib.core.get_sequence_id(self.session))

    # ------------------------------------------------------------------------------------------------------------------
    # Common handlers

    def enterJsonOptions(self, ctx):
        self.mrs_object["options"] = ctx.jsonValue().getText()

    def enterComments(self, ctx):
        self.mrs_object["comments"] = ctx.quotedText().getText()[1:-1]

    def enterEnabledDisabled(self, ctx):
        if ctx.ENABLED_SYMBOL() is not None:
            self.mrs_object["enabled"] = True
        if ctx.DISABLED_SYMBOL() is not None:
            self.mrs_object["enabled"] = False

    def enterAuthenticationRequired(self, ctx):
        # If the NOT keyword is present in (AUTHENTICATION NOT? REQUIRED)?
        # authentication is required
        if ctx.NOT_SYMBOL() is not None:
            self.mrs_object["requires_auth"] = True
        else:
            self.mrs_object["requires_auth"] = False

    def enterItemsPerPage(self, ctx):
        self.mrs_object["items_per_page"] = int(
            ctx.itemsPerPageNumber().getText())

    def enterServiceRequestPath(self, ctx):
        self.mrs_object["url_context_root"] = ctx.requestPathIdentifier(
        ).getText()
        # Check if there was a host:port defined as well
        val = ctx.hostAndPortIdentifier()
        if val is not None:
            self.mrs_object["url_host_name"] = val.getText()

    def enterServiceSchemaSelector(self, ctx):
        self.mrs_object["schema_request_path"] = ctx.schemaRequestPath(
        ).getText()

    # ==================================================================================================================
    # CREATE REST statements

    # ------------------------------------------------------------------------------------------------------------------
    # CREATE REST METADATA

    def enterConfigureRestMetadataStatement(self, ctx):
        self.mrs_object = {
            "current_operation": "CONFIGURE REST METADATA",
            "update_if_available": True if (
                ctx.restMetadataOptions() is not None and
                ctx.restMetadataOptions().updateIfAvailable() is not None) else False
        }

    def exitConfigureRestMetadataStatement(self, ctx):
        self.mrs_ddl_executor.createRestMetadata(self.mrs_object)

    # ------------------------------------------------------------------------------------------------------------------
    # CREATE REST SERVICE

    def enterCreateRestServiceStatement(self, ctx):
        self.mrs_object = {
            "current_operation": (
                "CREATE" if ctx.REPLACE_SYMBOL() is None
                else "CREATE OR REPLACE") + " REST SERVICE",
            "do_replace": ctx.REPLACE_SYMBOL() is not None
        }

    def enterRestProtocol(self, ctx):
        if ctx.HTTP_SYMBOL() is not None and ctx.HTTPS_SYMBOL() is not None:
            self.mrs_object["url_protocol"] = "HTTP,HTTPS"
        elif ctx.HTTP_SYMBOL() is not None:
            self.mrs_object["url_protocol"] = "HTTP"
        elif ctx.HTTPS_SYMBOL() is not None:
            self.mrs_object["url_protocol"] = "HTTPS"

    def enterAuthPath(self, ctx):
        val = ctx.quotedTextOrDefault().getText()
        if val != "DEFAULT":
            self.mrs_object["auth_path"] = val[1:-1]

    def enterAuthRedirection(self, ctx):
        val = ctx.quotedTextOrDefault().getText()
        if val != "DEFAULT":
            self.mrs_object["auth_completed_url"] = val[1:-1]

    def enterAuthValidation(self, ctx):
        val = ctx.quotedTextOrDefault().getText()
        if val != "DEFAULT":
            self.mrs_object["auth_completed_url_validation"] = val[1:-1]

    def enterAuthPageContent(self, ctx):
        val = ctx.quotedTextOrDefault().getText()
        if val != "DEFAULT":
            self.mrs_object["auth_completed_page_content"] = val[1:-1]

    def enterUserManagementSchema(self, ctx):
        val = ctx.schemaName()
        if val is not None:
            self.mrs_object["custom_metadata_schema"] = val.strip("`")

    def exitCreateRestServiceStatement(self, ctx):
        self.mrs_ddl_executor.createRestService(self.mrs_object)

    # ------------------------------------------------------------------------------------------------------------------
    # CREATE REST SCHEMA

    def enterCreateRestSchemaStatement(self, ctx):
        self.mrs_object = {
            "current_operation": (
                "CREATE" if ctx.REPLACE_SYMBOL() is None
                else "CREATE OR REPLACE") + " REST SCHEMA",
            "do_replace": ctx.REPLACE_SYMBOL() is not None,
            "schema_name": ctx.schemaName().getText()[1:-1],
            "schema_request_path": (
                ctx.schemaRequestPath().getText()
                if ctx.schemaRequestPath() is not None
                else f'/{lib.core.unquote(ctx.schemaName().getText())}')
        }

    def exitCreateRestSchemaStatement(self, ctx):
        self.mrs_ddl_executor.createRestSchema(self.mrs_object)

    # ------------------------------------------------------------------------------------------------------------------
    # CREATE REST VIEW

    def get_db_object_fields(self, object_id, db_schema_name, db_object_name):
        # Get the actual columns with references
        columns = lib.db_objects.get_table_columns_with_references(
            session=self.session, schema_name=db_schema_name,
            db_object_name=db_object_name)

        parent_reference_stack = self.mrs_object.get(
            "parent_reference_stack")
        if len(parent_reference_stack) > 0:
            parent_reference_id = parent_reference_stack[-1].get(
                "object_reference").get("id")
        else:
            parent_reference_id = None

        # Convert to object_fields and disable all to begin with
        fields = []
        for column in columns:
            db_column = column.get("db_column")
            fields.append({
                "id": self.get_uuid(),
                "object_id": object_id,
                "parent_reference_id": parent_reference_id,
                "name": lib.core.convert_snake_to_camel_case(column.get("name")),
                "position": column.get("position"),
                "db_column": column.get("db_column"),
                "enabled": False,
                "allow_filtering": True,
                # Only allow sorting for top level fields
                "allow_sorting": (
                    len(parent_reference_stack) == 0
                    and db_column is not None
                    and (
                        db_column.get("isPrimary") is not None
                        or db_column.get("isUnique") is not None
                    )),
                "no_check": False,
                "no_update": False,
                "sdk_options": None,
                "comments": None,
                "reference_mapping": column.get("reference_mapping")
            })

        return fields

    def get_db_object(self, ctx):
        if ctx.serviceSchemaSelector() is not None:
            schema_request_path = ctx.serviceSchemaSelector().schemaRequestPath().getText()
            url_context_root = None
            url_host_name = None

            if ctx.serviceSchemaSelector().serviceRequestPath() is not None:
                url_context_root = ctx.serviceSchemaSelector(
                ).serviceRequestPath().requestPathIdentifier().getText()
                if ctx.serviceSchemaSelector().serviceRequestPath().hostAndPortIdentifier() is not None:
                    url_host_name = ctx.serviceSchemaSelector(
                    ).serviceRequestPath().hostAndPortIdentifier().getText()
        else:
            schema_request_path = self.mrs_object.get("schema_request_path")
            url_context_root = self.mrs_object.get("url_context_root")
            url_host_name = self.mrs_object.get("url_host_name")

        if schema_request_path is None:
            schema_id = self.mrs_ddl_executor.get_current_schema_id()
            if schema_id is None:
                raise Exception("No REST schema given.")
        else:
            if url_context_root is None:
                raise Exception("No REST service given.")

            service = lib.services.get_service(
                session=self.session,
                url_context_root=url_context_root,
                url_host_name=url_host_name)
            if service is None:
                raise Exception(
                    f"The REST service `{url_host_name}{url_context_root}` was not found.")

            schema = lib.schemas.get_schema(
                session=self.session,
                service_id=service["id"],
                request_path=schema_request_path)

            if schema is None:
                raise Exception(
                    f"""The REST schema `{
                        url_host_name if url_host_name is not None else ''}{
                            url_context_root if url_context_root is not None else ''}{
                                schema_request_path if schema_request_path is not None else ''
                                }` was not found.""")
            schema_id = schema["id"]

        db_object = lib.db_objects.get_db_object(
            session=self.session,
            schema_id=schema_id,
            request_path=self.mrs_object.get("request_path"))
        if db_object is None:
            raise Exception(
                f'''REST object `{url_host_name}{url_context_root}{
                    schema_request_path}{
                        self.mrs_object.get("request_path")}` was not found.''')

        return db_object

    def set_schema_name_and_name(self, ctx):
        # If no schema name nor name was given, look it up from existing db_object
        if ctx.qualifiedIdentifier() is None:
            db_object = self.get_db_object(ctx=ctx)

            self.mrs_object["name"] = db_object.get("name")
            self.mrs_object["schema_name"] = db_object.get("schema_name")
        # If no db schema name was given, get the schema name from the current REST schema
        elif ctx.qualifiedIdentifier().dotIdentifier() is None:
            self.mrs_object["name"] = ctx.qualifiedIdentifier().getText()

            if self.current_schema_id is None:
                raise Exception(
                    f'The database schema was not given for `{self.mrs_object["name"]}`')

            schema = lib.schemas.get_schema(
                session=self.session, schema_id=self.current_schema_id)
            if schema is not None:
                self.mrs_object["schema_name"] = schema.get("name")
            else:
                raise Exception(
                    f'The database schema was not found for `{self.mrs_object["name"]}`')
        else:
            self.mrs_object["name"] = ctx.qualifiedIdentifier(
            ).dotIdentifier().identifier().getText().strip("`")
            self.mrs_object["schema_name"] = ctx.qualifiedIdentifier(
            ).identifier().getText().strip("`")

    def enterCreateRestViewStatement(self, ctx):
        self.mrs_object = {
            "current_operation": f"""CREATE{
                '' if ctx.REPLACE_SYMBOL() is None else ' OR REPLACE'
                } REST DUALITY VIEW""",
            "do_replace": ctx.REPLACE_SYMBOL() is not None,
            "id": self.get_uuid(),
            "request_path": ctx.viewRequestPath().requestPathIdentifier().getText(),
            "crud_operations": self.build_crud_operations_list(
                ctx=ctx.graphGlCrudOptions()),
            "parent_reference_stack": []
        }

        self.set_schema_name_and_name(ctx=ctx)

        self.mrs_object["db_object_type"] = "TABLE" if (
            lib.db_objects.db_schema_object_is_table(
                session=self.session,
                db_schema_name=self.mrs_object["schema_name"],
                db_object_name=self.mrs_object["name"])
        ) else "VIEW"

        object_id = self.get_uuid()
        self.mrs_object["objects"] = [{
            "id": object_id,
            "db_object_id": self.mrs_object.get("id"),
            "name": ctx.restObjectName().identifier().getText(),
            "kind": "RESULT",
            "position": 0,
            # Get top level fields
            "fields": self.get_db_object_fields(
                object_id=object_id,
                db_schema_name=self.mrs_object["schema_name"],
                db_object_name=self.mrs_object["name"])
        }]

    def enterRestViewMediaType(self, ctx):
        if ctx.quotedText() is not None:
            self.mrs_object["media_type"] = ctx.quotedText().getText()[1:-1]
        elif ctx.AUTODETECT_SYMBOL() is not None:
            self.mrs_object["media_type_autodetect"] = True

    def enterRestViewFormat(self, ctx):
        if ctx.FEED_SYMBOL() is not None:
            self.mrs_object["format"] = "FEED"
        elif ctx.ITEM_SYMBOL() is not None:
            self.mrs_object["format"] = "ITEM"
        elif ctx.MEDIA_SYMBOL() is not None:
            self.mrs_object["format"] = "MEDIA"

    def enterRestViewAuthenticationProcedure(self, ctx):
        self.mrs_object["auth_stored_procedure"] = ctx.qualifiedIdentifier(
        ).getText()

    def build_crud_operations_list(self, ctx: MRSParser.GraphGlCrudOptionsContext):
        crud_list = ["READ"]

        if ctx is None:
            return crud_list

        # cSpell:ignore NOSELECT NOINSERT NOUPDATE NODELETE
        if (ctx.AT_NOSELECT_SYMBOL(0) is not None) and "READ" in crud_list:
            crud_list.remove("READ")
        if (ctx.AT_INSERT_SYMBOL(0) is not None) and "CREATE" not in crud_list:
            crud_list.append("CREATE")
        if (ctx.AT_NOINSERT_SYMBOL(0) is not None) and "CREATE" in crud_list:
            crud_list.remove("CREATE")
        if (ctx.AT_UPDATE_SYMBOL(0) is not None) and "UPDATE" not in crud_list:
            crud_list.append("UPDATE")
        if (ctx.AT_NOUPDATE_SYMBOL(0) is not None) and "UPDATE" in crud_list:
            crud_list.remove("UPDATE")
        if (ctx.AT_DELETE_SYMBOL(0) is not None) and "DELETE" not in crud_list:
            crud_list.append("DELETE")
        if (ctx.AT_NODELETE_SYMBOL(0) is not None) and "DELETE" in crud_list:
            crud_list.remove("DELETE")

        return crud_list

    def enterRestProcedureResult(self, ctx):
        # A REST PROCEDURE can have multiple results
        graph_gl_object_count = self.mrs_object.get(
            "graph_gl_object_count", 0) + 1
        self.mrs_object["graph_gl_object_count"] = graph_gl_object_count

        # Add a new mrs object for each RESULT
        self.mrs_object["objects"].append({
            "id": self.get_uuid(),
            "db_object_id": self.mrs_object.get("id"),
            "name": ctx.restResultName().getText(),
            "kind": "RESULT",
            "position": graph_gl_object_count,
            "fields": []
        })

    def enterGraphGlPair(self, ctx):
        objects = self.mrs_object["objects"]
        current_object = objects[-1]
        fields = current_object["fields"]
        field_name = lib.core.unquote(ctx.graphKeyValue().getText())

        # If this is not a qualified identifier, it's a column
        if ctx.qualifiedIdentifier().dotIdentifier() is None:
            db_column_name = ctx.qualifiedIdentifier().getText().strip("`")

            # Check if this is a REST PROCEDURE RESULT
            graph_gl_object_count = self.mrs_object.get(
                "graph_gl_object_count", 0)
            if graph_gl_object_count == 0:
                # A REST VIEW RESULT or REST PROCEDURE PARAMETERS
                for field in fields:
                    db_column = field.get("db_column")
                    if db_column is not None and db_column.get("name") == db_column_name:
                        field["name"] = field_name
                        field["enabled"] = True

                        # cSpell:ignore NOCHECK NOFILTERING ROWOWNERSHIP
                        if ctx.AT_NOCHECK_SYMBOL() is not None:
                            field["no_check"] = True
                        if ctx.AT_SORTABLE_SYMBOL() is not None:
                            field["allow_sorting"] = True
                        if ctx.AT_NOFILTERING_SYMBOL() is not None:
                            field["allow_filtering"] = False
                        if (ctx.graphGlCrudOptions() is not None
                                and ctx.graphGlCrudOptions().AT_NOUPDATE_SYMBOL() is not None):
                            field["no_update"] = True
                        if ctx.AT_ROWOWNERSHIP_SYMBOL() is not None:
                            self.mrs_object["row_user_ownership_enforced"] = True
                            self.mrs_object["row_user_ownership_column"] = db_column_name
                        if ctx.AT_DATATYPE_SYMBOL() is not None:
                            db_column["datatype"] = lib.core.unquote(
                                ctx.graphGlDatatypeValue().getText().lower())
                        break
                else:
                    raise Exception(
                        f'The column `{db_column_name}` does not exist on '
                        f'`{self.mrs_object.get("schema_name")}`.`{self.mrs_object.get("name")}`.')
            else:
                # A REST PROCEDURE RESULT
                fields.append({
                    "id": self.get_uuid(),
                    "object_id": self.mrs_object.get("objects")[graph_gl_object_count].get("id"),
                    "name": field_name,
                    "position": len(fields),
                    "db_column": {
                        "name": db_column_name,
                        "datatype": lib.core.unquote(
                            ctx.graphGlDatatypeValue().getText().lower()
                        ) if ctx.AT_DATATYPE_SYMBOL() else "varchar(45)"
                    },
                    "enabled": True,
                    "allow_filtering": True,
                    "allow_sorting": False,
                    "no_check": False,
                    "no_update": False
                })

                current_object["fields"] = fields

        else:
            db_schema_name = ctx.qualifiedIdentifier(
            ).identifier().getText().strip("`")
            db_object_name = ctx.qualifiedIdentifier(
            ).dotIdentifier().identifier().getText().strip("`")

            ref_mapping = None
            for field in fields:
                ref_mapping = field.get("reference_mapping")
                if (ref_mapping is not None and
                        ref_mapping.get("referenced_schema") == db_schema_name and
                        ref_mapping.get("referenced_table") == db_object_name and
                        field["enabled"] == False):
                    field["name"] = field_name
                    field["enabled"] = True

                    # Build object_reference
                    obj_reference_id = self.get_uuid()
                    obj_reference = {
                        "id": obj_reference_id,
                        "reference_mapping": ref_mapping,
                        "crud_operations": ",".join(self.build_crud_operations_list(
                            ctx.graphGlCrudOptions())),
                        "unnest": ctx.AT_UNNEST_SYMBOL() is not None
                    }

                    field["object_reference"] = obj_reference
                    field["represents_reference_id"] = obj_reference_id

                    self.mrs_object.get("parent_reference_stack").append({
                        "object_reference": obj_reference,
                        "referenced_fields_offset": len(fields)
                    })

                    # Get referenced fields as well
                    ref_fields = self.get_db_object_fields(
                        object_id=current_object.get("id"),
                        db_schema_name=db_schema_name,
                        db_object_name=db_object_name)

                    # Append them to the fields list
                    current_object["fields"] = fields + ref_fields

                    break
            else:
                raise Exception(
                    f'The table `{db_schema_name}`.`{db_object_name}` has no reference to '
                    f'`{self.mrs_object.get("schema_name")}`.`{self.mrs_object.get("name")}`.')

    def exitGraphGlPair(self, ctx):
        if ctx.qualifiedIdentifier().dotIdentifier() is not None:
            # Remove last reference_id
            ref_stack = self.mrs_object.get("parent_reference_stack")
            if len(ref_stack) > 0:
                parent_ref = ref_stack.pop()
            else:
                parent_ref = None

            if parent_ref is not None and ctx.AT_REDUCETO_SYMBOL() is not None:
                reduce_to = lib.core.unquote(
                    ctx.graphGlReduceToValue().getText().lower())

                objects = self.mrs_object["objects"]
                current_object = objects[-1]
                fields = current_object.get("fields")
                ref_fields_offset = parent_ref.get("referenced_fields_offset")
                obj_reference = parent_ref.get("object_reference")

                for i, reduce_to_field in enumerate(fields):
                    # Ignore all higher level fields and only consider referenced fields
                    if i < ref_fields_offset:
                        continue

                    if (reduce_to_field.get("name").lower() == reduce_to):
                        obj_reference[
                            "reduce_to_value_of_field_id"] = reduce_to_field.get("id")
                        break
                else:
                    raise Exception(
                        f'The column `{reduce_to}` defined for a reduce operation was not found.')

    def exitCreateRestViewStatement(self, ctx):
        self.mrs_ddl_executor.createRestDbObject(self.mrs_object)

    # ------------------------------------------------------------------------------------------------------------------
    # CREATE REST PROCEDURE

    def add_rest_procedure_params(self, ctx, db_schema_name, db_object_name):
        object_id = self.get_uuid()

        params = lib.db_objects.get_db_object_parameters(
            session=self.session,
            db_schema_name=db_schema_name,
            db_object_name=db_object_name)

        param_fields = []
        for param in params:
            param_name = lib.core.convert_snake_to_camel_case(
                param.get("name"))
            field = {
                "id": self.get_uuid(),
                "object_id": object_id,
                "name": param_name,
                "position": param.get("position"),
                "db_column": {
                    "name": param.get("name"),
                    "in": "IN" in param.get("mode"),
                    "out": "OUT" in param.get("mode"),
                    "datatype": param.get("datatype"),
                    "not_null": True,
                    "is_generated": False,
                    "is_primary": False,
                    "is_unique": False,
                },
                "enabled": True,
                "allow_filtering": True,
                "allow_sorting": False,
                "no_check": False,
                "no_update": False
            }
            param_fields.append(field)

        self.mrs_object["objects"] = [{
            "id": object_id,
            "db_object_id": self.mrs_object["id"],
            "name": ctx.restObjectName().identifier().getText(),
            "kind": "PARAMETERS",
            "position": 0,
            "fields": param_fields
        }]

    def enterCreateRestProcedureStatement(self, ctx):
        self.mrs_object = {
            "current_operation": (
                "CREATE" if ctx.REPLACE_SYMBOL() is None
                else "CREATE OR REPLACE") + " REST PROCEDURE",
            "do_replace": ctx.REPLACE_SYMBOL() is not None,
            "id": self.get_uuid(),
            "request_path": ctx.procedureRequestPath().getText(),
            "db_object_type": "PROCEDURE",
            "crud_operations": ["UPDATE"]
        }

        self.set_schema_name_and_name(ctx=ctx)

        self.add_rest_procedure_params(
            ctx=ctx,
            db_schema_name=self.mrs_object["schema_name"],
            db_object_name=self.mrs_object["name"])

    def exitCreateRestProcedureStatement(self, ctx):
        self.mrs_ddl_executor.createRestDbObject(self.mrs_object)

    # ==================================================================================================================
    # ALTER REST Statements

    # ------------------------------------------------------------------------------------------------------------------
    # ALTER REST SERVICE

    def enterAlterRestServiceStatement(self, ctx):
        self.mrs_object = {
            "current_operation": "ALTER REST SERVICE"
        }

    def enterNewServiceRequestPath(self, ctx):
        self.mrs_object["new_url_context_root"] = ctx.requestPathIdentifier(
        ).getText()
        # Check if there was a host:port defined as well
        val = ctx.hostAndPortIdentifier()
        if val is not None:
            self.mrs_object["new_url_host_name"] = val.getText()

    def exitAlterRestServiceStatement(self, ctx):
        self.mrs_ddl_executor.alterRestService(self.mrs_object)

    # ------------------------------------------------------------------------------------------------------------------
    # ALTER REST SCHEMA

    def enterAlterRestSchemaStatement(self, ctx):
        self.mrs_object = {
            "current_operation": "ALTER REST SCHEMA"
        }

    def enterNewSchemaRequestPath(self, ctx):
        self.mrs_object["new_request_path"] = ctx.requestPathIdentifier(
        ).getText()

    def exitAlterRestSchemaStatement(self, ctx):
        self.mrs_ddl_executor.alterRestSchema(self.mrs_object)

    # ------------------------------------------------------------------------------------------------------------------
    # ALTER REST VIEW

    def enterAlterRestViewStatement(self, ctx):
        self.mrs_object = {
            "current_operation": "ALTER REST VIEW",
            "request_path": ctx.viewRequestPath().requestPathIdentifier().getText(),
            "new_request_path": (
                ctx.newViewRequestPath().requestPathIdentifier().getText()
                if ctx.newViewRequestPath() is not None else None),
            "new_object_name": (
                ctx.restObjectName().identifier().getText()
                if ctx.restObjectName() is not None else None),
            "type": "DUALITY VIEW",
            "parent_reference_stack": []
        }

        if ctx.graphGlCrudOptions() is not None:
            self.mrs_object["crud_operations"] = self.build_crud_operations_list(
                ctx=ctx.graphGlCrudOptions())

        db_object = self.get_db_object(ctx=ctx)

        # Set mrs_object["id"] since the field listener need that
        self.mrs_object["id"] = db_object["id"]

        if ctx.restObjectName() is not None:
            object_id = self.get_uuid()
            self.mrs_object["objects"] = [{
                "id": object_id,
                "db_object_id": db_object["id"],
                "name": ctx.restObjectName().identifier().getText(),
                "kind": "RESULT",
                "position": 0,
                # Get top level fields
                "fields": self.get_db_object_fields(
                    object_id=object_id,
                    db_schema_name=db_object["schema_name"],
                    db_object_name=db_object["name"])
            }]

    def exitAlterRestViewStatement(self, ctx):
        self.mrs_ddl_executor.alterRestDbObject(self.mrs_object)

    # ------------------------------------------------------------------------------------------------------------------
    # ALTER REST PROCEDURE

    def enterAlterRestProcedureStatement(self, ctx):
        self.mrs_object = {
            "current_operation": "ALTER REST PROCEDURE",
            "request_path": ctx.procedureRequestPath().getText(),
            "new_request_path": (
                ctx.newProcedureRequestPath().requestPathIdentifier().getText()
                if ctx.newProcedureRequestPath() is not None else None),
            "new_object_name": (
                ctx.restObjectName().identifier().getText()
                if ctx.restObjectName() is not None else None),
            "type": "PROCEDURE"
        }

        db_object = self.get_db_object(ctx=ctx)

        # Set mrs_object["id"] since the field listener need that
        self.mrs_object["id"] = db_object["id"]

        if ctx.restObjectName() is not None:
            self.add_rest_procedure_params(
                ctx=ctx,
                db_schema_name=db_object["schema_name"],
                db_object_name=db_object["name"])

    def exitAlterRestProcedureStatement(self, ctx):
        self.mrs_ddl_executor.alterRestDbObject(self.mrs_object)

    # ==================================================================================================================
    # DROP REST Statements

    # ------------------------------------------------------------------------------------------------------------------
    # DROP REST SERVICE

    def enterDropRestServiceStatement(self, ctx):
        self.mrs_object = {
            "current_operation": "DROP REST SERVICE"
        }

    def exitDropRestServiceStatement(self, ctx):
        self.mrs_ddl_executor.dropRestService(self.mrs_object)

    # ------------------------------------------------------------------------------------------------------------------
    # DROP REST SCHEMA

    def enterDropRestSchemaStatement(self, ctx):
        self.mrs_object = {
            "current_operation": "DROP REST SCHEMA",
            "request_path": ctx.schemaRequestPath().getText()
        }

    def exitDropRestSchemaStatement(self, ctx):
        self.mrs_ddl_executor.dropRestSchema(self.mrs_object)

    # ------------------------------------------------------------------------------------------------------------------
    # DROP REST VIEW

    def enterDropRestDualityViewStatement(self, ctx):
        self.mrs_object = {
            "current_operation": "DROP REST VIEW",
            "request_path": ctx.viewRequestPath().getText(),
            "type": "DUALITY VIEW"
        }

    def exitDropRestDualityViewStatement(self, ctx):
        self.mrs_ddl_executor.dropRestDbObject(self.mrs_object)

    # ------------------------------------------------------------------------------------------------------------------
    # DROP REST PROCEDURE

    def enterDropRestProcedureStatement(self, ctx):
        self.mrs_object = {
            "current_operation": "DROP REST PROCEDURE",
            "request_path": ctx.procedureRequestPath().getText(),
            "type": "PROCEDURE"
        }

    def exitDropRestProcedureStatement(self, ctx):
        self.mrs_ddl_executor.dropRestDbObject(self.mrs_object)

    # ==================================================================================================================
    # USE REST Statement

    def enterUseStatement(self, ctx):
        self.mrs_object = {
            "current_operation": (
                "USE REST " +
                "SERVICE" if (
                    ctx.serviceAndSchemaRequestPaths().schemaRequestPath() is None
                ) else "SCHEMA"),
            "schema_request_path":
                ctx.serviceAndSchemaRequestPaths().schemaRequestPath().getText()
                if (ctx.serviceAndSchemaRequestPaths().schemaRequestPath() is not None)
                else None
        }

    def exitUseStatement(self, ctx):
        self.mrs_ddl_executor.use(self.mrs_object)

    # ==================================================================================================================
    # SHOW REST Statements

    # ------------------------------------------------------------------------------------------------------------------
    # SHOW REST METADATA STATUS

    def enterShowRestMetadataStatusStatement(self, ctx):
        self.mrs_object = {
            "current_operation": "SHOW REST METADATA STATUS"
        }

    def exitShowRestMetadataStatusStatement(self, ctx):
        self.mrs_ddl_executor.showRestMetadataStatus(self.mrs_object)

    # ------------------------------------------------------------------------------------------------------------------
    # SHOW REST SERVICES

    def enterShowRestServicesStatement(self, ctx):
        self.mrs_object = {
            "current_operation": "SHOW REST SERVICES"
        }

    def exitShowRestServicesStatement(self, ctx):
        self.mrs_ddl_executor.showRestServices(self.mrs_object)

    # ------------------------------------------------------------------------------------------------------------------
    # SHOW REST SCHEMAS

    def enterShowRestSchemasStatement(self, ctx):
        self.mrs_object = {
            "current_operation": "SHOW REST SCHEMAS"
        }

    def exitShowRestSchemasStatement(self, ctx):
        self.mrs_ddl_executor.showRestSchemas(self.mrs_object)

    # ------------------------------------------------------------------------------------------------------------------
    # SHOW REST VIEWS

    def enterShowRestViewsStatement(self, ctx):
        self.mrs_object = {
            "current_operation": "SHOW REST VIEWS",
            "object_types": ["TABLE", "VIEW"]
        }

    def exitShowRestViewsStatement(self, ctx):
        self.mrs_ddl_executor.showRestDbObjects(self.mrs_object)

    # ------------------------------------------------------------------------------------------------------------------
    # SHOW REST PROCEDURES

    def enterShowRestProceduresStatement(self, ctx):
        self.mrs_object = {
            "current_operation": "SHOW REST PROCEDURES",
            "object_types": ["PROCEDURE"]
        }

    def exitShowRestProceduresStatement(self, ctx):
        self.mrs_ddl_executor.showRestDbObjects(self.mrs_object)

    # ------------------------------------------------------------------------------------------------------------------
    # SHOW CREATE REST SERVICE

    def enterShowCreateRestServiceStatement(self, ctx):
        self.mrs_object = {
            "current_operation":
                "SHOW CREATE REST SERVICE"
        }

    def exitShowCreateRestServiceStatement(self, ctx):
        self.mrs_ddl_executor.showCreateRestService(self.mrs_object)

    # ------------------------------------------------------------------------------------------------------------------
    # SHOW CREATE REST SCHEMA

    def enterShowCreateRestSchemaStatement(self, ctx):
        self.mrs_object = {
            "current_operation":
                "SHOW CREATE REST SCHEMA"
        }

    def exitShowCreateRestSchemaStatement(self, ctx):
        self.mrs_ddl_executor.showCreateRestSchema(self.mrs_object)

    # ------------------------------------------------------------------------------------------------------------------
    # SHOW CREATE REST VIEW

    def enterShowCreateRestViewStatement(self, ctx):
        self.mrs_object = {
            "current_operation":
                "SHOW CREATE REST VIEW",
            "request_path": ctx.viewRequestPath().getText(),
            "type": "DUALITY VIEW"
        }

    def exitShowCreateRestViewStatement(self, ctx):
        self.mrs_ddl_executor.showCreateRestDbObject(self.mrs_object)

    # ------------------------------------------------------------------------------------------------------------------
    # SHOW CREATE REST PROCEDURE

    def enterShowCreateRestProcedureStatement(self, ctx):
        self.mrs_object = {
            "current_operation":
                "SHOW CREATE REST PROCEDURE",
            "request_path": ctx.procedureRequestPath().getText(),
            "type": "PROCEDURE"
        }

    def exitShowCreateRestProcedureStatement(self, ctx):
        self.mrs_ddl_executor.showCreateRestDbObject(self.mrs_object)


class MrsDdlErrorListener(antlr4.error.ErrorListener.ErrorListener):
    def __init__(self, errors):
        self.errors = errors

    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        self.errors.append({
            "line": line,
            "column": column,
            "message": msg.capitalize(),
            "fullMessage": f"Syntax Error: {msg.capitalize()} [Ln {line}: Col {column}]"
        })
