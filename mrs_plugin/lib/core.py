# Copyright (c) 2021, 2022, Oracle and/or its affiliates.
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

"""Sub-Module for core functions"""

# cSpell:ignore mysqlsh, mrs
import traceback
from mrs_plugin.lib import services, content_sets, general, schemas
import mysqlsh
import os
import re
import json
from enum import IntEnum
import threading
import base64

_metadata_schema_updated = False

class ConfigFile:
    def __init__(self) -> None:
        self._settings = {}

        self._filename = os.path.abspath(mysqlsh.plugin_manager.general.get_shell_user_dir(
        'plugin_data', 'mrs_plugin', "config.json"))
        try:
            with open(self._filename, "r") as f:
                self._settings = json.load(f)
                convert_ids_to_binary(["current_service_id"], self._settings)
        except:
            pass

    def store(self):
        # create a copy because we're changing the dict data
        settings_copy = self._settings.copy()

        if "current_service_id" in settings_copy:
            settings_copy["current_service_id"] = f"0x{settings_copy['current_service_id'].hex()}"

        os.makedirs(os.path.dirname(self._filename), exist_ok=True)
        with open(self._filename, "w") as f:
            json.dump(settings_copy, f)

    @property
    def settings(self):
        return self._settings


class Validations:
    @staticmethod
    def request_path(value, required=False, session=None):
        if required and value is None:
            raise Exception("The request_path is missing.")
        if value is None:
            return

        if not isinstance(value, str) or not value.startswith('/'):
            raise Exception("The request_path has to start with '/'.")
        if session:
            check_request_path(session, value)


class LogLevel(IntEnum):
    NONE = 1
    INTERNAL_ERROR = 2
    ERROR = 3
    WARNING = 4
    INFO = 5
    DEBUG = 6
    DEBUG2 = 7
    DEBUG3 = 8

def get_local_config():
    return ConfigFile().settings

def script_path(*suffixes):
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), *suffixes)

def print_exception(exc_type, exc_value, exc_traceback):
    # Exception handler for the MrsDbSession context manager, which should
    # be used only in interactive mode.
    # Returns True to signal the exception was dealt with
    exc_str = "".join([s.replace("\\n", "\n") for s in traceback.format_exception(exc_type, exc_value, exc_traceback)])
    print(exc_str)
    return True


def validate_service_path(session, path):
    """Ensures the given path is valid in any of the registered services.

    Args:
        session (object): The database session to use.
        path (str): The path to validate.

    Returns:
        service, schema, content_set as dict.
    """
    if not path:
        return None, None, None

    service = None
    schema = None
    content_set = None

    # Match path against services and schemas
    all_services = services.get_services(session)
    for item in all_services:
        host_ctx = item.get("host_ctx")
        if host_ctx == path[:len(host_ctx)]:
            service = item
            if len(path) > len(host_ctx):
                sub_path = path[len(host_ctx):]

                db_schemas = schemas.get_schemas(
                    service_id=service.get("id"), session=session)

                if db_schemas:
                    for item in db_schemas:
                        request_path = item.get("request_path")
                        if request_path == sub_path[:len(request_path)]:
                            schema = item
                        break

                if not schema:
                    content_sets_local = content_sets.get_content_sets(
                        service_id=service.get("id"), session=session)

                    if content_sets_local:
                        for item in content_sets_local:
                            request_path = item.get("request_path")
                            if request_path == sub_path[:len(request_path)]:
                                content_set = item
                            break

                if not schema and not content_set:
                    raise ValueError(
                        f"The given schema or content set was not found.")
            break

    if not service:
        raise ValueError(f"The given MRS service was not found.")

    return service, schema, content_set


