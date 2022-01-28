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
import { mount } from "enzyme";
import { act } from "preact/test-utils";
import React from "react";

import { Radiobutton, CheckState, IRadiobuttonProperties } from "../../../../components/ui/index";
import { eventMock } from "../../__mocks__/MockEvents";

describe("Radiobutton component tests", (): void => {

    it("Test Radiobutton output 1", async () => {
        const component = mount(
            <Radiobutton id="rb1" onClick={jest.fn()} name="rb">
                Unchecked radiobutton
            </Radiobutton>,
        );
        expect(component).toBeTruthy();
        expect(component.text()).toEqual("Unchecked radiobutton");

        const instance = component.instance();
        const spyOnClick = jest.spyOn(instance.props as IRadiobuttonProperties, "onClick");
        expect(spyOnClick).not.toBeCalled();
        const click = (component.props() as IRadiobuttonProperties).onClick;
        await act(() =>  {
            click?.(eventMock, {id: "1"});
        });
        expect(spyOnClick).toBeCalled();
    });

    it("Test Radiobutton output (snapshot)", () => {
        const component = render(
            <Radiobutton
                id="rb4"
                name="rbx"
                disabled
                checkState={CheckState.Checked}
            >
                Disabled radio button
            </Radiobutton>,
        );
        expect(component).toMatchSnapshot();
    });
});
