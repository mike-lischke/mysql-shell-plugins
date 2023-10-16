/*
 * Copyright (c) 2021, 2023, Oracle and/or its affiliates.
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

import { IMrsDbObjectData } from "../../../../frontend/src/communication/ProtocolMrs";
import { ShellInterfaceSqlEditor } from "../../../../frontend/src/supplement/ShellInterface/ShellInterfaceSqlEditor";
import { convertToPascalCase } from "../../../../frontend/src/utilities/string-helpers";
import { MrsTreeBaseItem } from "./MrsTreeBaseItem";

export class MrsDbObjectTreeItem extends MrsTreeBaseItem {
    public contextValue = "mrsDbObject";

    public constructor(
        label: string,
        public value: IMrsDbObjectData,
        backend: ShellInterfaceSqlEditor,
        connectionId: number) {
        super(label, backend, connectionId, MrsDbObjectTreeItem.getIconName(value), false);
    }

    private static getIconName = (value: IMrsDbObjectData): string => {
        let iconName = "mrsDbObject" + convertToPascalCase(value.objectType.toLowerCase());
        iconName += value.requiresAuth === 1 ? "Locked" : "";
        iconName += value.enabled !== 1 ? "Disabled" : "";

        return iconName + ".svg";
    };
}
