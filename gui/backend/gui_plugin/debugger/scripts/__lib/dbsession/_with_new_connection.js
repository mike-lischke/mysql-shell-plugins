var lib = ws.tokens.lib
var _this = lib.dbsession.with_new_connection
var settings = _this.params["database_settings"]

lib.dbsession.open_db_connection.params = {
    "connection_id": settings.result["connection_id"],
    "default_schema": settings.result["default_schema"],
    "validation": _this.params["validation"]
}

await ws.execute(lib.dbsession.open_db_connection.file)

//  Parameters to the sub-script should be set in the caller script
await ws.execute(_this.params["test"].file)

lib.connection.remove.params = {
    "profile_id": settings.result["profile_id"],
    "connection_id": settings.result["connection_id"]
}

await ws.execute(lib.connection.remove.file)
