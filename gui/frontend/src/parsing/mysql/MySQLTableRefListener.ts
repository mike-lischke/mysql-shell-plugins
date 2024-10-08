/*
 * Copyright (c) 2020, 2024, Oracle and/or its affiliates.
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License, version 2.0,
 * as published by the Free Software Foundation.
 *
 * This program is designed to work with certain software (including
 * but not limited to OpenSSL) that is licensed under separate terms, as
 * designated in a particular file or component or in included license
 * documentation.  The authors of MySQL hereby grant you an additional
 * permission to link the program and your derivative works with the
 * separately licensed software that they have either included with
 * the program or referenced in the documentation.
 *
 * This program is distributed in the hope that it will be useful,  but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See
 * the GNU General Public License, version 2.0, for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software Foundation, Inc.,
 * 51 Franklin St, Fifth Floor, Boston, MA 02110-1301 USA
 */

import { AutoCompletionContext } from "./MySQLCodeCompletion.js";
import { TableRefContext, TableAliasContext } from "./generated/MySQLMRSParser.js";
import { MySQLMRSParserListener } from "./generated/MySQLMRSParserListener.js";

import { unquote } from "../../utilities/string-helpers.js";

// A listener to handle references as we traverse a parse tree.
// We have two modes here:
//   fromClauseMode = true: we are not interested in sub queries and don't need to stop at the caret.
//   otherwise: go down all sub queries and stop when the caret position is reached.
export class MySQLTableRefListener extends MySQLMRSParserListener {

    private done = false;
    private level = 0;

    public constructor(private context: AutoCompletionContext, private fromClauseMode: boolean) {
        super();
    }

    public override exitTableRef = (ctx: TableRefContext): void => {
        if (this.done) {
            return;
        }

        if (!this.fromClauseMode || this.level === 0) {
            if (ctx.qualifiedIdentifier()) {
                let table = unquote(ctx.qualifiedIdentifier()!.identifier().getText());
                let schema = "";
                if (ctx.qualifiedIdentifier()?.dotIdentifier()) {
                    // Full schema.table reference.
                    schema = table;
                    table = unquote(ctx.qualifiedIdentifier()!.dotIdentifier()!.identifier().getText());
                }
                this.context.pushTableReference({
                    schema,
                    table,
                    alias: "",
                });
            } else {
                // No schema reference.
                this.context.pushTableReference({
                    schema: "",
                    table: unquote(ctx.dotIdentifier()!.identifier().getText()),
                    alias: "",
                });
            }
        }
    };

    public override exitTableAlias = (ctx: TableAliasContext): void => {
        if (this.done) {
            return;
        }

        if (this.level === 0) {
            // Appears after a single or derived table.
            // Since derived tables can be very complex it is not possible here to determine possible columns for
            // completion, hence we just walk over them and thus have no field where to store the found alias.
            this.context.setLastAlias(unquote(ctx.identifier().getText()));
        }
    };

    public override enterSubquery = (): void => {
        if (this.done) {
            return;
        }

        if (this.fromClauseMode) {
            ++this.level;
        } else {
            this.context.pushNewReferenceList();
        }
    };

    public override exitSubquery = (): void => {
        if (this.done) {
            return;
        }

        if (this.fromClauseMode) {
            --this.level;
        } else {
            this.context.popReferenceList();
        }
    };

}