def set_current_objects(service_id: bytes=None, service=None, schema_id: bytes=None,
                        schema=None, content_set_id: bytes=None, content_set=None,
                        db_object_id: bytes=None, db_object=None):
    """Sets the current objects to the given ones

    Note that if no service or no schema or no db_object are specified,
    they are reset

    Args:
        service_id: The id of the service to set as the current service
        service (dict): The service to set as the current service
        schema_id: The id of the schema to set as the current schema
        schema (dict): The schema to set as the current schema
        content_set_id: The id of the content_set to set as the current
        content_set (dict): The content_set to set as the current
        db_object_id: The id of the db_object to set as the current
            db_object
        db_object (dict): The db_object to set as the current db_object

    Returns:
        The current or default service or None if no default is set
    """

    # Get current_service_id from the global mrs_config
    mrs_config = get_current_config()

    if service_id:
        mrs_config['current_service_id'] = service_id
    if service:
        mrs_config['current_service_id'] = service.get("id")
    # If current_service_id is current set but not passed in, clear it
    if mrs_config.get('current_service_id') and not (service_id or service):
        mrs_config['current_service_id'] = None

    if schema_id:
        mrs_config['current_schema_id'] = schema_id
    if schema:
        mrs_config['current_schema_id'] = schema.get("id")
    # If current_schema_id is current set but not passed in, clear it
    if mrs_config.get('current_schema_id') and not (schema_id or schema):
        mrs_config['current_schema_id'] = None

    if db_object_id:
        mrs_config['current_db_object_id'] = db_object_id
    if db_object:
        mrs_config['current_db_object_id'] = db_object.get("id")
    # If current_db_object_id is current set but not passed in, clear it
    if mrs_config.get('current_db_object_id') and not (db_object_id or
                                                       db_object):
        mrs_config['current_db_object_id'] = None

    if content_set_id:
        mrs_config['current_content_set_id'] = content_set_id
    if content_set:
        mrs_config['current_content_set_id'] = content_set.get("id")
    # If current_db_object_id is current set but not passed in, clear it
    if mrs_config.get('current_content_set_id') and not (content_set_id or
                                                         content_set):
        mrs_config['current_content_set_id'] = None


def get_interactive_default():
    """Returns the default of the interactive mode

    Returns:
        The current database session
    """
    if mysqlsh.globals.shell.options.useWizards:
        ct = threading.current_thread()
        if ct.__class__.__name__ == '_MainThread':
            return True
    return False


def get_interactive_result():
    """
    To be used in plugin functions that may return pretty formatted result when
    called in an interactive Shell session
    """
    return get_interactive_default()


def get_current_session(session=None):
    """Returns the current database session

    If a session is provided, it will be returned instead of the current one.
    If there is no active session, then an exception will be raised.

    Returns:
        The current database session
    """
    if session is not None:
        return session

    # Check if the user provided a session or there is an active global session
    session = mysqlsh.globals.shell.get_session()
    if session is None:
        raise Exception(
            "MySQL session not specified. Please either pass a session "
            "object when calling the function or open a database "
            "connection in the MySQL Shell first.")

    return session

def get_metadata_schema_updated():
    return _metadata_schema_updated

def _ensure_mrs_metadata_schema(session):
    """Creates or updates the MRS metadata schema

    Raises exception on failure

    Args:
        session (object): The database session to use

    Returns:
        True if the metadata schema has been changed
    """
    _metadata_schema_updated = False

    # Check if the MRS metadata schema already exists
    row = select(table="INFORMATION_SCHEMA.SCHEMATA", cols="COUNT(*) AS schema_exists",
        where="SCHEMA_NAME = 'mysql_rest_service_metadata'"
    ).exec(session).first

    if row["schema_exists"] == 0:
        create_rds_metadata_schema(session)
        _metadata_schema_updated = True
        return True

    # If it exists, check the version number
    row = select(table="schema_version", cols=["major", "minor", "patch", "CONCAT(major, '.', minor, '.', patch) AS version"]
    ).exec(session).first

    if not row:
        raise Exception(
            "Unable to fetch MRS metadata database schema version.")

    db_version_str = row["version"]
    if db_version_str != general.DB_VERSION_STR:
        db_version_num = (100000 * row["major"] +
                            1000 * row["minor"] +
                            row["patch"])

        if db_version_num > general.DB_VERSION_NUM:
            raise Exception(
                "Unsupported MRS metadata database schema "
                f"version {db_version_str}. "
                "Please update your MRS Shell Plugin.")
        else:
            update_rds_metadata_schema(session, db_version_str)
            return True

    return False

