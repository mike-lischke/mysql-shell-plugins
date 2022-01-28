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

import { render } from "@testing-library/preact";
import { shallow } from "enzyme";
import React from "react";

import { Label, ComponentSize, TextAlignment, ILabelProperties } from "../../../../components/ui/index";

describe("Label component test", (): void => {

    it("Test Label elements", () => {
        const component = shallow(
            <Label
                id="myLabel1"
                textAlignment={TextAlignment.Center}
                size={ComponentSize.Tiny}>
                Tiny Label
            </Label>,
        );
        expect(component).toBeTruthy();
        const props = component.props();
        expect(props.id).toEqual("myLabel1");
    });


    it("Test Label output (Snapshot)", () => {
        const component = render(
            <Label as="h1">H1 Label</Label>,
        );
        expect(component).toMatchSnapshot();
    });

    it("Label with ansi formatting", () => {
        const component = shallow<ILabelProperties>(
            <Label
                caption="Lorem ipsum dolor sit amet"
                language="ansi"
            />,
        );

        const props = component.props();
        expect(props.className).toEqual("msg resultText");
    });

    it("Label with ansi formatting (Snapshot) 1", () => {
        const component = render(
            <Label
                language="ansi"
                caption="Lorem ipsum dolor sit amet"
            />,
        );
        expect(component).toMatchSnapshot();
    });

});

