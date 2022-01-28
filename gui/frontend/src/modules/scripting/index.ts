/*
 * Copyright (c) 2020, 2022, Oracle and/or its affiliates.
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

import { ICommDbTypesEvent } from "../../communication";
import { EditorLanguage } from "../../supplement";
import { ShellInterfaceDbConnection } from "../../supplement/ShellInterface";

// The of an entry in trees etc.
export enum EntityType {
    Console,
    Script,
    Table,
    Folder,
}

export enum SchemaTreeType {
    Document,
    Schema,
    Table,
    Routine,
    Event,
    Trigger,
    Column,
    Function,
    Views,
    Indexes,
    ForeignKeys,
    Triggers,
    GroupNode,
    UserVariable,
    User,
    Engine,
    Plugin,
    Character
}

export interface ISchemaTreeEntry<T = unknown> {
    type: SchemaTreeType;
    expanded: boolean;     // Currently expanded?
    expandedOnce: boolean; // Was expanded before?

    id: string;            // To uniquely address the entry.
    caption: string;       // The text to show in the tree.
    qualifiedName: {       // The parts of the FQN to access a db object.
        schema: string;
        table?: string;
        name?: string;     // Column or index name.
    };

    details: T;
    children?: Array<ISchemaTreeEntry<T>>;
}

// Base fields for entries in the various sections on a scripting tab.
export interface IEntityBase {
    type: EntityType;

    id: string;
    caption: string;
}

export interface IModuleDataEntry extends IEntityBase {
    // The id under which this entry is reachable in the backend.
    moduleDataId: number;

    // The module data ID of the folder in which this entry resides.
    folderId: number;
}

export interface IFolderEntity extends IModuleDataEntry {
    children: IModuleDataEntry[];
}

export interface IDBEditorScriptState extends IModuleDataEntry {
    language: EditorLanguage;
}

export interface IEditorStatusInfo {
    insertSpaces?: boolean;
    indentSize?: number;
    tabSize?: number;
    line?: number;
    column?: number;
    language?: string;
    eol?: string;
}

export const languageMap: Map<EditorLanguage, string> = new Map([
    ["msg", "Combined"],
    ["typescript", "TypeScript"],
    ["javascript", "JavaScript"],
    ["mysql", "MySQL"],
    ["sql", "SQlite"],
]);

const registeredDbTypes: string[] = [];

export const enumerateDbTypeNames = (): string[] => {
    return registeredDbTypes;
};

/**
 * Called on creation of the connection browser to load known database types if not yet done.
 * They are used to convert db IDs to our DB enum.
 *
 * @param backend The interface to the communication backend.
 */
export const initializeDbTypes = (backend: ShellInterfaceDbConnection): void => {
    if (registeredDbTypes.length === 0) {
        backend.getDbTypes().then((event: ICommDbTypesEvent) => {
            if (event.data) {
                registeredDbTypes.push(...event.data.dbType);
            }
        });
    }
};