def update_rds_metadata_schema(session, current_db_version_str):
    """Creates or updates the MRS metadata schema

    Raises exception on failure

    Args:
        session (object): The database session to use
        current_db_version_str (string): Current version of the metadata schema
        interactive (bool): Indicates whether to execute in interactive mode

    Returns:
        None
    """
    interactive = get_interactive_default()
    if interactive:
        print("Updating MRS metadata schema...")

    script_dir_path = script_path('db_schema')

    version_to_update = current_db_version_str

    # run updates until ending up at current version
    upgrade_file_found = True

    while general.DB_VERSION_STR != version_to_update and upgrade_file_found:
        # set upgrade_file_found to False to ensure execution will not be
        # stuck in this loop forever
        upgrade_file_found = False

        for f in os.listdir(script_dir_path):
            m = re.match(
                r'mrs_metadata_schema_(\d+\.\d+\.\d+)_to_'
                r'(\d+\.\d+\.\d+)\.sql', f)
            if m:
                g = m.groups()

                update_from_version = g[0]
                update_to_version = g[1]

                if version_to_update == update_from_version:
                    upgrade_file_found = True

                    try:
                        with open(os.path.join(script_dir_path, f),
                                  'r') as sql_file:
                            sql_script = sql_file.read()

                        if interactive:
                            print(f"Update from version {update_from_version} "
                                  f"to version {update_to_version} ...")

                        for cmd in mysqlsh.mysql.split_script(sql_script):
                            current_cmd = cmd.strip()
                            if current_cmd:
                                MrsDbExec(current_cmd).exec(session)
                                # session.run_sql(current_cmd)

                        version_to_update = update_to_version
                    except (mysqlsh.DBError, Exception) as e:
                        raise Exception(
                            "The MRS metadata database schema could not "
                            f"be updated.\n{current_cmd}\n{e}")

        if general.DB_VERSION_STR != version_to_update and not upgrade_file_found:
            raise Exception("The file to update the metadata "
                            f"schema from version {version_to_update} to "
                            f"version {general.DB_VERSION_STR} was not found.")
        else:
            if interactive:
                print(f"The MRS metadata schema was successfully update "
                      f"to version {general.DB_VERSION_STR}.")


def create_rds_metadata_schema(session):
    """Creates or updates the MRS metadata schema
#
    Raises exception on failure

    Args:
        session (object): The database session to use
        interactive (bool): Indicates whether to execute in interactive mode

    Returns:
        None
    """
    interactive = get_interactive_default()
    if interactive:
        print("Creating MRS metadata schema...")

    latest_version_val = [0, 0, 0]

    script_dir = sql_file_path = script_path('db_schema')

    # find the latest version of the database file available
    for f in os.listdir(script_dir):
        m = re.match(
            r'mrs_metadata_schema_(\d+)\.(\d+)\.(\d+)\.sql', f)
        if m:
            g = [int(group) for group in m.groups()]
            if g > latest_version_val or latest_version_val == [0, 0, 0]:
                latest_version_val = g

    if latest_version_val == [0, 0, 0]:
        return

    if latest_version_val > general.DB_VERSION:
        latest_version_val = general.DB_VERSION

    sql_file_path = script_path('db_schema', f'mrs_metadata_schema_{".".join(map(str, latest_version_val))}.sql')

    with open(sql_file_path) as f:
        sql_script = f.read()

    cmds = mysqlsh.mysql.split_script(sql_script)

    # Execute all commands
    current_cmd = ""
    try:
        for cmd in cmds:
            current_cmd = cmd.strip()
            if current_cmd:
                session.run_sql(current_cmd)
    except mysqlsh.DBError as e:
        # On exception, drop the schema and re-raise
        session.run_sql("DROP SCHEMA IF EXISTS `mysql_rest_service_metadata`")
        raise Exception(f"Failed to create the MRS metadata schema.\n"
                        f"{current_cmd}\n{e}")


