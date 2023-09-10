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
from mrs_plugin.lib.MrsDdlExecutorInterface import MrsDdlExecutorInterface
import json


def cutLastComma(fields):
    # Cut the last , away if present
    if fields.endswith(",\n"):
        return fields[:-2]

    # Otherwise, just cut the last \n
    return fields[:-1]


def walk(fields, parent_id=None, level=1, add_data_type=False, current_object=None):
    result = ""
    filtered_fields = list(filter(lambda f: f.get(
        "reduceToValueOfFieldId", {}).get("reduce_to_value_of_field_id"), fields))
    reduce_to_field_ids = [f.get("reduceToValueOfFieldId", {}).get(
        "reduce_to_value_of_field_id", "") for f in filtered_fields]

    indent = " " * level * 4

    for field in fields:
        if field.get("parent_reference_id") != parent_id:
            continue

        if not field.get("object_reference") and (field["enabled"] or field["id"] in reduce_to_field_ids):
            attributes = []
            inout = f'@{"IN" if field["db_column"].get("in") else ""}{"OUT" if field["db_column"].get("out") else ""}'
            inout != "@" and attributes.append(inout)
            field.get("no_check") and attributes.append("@NOCHECK")
            field.get("no_update") and attributes.append("@NOUPDATE")
            field.get("allow_sorting") and attributes.append("@SORTABLE")
            not field.get("allow_filtering") and attributes.append(
                "@NOFILTERING")
            add_data_type and field["db_column"] and field["db_column"]["datatype"] and \
                attributes.append(
                    f'@DATATYPE("{field["db_column"]["datatype"]}")')

            field["db_column"].get("name") == current_object.get("row_user_ownership_column") and \
                current_object.get("row_user_ownership_enforced") and \
                attributes.append("@ROWOWNERSHIP")

            result += f"{indent}{field['name']}: {field['db_column']['name']}"
            if attributes:
                result = f"{result} {' '.join(attributes)}"
            result = f"{result},\n"
        elif field.get("object_reference") and field["object_reference"].get("unnest") or field["enabled"]:
            ref_table = f'{field["object_reference"]["reference_mapping"]["referenced_schema"]}.{field["object_reference"]["reference_mapping"]["referenced_table"]}'

            attributes = []
            "CREATE" in field["object_reference"]["crud_operations"] and attributes.append(
                "@INSERT")
            "UPDATE" in field["object_reference"]["crud_operations"] and attributes.append(
                "@UPDATE")
            "DELETE" in field["object_reference"]["crud_operations"] and attributes.append(
                "@DELETE")
            field["object_reference"]["unnest"] and attributes.append(
                "@UNNEST")

            if field["object_reference"].get("reduce_to_value_of_field_id"):
                reduce_to_field = list(filter(lambda f: f["id"] == field["object_reference"].get(
                    "reduce_to_value_of_field_id"), fields))

                if reduce_to_field:
                    attributes.append(
                        f'@REDUCETO({reduce_to_field["db_column"].get("name")})')

            children = cutLastComma(walk(fields=fields, parent_id=field["represents_reference_id"],
                                         level=level + 1, add_data_type=add_data_type, current_object=current_object))

            result = f'{result}{indent}{field["name"]}: {ref_table}'

            if attributes:
                result = f'{result} {" ".join(attributes)}'

            if children:
                result = f"{result} {{\n{children}\n{indent}}}\n"

    return result


