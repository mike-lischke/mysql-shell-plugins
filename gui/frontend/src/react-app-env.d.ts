/*
 * Copyright (c) 2020, 2021, Oracle and/or its affiliates.
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License, version 2.0,
 * as published by the Free Software Foundation.
 *
 * This program is also distributed with certain software (including
 * but not limited to OpenSSL) that is licensed under separate terms, as
 * designated in a particular file or component or in included license
 * documentation.  The authors of MySQL hereby grant you an additional
 * permission to link the program and your derivative works with the
 * separately licensed software that they have included with MySQL.
 * This program is distributed in the hope that it will be useful,  but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See
 * the GNU General Public License, version 2.0, for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software Foundation, Inc.,
 * 51 Franklin St, Fifth Floor, Boston, MA 02110-1301 USA
 */
/// <reference types="react-scripts" />
/// <reference types="enzyme-adapter-preact-pure" />

declare module "monaco-editor/esm/vs/basic-languages/typescript/typescript";
declare module "monaco-editor/esm/vs/basic-languages/javascript/javascript";
declare module "monaco-editor/esm/vs/basic-languages/mysql/mysql";
declare module "monaco-editor/esm/vs/basic-languages/python/python";
declare module "monaco-editor/esm/vs/platform/contextkey/common/contextkey";

declare module "pixi-ease/dist/ease";

declare module "*.txt" {
    const content: string;
    export default content;
}

declare module "file-loader?name=[name].[contenthash].js!*" {
    const value: string;
    export = value;
}

declare module "worker-loader?filename=static/workers/[name].[contenthash].js!*" {
    class WebpackWorker extends Worker {
        public id: string;

        public constructor();
    }

    export default WebpackWorker;
}