def prompt_for_list_item(item_list, prompt_caption, prompt_default_value='',
                         item_name_property=None, given_value=None,
                         print_list=False, allow_multi_select=False):
    """Lets the use choose and item from a list

    When prompted, the user can either provide the index of the item or the
    name of the item.

    If given_value is provided, it will be checked against the items in the list
    instead of prompting the user for a new value

    Args:
        item_list (list): The list of items to choose from
        prompt_caption (str): The caption of the prompt that will be displayed
        prompt_default_value (str): The default_value for the prompt
        item_name_property (str): The name of the property that is used to
            compare with the user input
        given_value (str): Value that the user provided beforehand.
        print_list (bool): Specifies whether the list of items should be printed
        allow_multi_select (bool): Whether multiple items can be entered,
            separated by ',' and the string '*' is allowed

    Returns:
        The selected item or the selected item list when allow_multi_select is
        True or None when the user cancelled the selection
    """

    # If a given_value was provided, check this first instead of prompting the
    # user
    if given_value:
        given_value = given_value.lower()
        selected_item = None
        for item in item_list:
            if item_name_property is not None:
                if isinstance(item, dict):
                    item_name = item.get(item_name_property)
                else:
                    item_name = getattr(item, item_name_property)
            else:
                item_name = item

            if item_name.lower() == given_value:
                selected_item = item
                break

        return selected_item

    if print_list:
        i = 1
        for item in item_list:
            if item_name_property:
                if isinstance(item, dict):
                    item_caption = item.get(item_name_property)
                else:
                    item_caption = getattr(item, item_name_property)
            else:
                item_caption = item
            print(f"{i:>4} {item_caption}")
            i += 1
        print()

    selected_items = []

    # Let the user choose from the list
    while len(selected_items) == 0:
        # Prompt the user for specifying an item
        prompt = mysqlsh.globals.shell.prompt(
            prompt_caption, {'defaultValue': prompt_default_value}
        ).strip().lower()

        if prompt == '':
            return None
        # If the user typed '*', return full list
        if allow_multi_select and prompt == "*":
            return item_list

        if allow_multi_select:
            prompt_items = prompt.split(',')
        else:
            prompt_items = [prompt]

        try:
            for prompt in prompt_items:
                try:
                    # If the user provided an index, try to map that to an item
                    nr = int(prompt)
                    if nr > 0 and nr <= len(item_list):
                        selected_items.append(item_list[nr - 1])
                    else:
                        raise IndexError
                except ValueError:
                    # Search by name
                    selected_item = None
                    for item in item_list:
                        if item_name_property is not None:
                            if isinstance(item, dict):
                                item_name = item.get(item_name_property)
                            else:
                                item_name = getattr(item, item_name_property)
                        else:
                            item_name = item

                        if item_name.lower() == prompt:
                            selected_item = item
                            break

                    if selected_item is None:
                        raise ValueError
                    else:
                        selected_items.append(selected_item)

        except (ValueError, IndexError):
            msg = f'The item {prompt} was not found. Please try again'
            if prompt_default_value == "":
                msg += " or leave empty to cancel the operation.\n"
            else:
                msg += ".\n"
            print(msg)

    if allow_multi_select:
        return selected_items if len(selected_items) > 0 else None
    elif len(selected_items) > 0:
        return selected_items[0]


def prompt_for_comments():
    """Prompts the user for comments

    Returns:
        The comments as str
    """

    return prompt("Comments: ").strip()

def get_sql_result_as_dict_list(res, fetch_all=True):
    """Returns the result set as a list of dicts

    Args:
        res: (object): The sql result set

    Returns:
        A list of dicts
    """
    if not res:
        return []


    cols = res.get_columns()
    rows = res.fetch_all()
    dict_list = []

    for row in rows:
        item = {}
        for col in cols:
            col_name = col.get_column_label()
            field_val = row.get_field(col_name)
            col_type = str(col.get_type())
            if col_type == "<Type.SET>":
                item[col_name] = field_val.split(",") if field_val else []
            elif col_type == "<Type.JSON>":
                item[col_name] = json.loads(field_val) if field_val else None
            else:
                item[col_name] = field_val

        dict_list.append(item)

    return dict_list


def get_current_config(mrs_config=None):
    """Gets the active config dict

    If no config dict is given as parameter, the global config dict will be used

    Args:
        config (dict): The config to be used or None

    Returns:
        The active config dict
    """
    if mrs_config is None:
        # Check if global object 'mrs_config' has already been registered
        if 'mrs_config' in dir(mysqlsh.globals):
            mrs_config = getattr(mysqlsh.globals, 'mrs_config')
        else:
            mrs_config = {}
            setattr(mysqlsh.globals, 'mrs_config', mrs_config)

    return mrs_config


def prompt(message, options=None):
    """Prompts the user for input

    Args:
        message (str): A string with the message to be shown to the user.
        config (dict): Dictionary with options that change the function
            behavior. The options dictionary may contain the following options:
            - defaultValue: a str value to be returned if the provides no data.
            - type: a str value to define the prompt type.
                The type option supports the following values:
                - password: the user input will not be echoed on the screen.

    Returns:
        A string value containing the input from the user.
    """
    return mysqlsh.globals.shell.prompt(message, options)


