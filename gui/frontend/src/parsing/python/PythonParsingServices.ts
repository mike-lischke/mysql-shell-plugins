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
 * documentation. The authors of Python hereby grant you an additional
 * permission to link the program and your derivative works with the
 * separately licensed software that they have included with
 * This program is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See
 * the GNU General Public License, version 2.0, for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software Foundation, Inc.,
 * 51 Franklin St, Fifth Floor, Boston, MA 02110-1301 USA
 */

// This file contains the main interface to all language services for Python.

import {
    CommonTokenStream, BailErrorStrategy, DefaultErrorStrategy, CharStreams,
} from "antlr4ts";
import { ParseCancellationException } from "antlr4ts/misc";
import { ParseTree } from "antlr4ts/tree";
import { PredictionMode } from "antlr4ts/atn/PredictionMode";

import { PythonLexer } from "./generated/PythonLexer";
import { PythonParser } from "./generated/PythonParser";
import { PythonErrorListener } from "./PythonErrorListener";

import { IParserErrorInfo } from "../parser-common";
import { unquote } from "../../utilities/string-helpers";

export enum PythonParseUnit {
    Generic
}

export class PythonParsingServices {

    private static services?: PythonParsingServices;
    private static readonly delimiterKeyword = /delimiter/i;

    private lexer = new PythonLexer(CharStreams.fromString(""));
    private tokenStream = new CommonTokenStream(this.lexer);
    private parser = new PythonParser(this.tokenStream);
    private errors: IParserErrorInfo[] = [];

    private tree: ParseTree | undefined;

    private errorListener = new PythonErrorListener (
        (message: string, tokenType: number, startIndex: number, line: number, column: number,
            length: number): void => {

            if (length === 0) {
                length = 1;
            }

            this.errors.push({ message, tokenType, charOffset: startIndex, line, offset: column, length });
        },
    );

    private constructor() {
        this.lexer.removeErrorListeners();
        this.lexer.addErrorListener(this.errorListener);

        this.parser.removeParseListeners();
        this.parser.removeErrorListeners();
        this.parser.addErrorListener(this.errorListener);
    }

    /**
     * Creates the parsing services instance on demand. This involves loading certain data files.
     *
     * @returns The singleton instance of the parsing services.
     */
    public static get instance(): PythonParsingServices {
        if (!PythonParsingServices.services) {
            PythonParsingServices.services = new PythonParsingServices();
        }

        return PythonParsingServices.services;
    }

    /**
     * Quick check for syntax errors.
     *
     * @param text The text to parse.
     * @param unit The type of input. Can be used to limit the available syntax to certain constructs.
     *
     * @returns True if no error was found, otherwise false.
     */
    public errorCheck(text: string, unit: PythonParseUnit): boolean {
        this.startParsing(text, true, unit);

        return this.errors.length === 0;
    }

    /**
     * Returns a collection of errors from the last parser run. The start position is offset by the given
     * value (used to adjust error position in a larger context).
     *
     * @param offset The character offset to add for each error.
     *
     * @returns The updated error list from the last parse run.
     */
    public errorsWithOffset(offset: number): IParserErrorInfo[] {
        const result: IParserErrorInfo[] = [...this.errors];
        result.forEach((error: IParserErrorInfo) => {
            error.charOffset += offset;
        });

        return result;
    }

    /**
     * Used to tokenize the given text to see if there's a string token covering the given position.
     *
     * @param text The text to examine.
     * @param line The (zero-based) line number for the text.
     * @param offset The (zero-based) column in that text.
     *
     * @returns The string, if one was found. Otherwise undefined.
     */
    public stringFromPosition = (text: string, line: number, offset: number): string | undefined => {
        const input = CharStreams.fromString(text);
        const lexer = new PythonLexer(input);
        const tokenStream = new CommonTokenStream(lexer);

        try {
            tokenStream.fill();
            const tokens = tokenStream.getTokens();

            // Find the token which contains the position.
            let index = 0;
            while (index < tokens.length) {
                let token = tokens[index];
                const tokenLine = token.line - 1; // ANTLR lines are one-based.
                if (tokenLine > line || (tokenLine === line && token.charPositionInLine > offset)) {
                    // First token starting after the caret.
                    if (index > 0) {
                        // See if the previous token starts before or on the caret.
                        token = tokens[index - 1];
                        if (token.line - 1 < line || token.charPositionInLine <= offset) {
                            if (token.type === PythonLexer.STRING && token.text) {
                                return unquote(token.text);
                            }

                            break;
                        }
                    }
                }

                ++index;
            }
        } catch (reason) {
            return undefined;
        }

        return undefined;
    };

    /**
     * This is the method to parse text. Depending on fast mode it creates a syntax tree and otherwise
     * bails out if an error was found, asap.
     *
     * @param text The text to parse.
     * @param fast If true use fast mode (no parse tree creation, fast bail out in case of errors).
     * @param unit The type of input to parse.
     *
     * @returns A parse tree if enabled.
     */
    private startParsing(text: string, fast: boolean, unit: PythonParseUnit): ParseTree | undefined {
        this.errors = [];
        this.lexer.inputStream = CharStreams.fromString(text);
        this.tokenStream.tokenSource = this.lexer;

        this.parser.reset();
        this.parser.buildParseTree = !fast;

        // First parse with the bail error strategy to get quick feedback for correct queries.
        this.parser.errorHandler = new BailErrorStrategy();
        this.parser.interpreter.setPredictionMode(PredictionMode.SLL);

        try {
            this.tree = this.parseUnit(unit);
        } catch (e) {
            if (e instanceof ParseCancellationException) {
                // Even in fast mode we have to do a second run if we got no error yet (BailErrorStrategy
                // does not do full processing).
                if (fast && this.errors.length > 0) {
                    this.tree = undefined;
                } else {
                    // If parsing was canceled we either really have a syntax error or we need to do a second step,
                    // now with the default strategy and LL parsing.
                    this.tokenStream.seek(0);
                    this.parser.reset();
                    this.errors = [];
                    this.parser.errorHandler = new DefaultErrorStrategy();
                    this.parser.interpreter.setPredictionMode(PredictionMode.LL);
                    this.tree = this.parseUnit(unit);
                }
            } else {
                throw e;
            }
        }

        return this.tree;
    }

    /**
     * Starts a single parse run for a given input type.
     *
     * @param unit The type of input to parse.
     *
     * @returns A parse tree, if enabled.
     */
    private parseUnit(unit: PythonParseUnit): ParseTree | undefined {
        switch (unit) {
            default: // Generic.
                return this.parser.root();
        }
    }

}