class MrsDdlExecutor(MrsDdlExecutorInterface):

    def __init__(self, session,
                 current_service_id=None, current_service=None,
                 current_service_host=None,
                 current_schema_id=None, current_schema=None):
        self.session = session
        self.results = []
        self.current_service_id = current_service_id
        self.current_service = current_service
        self.current_service_host = current_service_host
        self.current_schema_id = current_schema_id
        self.current_schema = current_schema
        self.current_operation = None

    def get_current_service_id(self):
        return self.current_service_id

    def get_current_schema_id(self):
        return self.current_schema_id

    # Check if the current mrs_object includes a services request_path or if a
    # current service has been set via USE REST SERVICE
    def get_given_or_current_service_id(self, mrs_object):
        service_id = None

        # Prefer the given service if specified
        url_context_root = mrs_object.get("url_context_root")

        if url_context_root is None and self.current_service_id is not None:
            service_id = self.current_service_id
            mrs_object["url_context_root"] = self.current_service
            mrs_object["url_host_name"] = self.current_service_host
        elif url_context_root is not None:
            url_host_name = mrs_object.get("url_host_name", "")
            service = lib.services.get_service(
                url_context_root=url_context_root,
                url_host_name=url_host_name,
                session=self.session,
                get_default=False)
            if service is None:
                raise Exception(
                    f"Could not find the REST Service {url_host_name}{url_context_root}.")

            service_id = service.get("id")

        return service_id

    # Check if the current mrs_object includes a schema request_path or if a
    # current schema has been set via USE REST SCHEMA
    def get_given_or_current_schema_id(self, mrs_object):
        schema_id = None

        schema_request_path = mrs_object.get("schema_request_path")
        if schema_request_path is None and self.current_schema_id is not None:
            schema_id = self.current_schema_id
            mrs_object["schema_request_path"] = self.current_schema
            mrs_object["url_context_root"] = self.current_service
            mrs_object["url_host_name"] = self.current_service_host
        elif schema_request_path is not None:
            service_id = self.get_given_or_current_service_id(mrs_object)
            schema = lib.schemas.get_schema(
                service_id=service_id,
                request_path=schema_request_path,
                session=self.session)
            if schema is None:
                full_path = (
                    mrs_object.get("url_host_name", "") +
                    mrs_object.get("url_context_root", "") +
                    schema_request_path)
                raise Exception(f"Could not find the REST Schema {full_path}.")

            schema_id = schema.get("id")

        return schema_id

    def createRestMetadata(self, mrs_object: dict):
        self.current_operation = mrs_object.pop("current_operation")
        try:
            status = lib.general.configure(
                session=self.session,
                enable_mrs=mrs_object.get("enabled"),
                options=mrs_object.get("options"),
                update_if_available=mrs_object.get("update_if_available"))

            self.results.append({
                "statementIndex": len(self.results) + 1,
                "type": "success",
                "message": f"REST metadata updated successfully." if (
                    status.get("schema_changed", False) is True
                ) else f"REST Metadata configured successfully.",
                "operation": self.current_operation
            })
        except Exception as e:
            self.results.append({
                "statementIndex": len(self.results) + 1,
                "type": "error",
                "message": f"Failed to configure the REST metadata. {e}",
                "operation": self.current_operation
            })
            raise

    def createRestService(self, mrs_object):
        self.current_operation = mrs_object.pop("current_operation")
        do_replace = mrs_object.pop("do_replace")
        url_host_name = mrs_object.pop("url_host_name", "")
        full_path = f'{url_host_name}{mrs_object.get("url_context_root", "")}'

        with lib.core.MrsDbTransaction(self.session):
            try:
                # If the OR REPLACE was specified, check if there is an existing service on the same host
                # with the same path and delete it.
                if do_replace is True:
                    service = lib.services.get_service(
                        url_context_root=mrs_object.get(
                            "url_context_root"),
                        url_host_name=url_host_name,
                        get_default=False, session=self.session)
                    if service is not None:
                        lib.services.delete_service(
                            service_id=service.get("id"), session=self.session)

                # Add the service
                service_id = lib.services.add_service(
                    session=self.session,
                    url_host_name=url_host_name,
                    service=mrs_object)

                self.results.append({
                    "statementIndex": len(self.results) + 1,
                    "type": "success",
                    "message": f"REST Service `{full_path}` created successfully.",
                    "operation": self.current_operation,
                    "id": lib.core.convert_id_to_string(service_id)
                })
            except Exception as e:
                self.results.append({
                    "statementIndex": len(self.results) + 1,
                    "type": "error",
                    "message": f"Failed to create the REST Service `{full_path}`. {e}",
                    "operation": self.current_operation
                })
                raise

    def createRestSchema(self, mrs_object: dict):
        self.current_operation = mrs_object.pop("current_operation")
        do_replace = mrs_object.pop("do_replace")

        schema_request_path = mrs_object.get("schema_request_path")
        full_path = schema_request_path

        with lib.core.MrsDbTransaction(self.session):
            try:
                service_id = self.get_given_or_current_service_id(mrs_object)
                if service_id is None:
                    raise Exception("No REST Service specified.")

                full_path = (
                    mrs_object.get("url_host_name", "") +
                    mrs_object.get("url_context_root", "") +
                    schema_request_path)

                # If the OR REPLACE was specified, check if there is an existing schema on the same service
                # and delete it.
                if do_replace is not None:
                    schema = lib.schemas.get_schema(
                        service_id=service_id,
                        request_path=mrs_object.get("request_path"),
                        session=self.session)
                    if schema is not None:
                        lib.schemas.delete_schema(
                            schema_id=schema.get("id"), session=self.session)

                schema_id = lib.schemas.add_schema(
                    schema_name=mrs_object.get("schema_name"),
                    service_id=service_id,
                    request_path=schema_request_path,
                    requires_auth=mrs_object.get("requires_auth"),
                    enabled=mrs_object.get("enabled", 1),
                    items_per_page=mrs_object.get("items_per_page"),
                    comments=mrs_object.get("comments"),
                    options=mrs_object.get("options"),
                    session=self.session)

                self.results.append({
                    "statementIndex": len(self.results) + 1,
                    "type": "success",
                    "message": f"REST Schema `{full_path}` created successfully.",
                    "operation": self.current_operation,
                    "id": lib.core.convert_id_to_string(schema_id)
                })
            except Exception as e:
                self.results.append({
                    "statementIndex": len(self.results) + 1,
                    "type": "error",
                    "message": f"Failed to create the REST Schema `{full_path}`. {e}",
                    "operation": self.current_operation
                })
                raise

    def createRestDbObject(self, mrs_object: dict):
        self.current_operation = mrs_object.pop("current_operation")
        do_replace = mrs_object.pop("do_replace")

        full_path = (
            mrs_object.get("url_host_name", self.current_service_host) +
            mrs_object.get("url_context_root", self.current_service) +
            mrs_object.get("schema_request_path", self.current_schema) +
            mrs_object.get("request_path"))

        type_caption = "DUALITY VIEW" if mrs_object.get(
            "db_object_type") != "PROCEDURE" else "PROCEDURE"

        with lib.core.MrsDbTransaction(self.session):
            try:
                schema_id = self.get_given_or_current_schema_id(mrs_object)
                if schema_id is None:
                    raise Exception("No REST Schema specified.")

                # If the OR REPLACE was specified, check if there is an existing db_object on the same schema
                # and delete it.
                if do_replace is True:
                    db_object = lib.db_objects.get_db_object(
                        schema_id=schema_id,
                        request_path=mrs_object.get("request_path"),
                        session=self.session)
                    if db_object is not None:
                        lib.db_objects.delete_db_object(
                            db_object_id=db_object.get("id"), session=self.session)

                lib.db_objects.add_db_object(
                    session=self.session,
                    schema_id=lib.core.id_to_binary(schema_id, "schema_id"),
                    db_object_name=mrs_object.get("name"),
                    request_path=mrs_object.get("request_path"),
                    db_object_type=mrs_object.get("db_object_type"),
                    enabled=mrs_object.get("enabled", True),
                    items_per_page=mrs_object.get("items_per_page"),
                    requires_auth=mrs_object.get("requires_auth", 1),
                    row_user_ownership_enforced=mrs_object.get(
                        "row_user_ownership_enforced"),
                    row_user_ownership_column=mrs_object.get(
                        "row_user_ownership_column"),
                    crud_operations=mrs_object.get("crud_operations"),
                    crud_operation_format=mrs_object.get("format", "FEED"),
                    comments=mrs_object.get("comments"),
                    media_type=mrs_object.get("media_type"),
                    auto_detect_media_type=mrs_object.get(
                        "media_type_autodetect", False),
                    auth_stored_procedure=mrs_object.get(
                        "auth_stored_procedure"),
                    options=mrs_object.get("options"),
                    db_object_id=lib.core.id_to_binary(
                        mrs_object.get("id"), "db_object_id"),
                    objects=mrs_object.get("objects"))

                self.results.append({
                    "statementIndex": len(self.results) + 1,
                    "type": "success",
                    "message": f"REST {type_caption} `{full_path}` created successfully.",
                    "operation": self.current_operation,
                    "id": mrs_object.get("id")
                })
            except Exception as e:
                self.results.append({
                    "statementIndex": len(self.results) + 1,
                    "type": "error",
                    "message": f"Failed to create the REST{type_caption} `{full_path}`. {e}",
                    "operation": self.current_operation
                })
                raise

    def alterRestService(self, mrs_object: dict):
        self.current_operation = mrs_object.pop("current_operation")
        url_host_name = mrs_object.get(
            "url_host_name", self.current_service_host)
        full_path = f'{url_host_name}{mrs_object.get("url_context_root", self.current_service)}'

        try:
            service_id = self.get_given_or_current_service_id(mrs_object)
            if service_id is None:
                raise Exception("No REST Service specified.")

            # If a new url_context_root / url_host_name was given,
            # overwrite the existing values in the mrs_object
            # so they are set during the update
            new_url_context_root = mrs_object.pop("new_url_context_root")
            new_url_host_name = mrs_object.pop("new_url_host_name")
            if new_url_context_root is not None:
                if new_url_host_name is None:
                    new_url_host_name = ""
                mrs_object["url_context_root"] = new_url_context_root
                mrs_object["url_host_name"] = new_url_host_name

            lib.services.update_services(
                session=self.session,
                service_ids=[service_id],
                value=mrs_object)

            self.results.append({
                "statementIndex": len(self.results) + 1,
                "type": "success",
                "message": f"OK, 1 record updated.",
                "operation": self.current_operation,
                "id": lib.core.convert_id_to_string(service_id)
            })
        except Exception as e:
            self.results.append({
                "statementIndex": len(self.results) + 1,
                "type": "error",
                "message": f"Failed to update the REST Service `{full_path}`. {e}",
                "operation": self.current_operation
            })
            raise

    def alterRestSchema(self, mrs_object: dict):
        self.current_operation = mrs_object.pop("current_operation")
        url_host_name = mrs_object.get(
            "url_host_name", self.current_service_host)
        full_path = f'{url_host_name}{mrs_object.get("url_context_root", self.current_service)}{mrs_object.get("schema_request_path")}'

        try:
            service_id = self.get_given_or_current_service_id(mrs_object)
            if service_id is None:
                raise Exception("No REST Service specified.")

            schema = lib.schemas.get_schema(
                service_id=service_id,
                request_path=mrs_object.get("schema_request_path"),
                session=self.session)

            if schema is None:
                raise Exception("The REST schema was not found.")

            lib.schemas.update_schema(
                session=self.session,
                schemas={schema["id"]: ""},
                value={
                    "service_id": mrs_object.get("new_service_id", schema["service_id"]),
                    "request_path": mrs_object.get("new_request_path", schema["request_path"]),
                    "requires_auth": mrs_object.get("requires_auth", schema["requires_auth"]),
                    "enabled": mrs_object.get("enabled", schema["enabled"]),
                    "items_per_page": mrs_object.get("items_per_page", schema["items_per_page"]),
                    "comments": mrs_object.get("comments", schema["comments"]),
                    "options": mrs_object.get("options", schema["options"]),
                })

            self.results.append({
                "statementIndex": len(self.results) + 1,
                "type": "success",
                "message": f"OK, 1 record updated.",
                "operation": self.current_operation,
                "id": lib.core.convert_id_to_string(service_id)
            })
        except Exception as e:
            self.results.append({
                "statementIndex": len(self.results) + 1,
                "type": "error",
                "message": f"Failed to update the REST Schema `{full_path}`. {e}",
                "operation": self.current_operation
            })
            raise

    def alterRestDbObject(self, mrs_object: dict):
        self.current_operation = mrs_object.pop("current_operation")
        request_path = mrs_object.pop("request_path")
        rest_object_type = mrs_object.pop("type")

        db_object_id = mrs_object.pop("id")
        mrs_object.pop("parent_reference_stack", None)

        full_path = (
            mrs_object.pop("url_host_name", self.current_service_host) +
            mrs_object.pop("url_context_root", self.current_service) +
            mrs_object.pop("schema_request_path", self.current_schema) +
            request_path)

        try:
            db_object = lib.db_objects.get_db_object(
                session=self.session, db_object_id=db_object_id)
            if db_object is None:
                raise Exception(
                    f'The given REST {rest_object_type} `{full_path}` could not be found.')

            new_request_path = mrs_object.pop("new_request_path")
            if new_request_path is not None:
                mrs_object["request_path"] = new_request_path

            new_object_name = mrs_object.pop("new_object_name")
            if new_object_name is not None:
                # TODO: Implement object handling
                pass

            mrs_object.pop("graph_gl_object_count", None)
            objects = mrs_object.pop("objects", None)

            # Alter DB Object
            if mrs_object:
                lib.db_objects.update_db_objects(
                    session=self.session,
                    db_object_ids={db_object["id"]: ""},
                    value=mrs_object)

            if objects:
                lib.db_objects.set_objects(session=self.session,
                                           db_object_id=db_object["id"], objects=objects)

            self.results.append({
                "statementIndex": len(self.results) + 1,
                "type": "success",
                "message": "OK, 1 record updated.",
                "operation": self.current_operation,
                "id": lib.core.convert_id_to_string(db_object["id"])
            })
        except Exception as e:
            self.results.append({
                "statementIndex": len(self.results) + 1,
                "type": "error",
                "message": f'Failed to get the REST {rest_object_type} `{full_path}`. {e}',
                "operation": self.current_operation
            })
            raise

    def dropRestService(self, mrs_object: dict):
        self.current_operation = mrs_object.pop("current_operation")

        full_path = (
            mrs_object.get("url_host_name", "") +
            mrs_object.get("url_context_root", ""))

        with lib.core.MrsDbTransaction(self.session):
            try:
                service = lib.services.get_service(
                    url_context_root=mrs_object.get("url_context_root"),
                    url_host_name=mrs_object.get("url_host_name", ""),
                    session=self.session)
                if service is None:
                    raise Exception(
                        f'The given REST Service `{full_path}` could not be found.')

                lib.services.delete_service(
                    service_id=service["id"],
                    session=self.session)

                self.results.append({
                    "statementIndex": len(self.results) + 1,
                    "type": "success",
                    "message": f'REST Service `{full_path}` dropped successfully.',
                    "operation": self.current_operation,
                    "id": lib.core.convert_id_to_string(service["id"])
                })
            except Exception as e:
                self.results.append({
                    "statementIndex": len(self.results) + 1,
                    "type": "error",
                    "message": f'Failed to drop the REST Service `{full_path}`. {e}',
                    "operation": self.current_operation
                })
                raise

    def dropRestSchema(self, mrs_object: dict):
        self.current_operation = mrs_object.pop("current_operation")

        full_path = (
            mrs_object.get("url_host_name", self.current_service_host) +
            mrs_object.get("url_context_root", self.current_service) +
            mrs_object.get("request_path", ""))

        with lib.core.MrsDbTransaction(self.session):
            try:

                service_id = self.get_given_or_current_service_id(mrs_object)
                if service_id is None:
                    raise Exception("No REST Service specified.")

                schema = lib.schemas.get_schema(
                    service_id=service_id, request_path=mrs_object["request_path"],
                    session=self.session)
                if schema is None:
                    raise Exception(
                        f'The given REST Schema `{full_path}` could not be found.')

                lib.schemas.delete_schema(
                    schema_id=schema["id"], session=self.session)

                self.results.append({
                    "statementIndex": len(self.results) + 1,
                    "type": "success",
                    "message": f'REST Schema `{full_path}` dropped successfully.',
                    "operation": self.current_operation,
                    "id": lib.core.convert_id_to_string(schema["id"])
                })
            except Exception as e:
                self.results.append({
                    "statementIndex": len(self.results) + 1,
                    "type": "error",
                    "message": f'Failed to drop the REST Schema `{full_path}`. {e}',
                    "operation": self.current_operation
                })
                raise

    def dropRestDbObject(self, mrs_object: dict):
        self.current_operation = mrs_object.pop("current_operation")
        request_path = mrs_object.pop("request_path")
        rest_object_type = mrs_object.pop("type")

        full_path = (
            mrs_object.get("url_host_name", self.current_service_host) +
            mrs_object.get("url_context_root", self.current_service) +
            mrs_object.get("schema_request_path", self.current_schema) +
            request_path)

        with lib.core.MrsDbTransaction(self.session):
            try:
                schema_id = self.get_given_or_current_schema_id(mrs_object)
                if schema_id is None:
                    raise Exception("No REST Schema specified.")

                db_object = lib.db_objects.get_db_object(
                    session=self.session, schema_id=schema_id,
                    request_path=request_path)
                if db_object is None:
                    raise Exception(
                        f'The given REST {rest_object_type} `{full_path}` could not be found.')

                lib.db_objects.delete_db_object(
                    session=self.session, db_object_id=db_object.get("id"))

                self.results.append({
                    "statementIndex": len(self.results) + 1,
                    "type": "success",
                    "message": f'REST {rest_object_type} `{full_path}` dropped successfully.',
                    "operation": self.current_operation,
                    "id": lib.core.convert_id_to_string(db_object["id"])
                })
            except Exception as e:
                self.results.append({
                    "statementIndex": len(self.results) + 1,
                    "type": "error",
                    "message": f'Failed to drop the REST {rest_object_type} `{full_path}`. {e}',
                    "operation": self.current_operation
                })
                raise

    def use(self, mrs_object: dict):
        self.current_operation = mrs_object.pop("current_operation")

        try:
            url_context_root = mrs_object.get("url_context_root")
            if url_context_root is not None:
                service = lib.services.get_service(
                    url_context_root=url_context_root,
                    url_host_name=mrs_object.get("url_host_name", ""),
                    session=self.session)
                if service is not None:
                    self.current_service_id = service.get("id")
                    self.current_service = service.get("url_context_root")
                    self.current_service_host = mrs_object.get(
                        "url_host_name", "")
                else:
                    raise Exception(
                        f"A REST Service with the request path {url_context_root} could not be found.")

            if mrs_object.get("schema_request_path") is not None:
                if self.current_service_id is None:
                    raise Exception(
                        f"No current REST Service specified.")

                request_path = mrs_object.get("schema_request_path")
                schema = lib.schemas.get_schema(
                    service_id=self.current_service_id,
                    request_path=request_path,
                    session=self.session)
                if schema is not None:
                    self.current_schema_id = schema.get("id")
                    self.current_schema = schema.get("request_path")
                else:
                    raise Exception(
                        f"A REST Schema with the request path {request_path} could not be found.")

                self.results.append({
                    "statementIndex": len(self.results) + 1,
                    "type": "success",
                    "message": (f'Now using REST Schema `{self.current_schema}` '
                                f'on REST Service `{self.current_service_host}{self.current_service}`.'),
                    "operation": self.current_operation,
                    "id": lib.core.convert_id_to_string(self.current_schema_id)
                })
            else:
                self.results.append({
                    "statementIndex": len(self.results) + 1,
                    "type": "success",
                    "message": f'Now using REST Service `{self.current_service_host}{self.current_service}`.',
                    "operation": self.current_operation,
                    "id": lib.core.convert_id_to_string(self.current_service_id)
                })

        except Exception as e:
            self.results.append({
                "statementIndex": len(self.results) + 1,
                "type": "error",
                "message": f'Cannot USE the specified REST object. {e}',
                "operation": self.current_operation
            })
            raise

    def showRestMetadataStatus(self, mrs_object: dict):
        self.current_operation = mrs_object.pop("current_operation")

        try:
            result = [lib.general.get_status(session=self.session)]

            self.results.append({
                "statementIndex": len(self.results) + 1,
                "type": "success",
                "message": f'OK, 1 record received.',
                "operation": self.current_operation,
                "result": result
            })
        except Exception as e:
            self.results.append({
                "statementIndex": len(self.results) + 1,
                "type": "error",
                "message": f'Cannot SHOW the REST services. {e}',
                "operation": self.current_operation
            })
            raise

    def showRestServices(self, mrs_object: dict):
        self.current_operation = mrs_object.pop("current_operation")

        try:
            services = lib.services.get_services(session=self.session)
            result = []
            for service in services:
                result.append({
                    "REST Service Path": service.get("host_ctx"),
                    "enabled": service.get("enabled") == 1
                })

            self.results.append({
                "statementIndex": len(self.results) + 1,
                "type": "success",
                "message": f'OK, {len(services)} record{"s" if len(services) > 1 else ""} received.',
                "operation": self.current_operation,
                "result": result
            })
        except Exception as e:
            self.results.append({
                "statementIndex": len(self.results) + 1,
                "type": "error",
                "message": f'Cannot SHOW the REST services. {e}',
                "operation": self.current_operation
            })
            raise

    def showRestSchemas(self, mrs_object: dict):
        self.current_operation = mrs_object.pop("current_operation")

        try:
            service_id = self.get_given_or_current_service_id(mrs_object)
            if service_id is None:
                raise Exception("No REST Service specified.")

            schemas = lib.schemas.get_schemas(
                session=self.session, service_id=service_id)
            result = []
            for schema in schemas:
                result.append({
                    "REST schema path": schema.get("request_path"),
                    "enabled": schema.get("enabled") == 1
                })

            self.results.append({
                "statementIndex": len(self.results) + 1,
                "type": "success",
                "message": f'OK, {len(schemas)} record{"s" if len(schemas) > 1 else ""} received.',
                "operation": self.current_operation,
                "result": result
            })
        except Exception as e:
            self.results.append({
                "statementIndex": len(self.results) + 1,
                "type": "error",
                "message": f'Cannot SHOW the REST schemas. {e}',
                "operation": self.current_operation
            })
            raise

    def showRestDbObjects(self, mrs_object: dict):
        self.current_operation = mrs_object.pop("current_operation")
        object_types = mrs_object.pop("object_types")

        try:
            schema_id = self.get_given_or_current_schema_id(mrs_object)
            if schema_id is None:
                raise Exception("No REST Schema specified.")

            items = lib.db_objects.get_db_objects(
                session=self.session, schema_id=schema_id,
                object_types=object_types)
            result = []
            for item in items:
                result.append({
                    "REST DB Object": item.get("request_path"),
                    "enabled": item.get("enabled") == 1
                })

            self.results.append({
                "statementIndex": len(self.results) + 1,
                "type": "success",
                "message": f'OK, {len(items)} record{"s" if len(items) > 1 else ""} received.',
                "operation": self.current_operation,
                "result": result
            })
        except Exception as e:
            self.results.append({
                "statementIndex": len(self.results) + 1,
                "type": "error",
                "message": f'Cannot SHOW the REST db objects. {e}',
                "operation": self.current_operation
            })
            raise

    def showCreateRestService(self, mrs_object: dict):
        self.current_operation = mrs_object.pop("current_operation")
        url_host_name = mrs_object.get(
            "url_host_name", self.current_service_host)
        full_path = f'{url_host_name}{mrs_object.get("url_context_root", self.current_service)}'

        try:
            service_id = self.get_given_or_current_service_id(mrs_object)
            if service_id is None:
                raise Exception("No REST Service specified.")

            service = lib.services.get_service(
                session=self.session, service_id=service_id)

            stmt = f'CREATE REST SERVICE {service.get("host_ctx")}\n'
            if service.get("enabled") != 1:
                stmt += "    DISABLED\n"
            if service.get("comments") is not None:
                stmt += f'    COMMENTS "{service.get("comments")}"\n'

            auth = ""
            if service.get("auth_path") != "/authentication":
                auth += f'        PATH "{service.get("auth_path")}"\n'
            if service.get("auth_completed_url") is not None:
                auth += f'        REDIRECTION "{service.get("auth_completed_url")}"\n'
            if service.get("auth_completed_url_validation") is not None:
                auth += f'        VALIDATION "{service.get("auth_completed_url_validation")}"\n'
            if service.get("auth_completed_page_content") is not None:
                auth += f'        PAGE CONTENT "{service.get("auth_completed_page_content")}"\n'
            if auth != "":
                stmt += f'    AUTHENTICATION\n{auth}'

            options = service.get("options")
            if options is not None and options != "":
                js = json.dumps(options, indent=4)
                # Indent the json.dumps with 4 spaces
                js_indented = ""
                for ln in js.split("\n"):
                    js_indented += f'    {ln}\n'
                stmt += f'    OPTIONS {js_indented[4:-1]}\n'

            result = [{
                "CREATE REST SERVICE": stmt[:-1] + ";"
            }]

            self.results.append({
                "statementIndex": len(self.results) + 1,
                "type": "success",
                "message": "OK, 1 record received.",
                "operation": self.current_operation,
                "id": lib.core.convert_id_to_string(service_id),
                "result": result
            })
        except Exception as e:
            self.results.append({
                "statementIndex": len(self.results) + 1,
                "type": "error",
                "message": f"Failed to get the REST Service `{full_path}`. {e}",
                "operation": self.current_operation
            })
            raise

    def showCreateRestSchema(self, mrs_object: dict):
        self.current_operation = mrs_object.pop("current_operation")
        url_host_name = mrs_object.get(
            "url_host_name", self.current_service_host)
        full_path = f'{url_host_name}{mrs_object.get("url_context_root", self.current_service)}'
        try:
            service_id = self.get_given_or_current_service_id(mrs_object)
            if service_id is None:
                raise Exception("No REST Service specified.")

            service = lib.services.get_service(
                session=self.session, service_id=service_id)

            schema = lib.schemas.get_schema(
                service_id=service_id,
                request_path=mrs_object.get("schema_request_path"),
                session=self.session)

            if schema is None:
                raise Exception("The REST schema was not found.")

            stmt = f'CREATE OR REPLACE REST SCHEMA {schema.get("request_path")} FROM \'{schema.get("name")}\'\n'
            stmt += f'    ON SERVICE {service.get("host_ctx")}\n'

            if schema.get("enabled") != 1:
                stmt += "    DISABLED\n"

            options = schema.get("options")
            if options is not None and options != "":
                js = json.dumps(options, indent=4)
                # Indent the json.dumps with 4 spaces
                js_indented = ""
                for ln in js.split("\n"):
                    js_indented += f'    {ln}\n'
                stmt += f'    OPTIONS {js_indented[4:-1]}\n'

            result = [{
                "CREATE REST SCHEMA ": stmt[:-1] + ";"
            }]

            self.results.append({
                "statementIndex": len(self.results) + 1,
                "type": "success",
                "message": "OK, 1 record received.",
                "operation": self.current_operation,
                "id": lib.core.convert_id_to_string(schema.get("id")),
                "result": result
            })
        except Exception as e:
            self.results.append({
                "statementIndex": len(self.results) + 1,
                "type": "error",
                "message": f"Failed to get the REST Service `{full_path}`. {e}",
                "operation": self.current_operation
            })
            raise

    def showCreateRestDbObject(self, mrs_object: dict):
        # Keep in sync with the function buildDualityViewSql implemented in
        # ../../frontend/src/modules/mrs/dialogs/MrsObjectFieldEditor.tsx

        self.current_operation = mrs_object.pop("current_operation")
        request_path = mrs_object.pop("request_path")
        rest_object_type = mrs_object.pop("type")

        full_path = (
            mrs_object.get("url_host_name", self.current_service_host) +
            mrs_object.get("url_context_root", self.current_service) +
            mrs_object.get("schema_request_path", self.current_schema) +
            request_path)

        try:
            schema_id = self.get_given_or_current_schema_id(mrs_object)
            if schema_id is None:
                raise Exception("No REST Schema specified.")

            db_object = lib.db_objects.get_db_object(
                session=self.session, schema_id=schema_id,
                request_path=request_path)
            if db_object is None:
                raise Exception(
                    f'The given REST {rest_object_type} `{full_path}` could not be found.')

            objects = lib.db_objects.get_objects(
                session=self.session,
                db_object_id=db_object.get("id")
            )

            if rest_object_type == "PROCEDURE" and db_object.get("object_type") != "PROCEDURE":
                raise Exception(
                    f'The given REST object `{full_path}` is not a REST PROCEDURE.')
            if (rest_object_type == "DUALITY VIEW" and
                    db_object.get("object_type") != "TABLE" and db_object.get("object_type") != "VIEW"):
                raise Exception(
                    f'The given REST object `{full_path}` is not a REST DUALITY VIEW.')

            options = []

            stmt = (f'CREATE OR REPLACE REST {rest_object_type} {db_object.get("request_path")}\n' +
                    f'    ON SERVICE {mrs_object.get("url_context_root")} SCHEMA {db_object.get("schema_request_path")}\n')

            if not db_object["enabled"]:
                stmt += "    DISABLED\n"

            if db_object["requires_auth"]:
                stmt += "    AUTHENTICATION REQUIRED\n"

            if db_object["items_per_page"] is not None and db_object["items_per_page"] != 25: # 25 is the default value
                stmt += f'    ITEMS PER PAGE {db_object["items_per_page"]}\n'

            if db_object["comments"]:
                stmt += f'    COMMENTS "{db_object["comments"]}"\n'

            if db_object["media_type"] is not None:
                stmt += f'    MEDIA TYPE {db_object["media_type"]}\n'

            if db_object["crud_operation_format"] != "FEED":
                stmt += f'    FORMAT {db_object["crud_operation_format"]}\n'

            if db_object["auth_stored_procedure"] is not None:
                stmt += f'    AUTHENTICATION PROCEDURE {db_object["auth_stored_procedure"]}\n'

            options = db_object.get("options")
            if options is not None and options != "":
                js = json.dumps(options, indent=4)
                # Indent the json.dumps with 4 spaces
                js_indented = ""
                for ln in js.split("\n"):
                    js_indented += f'    {ln}\n'
                stmt += f'    OPTIONS {js_indented[4:-1]}\n'

            stmt += f'    FROM {db_object.get("qualified_name")} AS {objects[0]["name"]}'

            if rest_object_type != "PROCEDURE":
                crud_ops = db_object.get("crud_operations")
                if "CREATE" in crud_ops:
                    stmt += " @INSERT"
                if "UPDATE" in crud_ops:
                    stmt += " @UPDATE"
                if "DELETE" in crud_ops:
                    stmt += " @DELETE"

                fields = []
                if len(objects) > 0:
                    fields = lib.db_objects.get_object_fields_with_references(
                        session=self.session, object_id=objects[0]["id"])

                stmt += f' {{\n{cutLastComma(walk(fields=fields, level=2, current_object=db_object))}\n    }}'
            else:
                for object in objects:
                    fields = lib.db_objects.get_object_fields_with_references(
                        session=self.session, object_id=object["id"])

                    children = cutLastComma(walk(
                        fields=fields, add_data_type=object["kind"] == "RESULT", current_object=db_object))

                    stmt += f'\n{object["kind"]}'

                    if object["kind"] == "RESULT":
                        stmt += f' {object["name"]}'

                    if children:
                        stmt += f" {{\n{children}\n}}"

            stmt += ";"

            # Build CREATE statement
            result = [{
                f"CREATE REST {rest_object_type}": stmt[:-1] + ";"
            }]

            self.results.append({
                "statementIndex": len(self.results) + 1,
                "type": "success",
                "message": "OK, 1 record received.",
                "operation": self.current_operation,
                "id": lib.core.convert_id_to_string(db_object["id"]),
                "result": result
            })
        except Exception as e:
            self.results.append({
                "statementIndex": len(self.results) + 1,
                "type": "error",
                "message": f'Failed to get the REST {rest_object_type} `{full_path}`. {e}',
                "operation": self.current_operation
            })
            raise
