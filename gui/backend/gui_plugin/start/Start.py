# Copyright (c) 2020, 2021, Oracle and/or its affiliates.
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
# Implementation of the MySQL Shell GUI web server

import subprocess
from mysqlsh.plugin_manager import plugin_function # pylint: disable=no-name-in-module
from gui_plugin.core.ShellGuiWebSocketHandler import ShellGuiWebSocketHandler
from gui_plugin.core.ThreadedHTTPServer import ThreadedHTTPServer
import mysqlsh
import ssl
import os
import sqlite3
from os import path
import json
import socket
from contextlib import closing
import uuid
from subprocess import Popen
import re
import time
import platform
import sys
import tempfile
import shutil
import signal
import gui_plugin.core.Logger as logger


@plugin_function('gui.start.webServer', cli=True)
def web_server(port=None, secure=None, webrootpath=None, single_instance_token=None):
    """Starts a web server that will serve the MySQL Shell GUI

    Args:
        port (int): The optional port the web server should be running on,
            defaults to 8000
        secure (dict): A dict with keyfile and certfile keys and values. An
            empty dict will use the default key and certificate files. If
            'None' is passed, then SSL will not be used.
        webrootpath (str): The optional web root path that will be used
            by the web server to serve files
        single_instance_token (str): A token string used to establish
            local user mode.

    Allowed options for secure:
        keyfile (str): The path to the server private key file
        certfile (str): The path to the server certificate file

    Returns:
        Nothing
    """
    # Start the web server
    logger.info(f'Starting MySQL Shell GUI web server...')

    # Get hold of the global shell object
    shell = mysqlsh.globals.shell

    server = None
    try:
        core_path = os.path.abspath(os.path.join(
            os.path.dirname(__file__), '..', 'core'))

        # Set defaults when necessary
        if port is None:
            port = 8000

        if webrootpath is None:
            webrootpath = os.path.join(core_path, 'webroot')

        # cspell:ignore chdir
        if not os.path.isdir(webrootpath):
            raise Exception(
                f'Cannot start webserver. Root directory does not exist({webrootpath}).')

        os.chdir(webrootpath)

        # Check if we can supply a default page
        if not os.path.isfile("index.html"):
            raise Exception(
                f'Cannot start webserver. The "index.html" file does not exist in {webrootpath}.')

        # try to cast from shell.Dict to dict
        try:
            secure = json.loads(str(secure))
        except:
            pass

        # Replace WSSimpleEcho with your own subclass of HTTPWebSocketHandler
        server = ThreadedHTTPServer(
            ('127.0.0.1', port), ShellGuiWebSocketHandler)
        server.daemon_threads = True
        server.host = f'{"https" if secure else "http"}://127.0.0.1'
        server.port = port
        server.single_instance_token = single_instance_token

        if type(secure) is dict:
            if 'keyfile' not in secure or secure['keyfile'] == "default":
                secure['keyfile'] = path.join(*[
                    core_path,
                    'certificates',
                    'server.key'])
            if 'certfile' not in secure or secure['certfile'] == "default":
                secure['certfile'] = path.join(*[
                    core_path,
                    'certificates',
                    'server.crt'])

            server.socket = ssl.wrap_socket(server.socket,
                                            keyfile=secure['keyfile'],
                                            certfile=secure['certfile'],
                                            server_side=True)

        def user_signal_handler(signum, frame):
            server.force_stop()

        # Register signal handler for SIGINT (handle ctrl+c)
        signal.signal(signal.SIGINT, user_signal_handler)

        try:
            logger.info(
                f"Server started [port:{port}, secure:{'version' in dir(server.socket)}, single user: {server.single_instance_token is not None}]", ['session'])

            # Log server start
            logger.info(f"\tPort: {port}")
            logger.info(f"\tSecure: {'version' in dir(server.socket)}")
            logger.info(f"\tWebroot: {webrootpath}")
            logger.info(
                f"\tMode: {f'Single user [token={server.single_instance_token}]' if server.single_instance_token is not None else 'Multi-user'}")

            # Start web server
            server.serve_forever()
            # TODO(anyone): Using the 'session' tag here causes database locks
            # logger.info("Web server is down.", ['session'])
            logger.info("Web server is down.")
        except Exception as e:  # pragma: no cover
            logger.error(f'Log message could not be inserted into db. {e}')
    except KeyboardInterrupt:  # pragma: no cover
        print('^C received, shutting down server')
        if server:
            server.socket.close()


