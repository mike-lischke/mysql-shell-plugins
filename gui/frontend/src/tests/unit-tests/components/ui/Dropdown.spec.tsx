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

import { render } from "@testing-library/preact";
import { shallow } from "enzyme";
import React from "react";

import { Dropdown } from "../../../../components/ui/index";

describe("Dropdown render testing", (): void => {

    it("Test Dropdown onSelect callback test", () => {
        const component = shallow<Dropdown>(
            <Dropdown initialSelection="tesla" optional={false} onSelect={jest.fn()} style={{ maxWidth: "300px" }}>
                <Dropdown.Item id="tesla" caption="Tesla" />
                <Dropdown.Item id="volvo" caption="Volvo" />
                <Dropdown.Item id="bmw" caption="BMW" />
                <Dropdown.Item id="renault" caption="Renault" />
            </Dropdown>,
        );

        const instance = component.instance();
        const spyOnChange = jest.spyOn(instance.props, "onSelect");
        instance.selectEntry("x", false);
        expect(spyOnChange).toBeCalled();
    });

    it("Test Dropdown output (snapshot)", () => {
        const component = render(
            <Dropdown initialSelection="tesla" optional={false} style={{ maxWidth: "300px" }}>
                <Dropdown.Item id="tesla" caption="Tesla" />
                <Dropdown.Item id="volvo" caption="Volvo" />
                <Dropdown.Item id="bmw" caption="BMW" />
                <Dropdown.Item id="renault" caption="Renault" />
            </Dropdown>,
        );
        expect(component).toMatchSnapshot();
    });
});