def check_request_path(session, request_path):
    """Checks if the given request_path is valid and unique

    Args:
        request_path (str): The request_path to check
        **kwargs: Additional options

    Keyword Args:
        session (object): The database session to use

    Returns:
        None
    """
    if not request_path:
        raise Exception("No request_path specified.")

    if not request_path.startswith("/"):
        raise ValueError(
                f"The request_path '{request_path}' has to start with '/'.")

    # Check if the request_path already exists for another db_object of that
    # schema
    res = session.run_sql("""
        SELECT CONCAT(h.name,
            se.url_context_root) as full_request_path
        FROM `mysql_rest_service_metadata`.service se
            LEFT JOIN `mysql_rest_service_metadata`.url_host h
                ON se.url_host_id = h.id
        WHERE CONCAT(h.name, se.url_context_root) = ?
        UNION
        SELECT CONCAT(h.name, se.url_context_root,
            sc.request_path) as full_request_path
        FROM `mysql_rest_service_metadata`.db_schema sc
            LEFT OUTER JOIN `mysql_rest_service_metadata`.service se
                ON se.id = sc.service_id
            LEFT JOIN `mysql_rest_service_metadata`.url_host h
                ON se.url_host_id = h.id
        WHERE CONCAT(h.name, se.url_context_root,
                sc.request_path) = ?
        UNION
        SELECT CONCAT(h.name, se.url_context_root,
            sc.request_path, o.request_path) as full_request_path
        FROM `mysql_rest_service_metadata`.db_object o
            LEFT OUTER JOIN `mysql_rest_service_metadata`.db_schema sc
                ON sc.id = o.db_schema_id
            LEFT OUTER JOIN `mysql_rest_service_metadata`.service se
                ON se.id = sc.service_id
            LEFT JOIN `mysql_rest_service_metadata`.url_host h
                ON se.url_host_id = h.id
        WHERE CONCAT(h.name, se.url_context_root,
                sc.request_path, o.request_path) = ?
        UNION
        SELECT CONCAT(h.name, se.url_context_root,
            co.request_path) as full_request_path
        FROM `mysql_rest_service_metadata`.content_set co
            LEFT OUTER JOIN `mysql_rest_service_metadata`.service se
                ON se.id = co.service_id
            LEFT JOIN `mysql_rest_service_metadata`.url_host h
                ON se.url_host_id = h.id
        WHERE CONCAT(h.name, se.url_context_root,
                co.request_path) = ?
        """, [request_path, request_path, request_path, request_path])

    row = res.fetch_one()

    if row and row.get_field("full_request_path") != "":
        raise Exception(f"The request_path {request_path} is already "
                    "in use.")


def convert_json(value):
    try:
        value_str = json.dumps(value)
    except:
        value_str = str(value)
        value_str = value_str.replace("{'", '{"')
        value_str = value_str.replace("'}'", '"}')
        value_str = value_str.replace("', '", '", "')
        value_str = value_str.replace("': '", '": "')
        value_str = value_str.replace("': [", '": [')
        value_str = value_str.replace("], '", '], "')
        value_str = value_str.replace("['", '["')
        value_str = value_str.replace("']", '"]')
        value_str = value_str.replace("': ", '": ')
        value_str = value_str.replace(", '", ', "')
        value_str = value_str.replace(": b\'", ': "')
    return json.loads(value_str)


def id_to_binary(id: str, context: str):
    if isinstance(id, bytes):
        return id
    elif isinstance(id, str):
        if id.startswith("0x"):
            try:
                result = bytes.fromhex(id[2:])
            except Exception:
                raise RuntimeError(f"Invalid hexadecimal string for {context}.")
        else:
            try:
                result = base64.b64decode(id, validate=True)
            except Exception:
                raise RuntimeError(f"Invalid base64 string for {context}.")

        if len(result) != 16:
            raise RuntimeError(f"The {context} has an invalid size.")
        return result

    raise RuntimeError(f"Invalid id type for {context}.")

def convert_ids_to_binary(id_options, kwargs):
   for id_option in id_options:
      id = kwargs.get(id_option)
      if id is not None:
        kwargs[id_option] = id_to_binary(id, id_option)

def _generate_where(where):
    if where:
       if isinstance(where, list):
         return " WHERE " + " AND ".join(where)
       else:
         return " WHERE " + where
    return ""