@plugin_function('gui.start.nativeUi', cli=True)
def native_ui():
    """Starts the native Shell GUI client

    Returns:
        Nothing
    """

    wrappers_path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "wrappers"))

    if platform.system() == "Linux":
        browser_app()
        return
    elif platform.system() == "Windows":
        browser_app()
        return
    elif platform.system() == "Darwin":
        executable_path = os.path.join(
            wrappers_path, "macos", "MySQL Shell GUI.app", "Contents", "MacOS", "MySQL Shell GUI")

    try:
        process = Popen(executable_path)
    except Exception as e:
        print(f"Unable to launch the native application: {str(e)}")
        return

    print(f"The native client was launched with the PID: {process.pid}")


def browser_app():
    """Starts the browser application in single user mode

    Returns:
        Nothing
    """
    browser_executable = ""
    if platform.system() == "Linux":
        browser_executable = "chromium"
        try:
            Popen([browser_executable, "--version"], stdin=subprocess.PIPE,
                  stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="UTF-8")
        except FileNotFoundError:
            print(
                f"Can't find installed Chromium browser. Install it first and then try again.")
            return

    elif platform.system() == "Windows":
        browser_executable = "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe"
        if not os.path.exists(browser_executable):
            print("Unable to find the Microsoft Edge browser.")
            return
    else:
        print("This function is only available on Linux and Windows")

    port = None
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(('localhost', 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        _, port = s.getsockname()

    token = str(uuid.uuid1())
    certs = {}
    url = f"https://localhost:{port}?token={token}"
    command = sys.executable if sys.executable else "mysqlsh"
    p_web_server = Popen(
        [command, '--py', '-e', f'gui.start.web_server(port={port}, secure={certs}, single_instance_token="{token}")'])

    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        while s.connect_ex(('localhost', port)) != 0:
            time.sleep(1)

    leftover_path = ""
    try:
        # In order to support running more than one instance of the application it is required to use a different user data dir
        # for this reason we create a temporary directory every time the application is launched
        data_dir_path = mysqlsh.plugin_manager.general.get_shell_user_dir( # pylint: disable=no-member
            'plugin_data', 'gui_plugin')
        with tempfile.TemporaryDirectory(dir=data_dir_path) as data_path:
            leftover_path = data_path

            p_application = None

            # The --allow-insecure-localhost is used to have the application bypass ERR_CERT_AUTHORITY_INVALID
            # Note the only differences on the calls below is how the --user-data-dir is passed, it is on purpose
            # Both OS's seem to dislike the other way
            if platform.system() == "Linux":
                p_application = Popen([
                    browser_executable, '--user-data-dir', data_path, '--allow-insecure-localhost', '--new-window', '--ignore-certificate-errors', '--ignore-ssl-errors', f'--app={url}'])
            else:
                p_application = Popen([
                    browser_executable, f'--user-data-dir={data_path}', '--allow-insecure-localhost', '--new-window', '--ignore-certificate-errors', '--ignore-ssl-errors', f'--app={url}'])

            p_application.communicate()
            p_application.wait()
    except PermissionError:
        # In Windows, it is possible that the file handles on the data dir are not released when the temporary directory is cleaned up
        # for that reason, we need this fallback cleanup logic to make it succeed
        done = False
        attempt = 0
        while not done and attempt < 5:
            try:
                time.sleep(1)
                shutil.rmtree(leftover_path)
                done = True
            except PermissionError:
                attempt += 1

    p_web_server.kill()