def _generate_table(table):
    if '.' in table:
        return table
    return f"`mysql_rest_service_metadata`.`{table}`"


def _generate_qualified_name(name):
    if '.' in name:
        return name
    parts = name.split("(")
    result = f"`mysql_rest_service_metadata`.`{parts[0]}`"
    if len(parts) == 2:     # it's a function call so add the parameters
        result = f"{result}({parts[1]}"

    return result


class MrsDbExec:
    def __init__(self, sql: str, params=[]) -> None:
        self._sql = sql
        self._result = None
        self._params = params

    def _convert_to_database(self, var):
        if isinstance(var, list):
            return ",".join(var)
        if isinstance(var, dict):
            return json.dumps(dict(var))
        return var

    @property
    def dump(self) -> "MrsDbExec":
        print(f"sql: {self._sql}\nparams: {self._params}")
        return self

    def exec(self, session, params=[]) -> "MrsDbExec":
        self._params = self._params + params
        try:
            # convert lists and dicts to store in the database
            self._params = [self._convert_to_database(param) for param in self._params]

            self._result = session.run_sql(self._sql, self._params)
        except Exception as e:
            mysqlsh.globals.shell.log(LogLevel.WARNING.name, f"[{e}\nsql: {self._sql}\nparams: {self._params}")
            raise
        return self
    def __str__(self):
        return self._sql
    @property
    def items(self):
        return get_sql_result_as_dict_list(self._result)
    @property
    def first(self):
        result = get_sql_result_as_dict_list(self._result)
        if not result:
            return None
        return result[0]
    @property
    def success(self):
        return self._result.get_affected_items_count() > 0
    @property
    def id(self):
        return self._result.auto_increment_value
    @property
    def affected_count(self):
        return self._result.get_affected_items_count()


def select(table: str, cols=['*'], where=[], order=None) -> MrsDbExec:
    if not isinstance(cols, str):
        cols = ','.join(cols)
    if order is not None and not isinstance(order, str):
        order = ','.join(order)
    sql = f"""
        SELECT {cols}
        FROM {_generate_table(table)}
        {_generate_where(where)}"""
    if order:
        sql = f"{sql} ORDER BY {order}"

    return MrsDbExec(sql)

def update(table: str, sets, where=[]) -> MrsDbExec:
    params = []
    if isinstance(sets, list):
        sets = ','.join(sets)
    elif isinstance(sets, dict):
        params = [value for value in sets.values()]
        sets = ",".join([f"{key}=?" for key in sets.keys()])

    sql = f"""
        UPDATE {_generate_table(table)}
        SET {sets}
        {_generate_where(where)}"""

    return MrsDbExec(sql, params)

def delete(table: str, where=[]) -> MrsDbExec:
    sql = f"""
        DELETE FROM {_generate_table(table)}
        {_generate_where(where)}"""

    return MrsDbExec(sql)

def insert(table, values={}):
    params = []
    place_holders = []
    cols = []
    if isinstance(values, list):
        cols = ",".join(values)
        place_holders = ','.join(["?" for val in values])
    elif isinstance(values, dict):
        cols = ','.join([str(col) for col in values.keys()])
        place_holders = ','.join(["?" for val in values.values()])
        params = [val for val in values.values()]

    sql = f"""
        INSERT INTO {_generate_table(table)}
        ({cols})
        VALUES
        ({place_holders})
    """
    return MrsDbExec(sql, params)

def get_sequence_id(session):
    return MrsDbExec(f"SELECT {_generate_qualified_name('get_sequence_id()')} as id").exec(session).first["id"]

class MrsDbSession:
    def __init__(self, **kwargs) -> None:
        self._session = get_current_session(kwargs.get("session"))
        self._exception_handler = kwargs.get("exception_handler")

        _ensure_mrs_metadata_schema(self._session)

    def __enter__(self):
        return self._session

    def __exit__(self, exc_type, exc_value, exc_traceback):
        if exc_type is None:
            return

        if get_interactive_default() and self._exception_handler:
            return self._exception_handler(exc_type, exc_value, exc_traceback)
        return False

    @property
    def session(self):
        return self._session

class MrsDbTransaction:
    def __init__(self, session) -> None:
        self._session = session

    def __enter__(self) -> "MrsDbTransaction":
        self._session.start_transaction()
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback) -> bool:
        if exc_type is None:
            self._session.commit()
            return

        self._session.rollback()
        return False
