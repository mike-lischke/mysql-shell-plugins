/*
 * Copyright (c) 2022, Oracle and/or its affiliates.
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
import {
    By,
    EditorView,
    Workbench,
    OutputView,
    until,
    BottomBarPanel,
    TextEditor,
    ModalDialog,
} from "vscode-extension-tester";

import { before, after, afterEach } from "mocha";
import fs from "fs/promises";
import { expect } from "chai";
import {
    dbTreeSection,
    ociTreeSection,
    consolesTreeSection,
    tasksTreeSection,
    driver,
    explicitWait,
    ociExplicitWait,
    ociTasksExplicitWait,
    Misc,
    isExtPrepared,
} from "../lib/misc";

import { Database } from "../lib/db";
import { homedir } from "os";
import { join } from "path";

describe("ORACLE CLOUD INFRASTRUCTURE", () => {

    before(async function () {

        try {
            if (!isExtPrepared) {
                await Misc.prepareExtension();
            }
            await Misc.initTreeSection(ociTreeSection);
            await Misc.toggleSection(dbTreeSection, false);
            await Misc.toggleSection(ociTreeSection, true);
            await Misc.toggleSection(consolesTreeSection, false);
            await Misc.toggleSection(tasksTreeSection, false);
            await Misc.toggleBottomBar(false);

            const path = join(homedir(), ".oci", "config");
            await fs.writeFile(path, "");

            const btn = await Misc.getSectionToolbarButton(ociTreeSection,
                "Configure the OCI Profile list");
            await btn.click();

            const editors = await new EditorView().getOpenEditorTitles();
            expect(editors).to.include.members(["config"]);

            const textEditor = new TextEditor();

            const editor = await driver.findElement(By.css("textarea"));

            let config = `[E2ETESTS]\nuser=ocid1.user.oc1..aaaaaaaan67cojwa52khe44xtpqsygzxlk4te6gqs7nkmy`;
            config += `abcju2w5wlxcpq\nfingerprint=15:cd:e2:11:ed:0b:97:c4:e4:41:c5:44:18:66:72:80\n`;
            config += `tenancy=ocid1.tenancy.oc1..aaaaaaaaasur3qcs245czbgrlyshd7u5joblbvmxddigtubzqcfo`;
            config += `5mmi2z3a\nregion=us-ashburn-1\nkey_file= ~/.oci/id_rsa_e2e.pem`;
            await editor.sendKeys(config);

            await textEditor.save();
            await Misc.reloadSection(ociTreeSection);

            await driver.wait(async () => {
                return Misc.existsTreeElement(ociTreeSection, "E2ETESTS (us-ashburn-1)");
            }, explicitWait, "E2ETESTS (us-ashburn-1) tree item was not found");

            await Misc.toggleTreeElement(ociTreeSection, "E2ETESTS*", true);

            await driver.wait(async () => {
                return !(await Misc.hasLoadingBar(ociTreeSection));
            }, 20000, "Loading bar is still displayed");

            await Misc.hasTreeChildren(ociTreeSection, "E2ETESTS*");
            await Misc.toggleTreeElement(ociTreeSection, "QA*", true);
            await driver.wait(async () => {
                return !(await Misc.hasLoadingBar(ociTreeSection));
            }, ociExplicitWait, "Loading bar is still displayed");
            await Misc.toggleTreeElement(ociTreeSection, "MySQLShellTesting", true);
            await driver.wait(async () => {
                return !(await Misc.hasLoadingBar(ociTreeSection));
            }, ociExplicitWait, "Loading bar is still displayed");
            await Misc.hasTreeChildren(ociTreeSection,
                "MySQLShellTesting", "MDSforVSCodeExtension");

        } catch (e) {
            await Misc.processFailure(this);
            throw e;
        }

    });

    after(async function () {

        try {
            await Misc.toggleSection(ociTreeSection, false);
            await fs.unlink(join(homedir(), ".oci", "config"));
        } catch (e) {
            await Misc.processFailure(this);
            throw e;
        }

    });

    describe("Profile", () => {

        afterEach(async function () {
            if (this.currentTest?.state === "failed") {
                await Misc.processFailure(this);
            }

            await driver.switchTo().defaultContent();
            const edView = new EditorView();
            const editors = await edView.getOpenEditorTitles();
            for (const editor of editors) {
                await edView.closeEditor(editor);
                try {
                    const dialog = new ModalDialog();
                    await dialog.pushButton("Don't Save");
                } catch (e) {
                    //continue
                }
            }
        });

        it("View Config Profile Information", async () => {

            await Misc.selectContextMenuItem(ociTreeSection,
                "E2ETESTS (us-ashburn-1)", "View Config Profile Information");

            const editors = await new EditorView().getOpenEditorTitles();
            expect(editors).to.include.members(["E2ETESTS Info.json"]);

            const textEditor = new TextEditor();
            await driver.wait(async () => {
                return (await textEditor.getText()).length > 0;
            }, 3000, "No text was found on file");

            expect(Misc.isJson(await textEditor.getText())).to.equal(true);

        });

        it("Set as New Default Config Profile", async () => {

            await Misc.selectContextMenuItem(ociTreeSection,
                "E2ETESTS (us-ashburn-1)", "Set as New Default Config Profile");

            expect(await Misc.isDefaultItem(ociTreeSection,
                "profile", "E2ETESTS (us-ashburn-1)")).to.equal(true);
        });
    });

    describe("Compartment", () => {

        let compartmentId = "";

        afterEach(async function () {
            if (this.currentTest?.state === "failed") {
                await Misc.processFailure(this);
            }

            await driver.switchTo().defaultContent();
            const edView = new EditorView();
            const editors = await edView.getOpenEditorTitles();
            for (const editor of editors) {
                await edView.closeEditor(editor);
                try {
                    const dialog = new ModalDialog();
                    await dialog.pushButton("Don't Save");
                } catch (e) {
                    //continue
                }
            }
        });

        after(async function () {

            try {
                await Misc.toggleSection(consolesTreeSection, false);
            } catch (e) {
                await Misc.processFailure(this);
                throw e;
            }

        });

        it("View Compartment Information", async () => {

            await Misc.selectContextMenuItem(ociTreeSection,
                "QA*", "View Compartment Information");

            await driver.wait(async () => {
                const editors = await new EditorView().getOpenEditorTitles();

                return editors.includes("QA Info.json");
            }, explicitWait, "'QA Info.json' was not opened");

            const textEditor = new TextEditor();
            await driver.wait(async () => {
                return (await textEditor.getText()).indexOf("{") !== -1;
            }, explicitWait, "No text was found inside QA Info.json");

            const json = await textEditor.getText();
            expect(Misc.isJson(json)).to.equal(true);

            const parsed = JSON.parse(json);
            compartmentId = parsed.id;

        });

        it("Set as Current Compartment", async () => {

            await Misc.selectContextMenuItem(ociTreeSection,
                "QA*", "Set as Current Compartment");

            await driver.wait(async () => {
                return !(await Misc.hasLoadingBar(ociTreeSection));
            }, ociExplicitWait, "There is still a loading bar on OCI");

            expect(await Misc.isDefaultItem(ociTreeSection, "compartment", "QA*")).to.be.true;

            expect(await Misc.hasTreeChildren(ociTreeSection,
                "E2ETESTS (us-ashburn-1)", "QA")).to.be.true;

            await Misc.toggleSection(consolesTreeSection, true);
            const btn = await Misc.getSectionToolbarButton(consolesTreeSection, "Add a New MySQL Shell Console");
            await btn.click();

            await Misc.switchToWebView();

            await driver.wait(until.elementLocated(By.id("shellEditorHost")), 20000, "Console was not loaded");

            const result = await Misc.execCmd("mds.get.currentCompartmentId()", 60000);

            expect(result[0]).to.equal(compartmentId);

        });

    });

    describe("DB System", () => {

        let outputView: OutputView;

        before(async function () {
            try {
                const bottomBar = new BottomBarPanel();
                outputView = await bottomBar.openOutputView();
                await Misc.toggleSection(tasksTreeSection, true);
            } catch (e) {
                await Misc.processFailure(this);
                throw e;
            }
        });

        beforeEach(async function () {
            try {
                await driver.wait(async () => {
                    return !(await Misc.hasLoadingBar(ociTreeSection));
                }, ociExplicitWait, "There is still a loading bar on OCI");
                await outputView.clearText();
            } catch (e) {
                await Misc.processFailure(this);
                throw e;
            }
        });

        afterEach(async function () {
            if (this.currentTest?.state === "failed") {
                await Misc.processFailure(this);
            }

            await driver.switchTo().defaultContent();
            const edView = new EditorView();
            const editors = await edView.getOpenEditorTitles();
            for (const editor of editors) {
                await edView.closeEditor(editor);
                try {
                    const dialog = new ModalDialog();
                    await dialog.pushButton("Don't Save");
                } catch (e) {
                    //continue
                }
            }
        });

        after(async function () {
            try {
                await Misc.toggleBottomBar(false);
                await Misc.toggleSection(tasksTreeSection, false);
            } catch (e) {
                await Misc.processFailure(this);
                throw e;
            }
        });


        it("View DB System Information", async () => {

            await Misc.selectContextMenuItem(ociTreeSection,
                "MDSforVSCodeExtension", "View DB System Information");

            await driver.wait(async () => {
                const editors = await new EditorView().getOpenEditorTitles();

                return editors.includes("MDSforVSCodeExtension Info.json");
            }, explicitWait, "MDSforVSCodeExtension Info.json was not opened");

            const textEditor = new TextEditor();
            await driver.wait(async () => {
                const text = await textEditor.getText();

                return text.includes("{");
            }, explicitWait, "No text was found inside MDSforVSCodeExtension Info.json");

            let json = await textEditor.getText();
            if (Array.from(json)[0] === "a") {
                json = json.slice(1);
            }

            expect(Misc.isJson(json)).to.equal(true);

        });

        it("Start a DB System (and cancel)", async () => {

            await Misc.selectContextMenuItem(ociTreeSection,
                "MDSforVSCodeExtension", "Start the DB System");

            expect(await Misc.existsTreeElement(tasksTreeSection, "Start DB System (running)")).to.be.true;

            await Misc.waitForOutputText(outputView, "OCI profile 'E2ETESTS' loaded.", 30000);

            await Misc.verifyNotification("Are you sure you want to start the DB System");

            const workbench = new Workbench();
            const ntfs = await workbench.getNotifications();

            await ntfs[ntfs.length - 1].takeAction("NO");

            await Misc.waitForOutputText(outputView, "Operation cancelled", ociExplicitWait);

            await Misc.waitForOutputText(outputView, "Task 'Start DB System' completed successfully.",
                ociExplicitWait);

            expect(await Misc.existsTreeElement(tasksTreeSection, "Start DB System (done)")).to.be.true;


        });

        it("Restart a DB System (and cancel)", async () => {

            await Misc.selectContextMenuItem(ociTreeSection,
                "MDSforVSCodeExtension", "Restart the DB System");

            expect(await Misc.existsTreeElement(tasksTreeSection, "Restart DB System (running)")).to.be.true;

            await Misc.waitForOutputText(outputView, "OCI profile 'E2ETESTS' loaded.", ociTasksExplicitWait);

            await outputView.clearText();

            await Misc.verifyNotification("Are you sure you want to restart the DB System");

            const workbench = new Workbench();
            const ntfs = await workbench.getNotifications();

            await ntfs[ntfs.length - 1].takeAction("NO");

            await Misc.waitForOutputText(outputView, "Operation cancelled", ociExplicitWait);

            await Misc.waitForOutputText(outputView, "Task 'Restart DB System' completed successfully.",
                ociExplicitWait);

        });

        it("Stop a DB System (and cancel)", async () => {

            await Misc.selectContextMenuItem(ociTreeSection,
                "MDSforVSCodeExtension", "Stop the DB System");

            expect(await Misc.existsTreeElement(tasksTreeSection, "Stop DB System (running)")).to.be.true;

            await Misc.waitForOutputText(outputView, "OCI profile 'E2ETESTS' loaded.", ociTasksExplicitWait);

            await Misc.verifyNotification("Are you sure you want to stop the DB System");

            const workbench = new Workbench();
            const ntfs = await workbench.getNotifications();

            await ntfs[ntfs.length - 1].takeAction("NO");

            await Misc.waitForOutputText(outputView, "Operation cancelled", ociExplicitWait);

            await Misc.waitForOutputText(outputView, "Task 'Stop DB System' completed successfully.",
                ociExplicitWait);

        });

        it("Delete a DB System (and cancel)", async () => {

            await Misc.selectContextMenuItem(ociTreeSection,
                "MDSforVSCodeExtension", "Delete the DB System");

            expect(await Misc.existsTreeElement(tasksTreeSection, "Delete DB System (running)")).to.be.true;

            await Misc.waitForOutputText(outputView, "OCI profile 'E2ETESTS' loaded.", ociTasksExplicitWait);

            await Misc.verifyNotification("Are you sure you want to delete");

            const workbench = new Workbench();
            const ntfs = await workbench.getNotifications();

            await ntfs[ntfs.length - 1].takeAction("NO");

            await Misc.waitForOutputText(outputView, "Deletion aborted", ociTasksExplicitWait);

            await Misc.waitForOutputText(outputView, "Task 'Delete DB System' completed successfully.",
                ociExplicitWait);

        });

    });

    describe("Bastion", () => {

        beforeEach(async function () {
            try {
                await driver.wait(async () => {
                    return !(await Misc.hasLoadingBar(ociTreeSection));
                }, ociExplicitWait, "There is still a loading bar on OCI");
            } catch (e) {
                await Misc.processFailure(this);
                throw e;
            }
        });

        afterEach(async function () {
            if (this.currentTest?.state === "failed") {
                await Misc.processFailure(this);
            }

            await driver.switchTo().defaultContent();
            await Misc.toggleSection(tasksTreeSection, false);
            await Misc.toggleSection(consolesTreeSection, false);
            const edView = new EditorView();
            const editors = await edView.getOpenEditorTitles();
            for (const editor of editors) {
                await edView.closeEditor(editor);
                try {
                    const dialog = new ModalDialog();
                    await dialog.pushButton("Don't Save");
                } catch (e) {
                    //continue
                }
            }

        });

        after(async function () {
            try {
                await Misc.toggleBottomBar(false);
                await Misc.toggleSection(tasksTreeSection, false);
            } catch (e) {
                await Misc.processFailure(this);
                throw e;
            }
        });

        it("Create connection with Bastion Service", async () => {

            await Misc.selectContextMenuItem(ociTreeSection,
                "MDSforVSCodeExtension", "Create Connection with Bastion Service");

            await driver.wait(async () => {
                const editors = await new EditorView().getOpenEditorTitles();

                return editors.includes("DB Connections");
            }, explicitWait, "DB Connections was not opened");

            await Misc.switchToWebView();

            const newConDialog = await driver.wait(until.elementLocated(By.css(".valueEditDialog")),
                10000, "Connection dialog was not loaded");

            expect(await newConDialog.findElement(By.id("caption")).getAttribute("value"))
                .to.equal("MDSforVSCodeExtension");

            expect(await newConDialog.findElement(By.id("description")).getAttribute("value"))
                .to.equal("DB System used to test the MySQL Shell for VSCode Extension.");

            expect(await newConDialog.findElement(By.id("hostName")).getAttribute("value"))
                .to.match(/(\d+).(\d+).(\d+).(\d+)/);

            await newConDialog.findElement(By.id("userName")).sendKeys("dba");

            const mdsTab = await newConDialog.findElement(By.id("page3"));

            expect(mdsTab).to.exist;

            await mdsTab.click();

            await driver.wait(async () => {
                return await driver.findElement(By.id("mysqlDbSystemId")).getAttribute("value") !== "";
            }, 3000, "DbSystemID field was not set");

            await driver.wait(async () => {
                return await driver.findElement(By.id("bastionId")).getAttribute("value") !== "";
            }, 3000, "BastionID field was not set");

            await newConDialog.findElement(By.id("ok")).click();

            await driver.switchTo().defaultContent();

            const mds = await Database.getWebViewConnection("MDSforVSCodeExtension");

            expect(mds).to.exist;

            try {

                await Misc.switchToWebView();

                await mds.click();

                await driver.wait(async () => {
                    const fingerprintDialog = await driver.findElements(By.css(".visible.confirmDialog"));
                    let passwordDialog = await driver.findElements(By.css(".visible.passwordDialog"));
                    if (fingerprintDialog.length > 0) {
                        await fingerprintDialog[0].findElement(By.id("accept")).click();
                        passwordDialog = await driver.findElements(By.css(".visible.passwordDialog"));
                    }
                    if (passwordDialog.length > 0) {
                        await passwordDialog[0].findElement(By.css("input")).sendKeys("MySQLR0cks!");
                        await passwordDialog[0].findElement(By.id("ok")).click();

                        return true;
                    }

                    return false;
                }, 30000, "Dialogs were not displayed");

                const confirmDialog = await driver.wait(until.elementLocated(By.css(".visible.confirmDialog")),
                    explicitWait, "Confirm dialog was not displayed");

                await confirmDialog.findElement(By.id("refuse")).click();

                const result = await Misc.execCmd("select version();", 10000);

                expect(result[0]).to.include("OK");

                await driver.switchTo().defaultContent();

                expect(await Misc.existsTreeElement(ociTreeSection,
                    "Bastion4PrivateSubnetStandardVnc"))
                    .to.be.true;

                expect(await Misc.existsTreeElement(dbTreeSection, "MDSforVSCodeExtension"))
                    .to.be.true;
            } finally {
                await driver.switchTo().defaultContent();
                await Misc.toggleSection(dbTreeSection, true);
                await Misc.reloadSection(dbTreeSection);
                await Misc.toggleSection(dbTreeSection, false);
            }
        });

        it("Get Bastion Information and set it as current", async () => {

            await Misc.selectContextMenuItem(ociTreeSection,
                "Bastion4PrivateSubnetStandardVnc", "Get Bastion Information");

            await driver.wait(async () => {
                const editors = await new EditorView().getOpenEditorTitles();

                return editors.includes("Bastion4PrivateSubnetStandardVnc Info.json");
            }, explicitWait, "Bastion4PrivateSubnetStandardVnc Info.json was not opened");

            const textEditor = new TextEditor();
            await driver.wait(async () => {
                return (await textEditor.getText()).indexOf("{") !== -1;
            }, explicitWait, "No text was found inside Bastion4PrivateSubnetStandardVnc Info.json");

            const json = await textEditor.getText();
            expect(Misc.isJson(json)).to.equal(true);

            const parsed = JSON.parse(json);
            const bastionId = parsed.id;

            await Misc.selectContextMenuItem(ociTreeSection,
                "Bastion4PrivateSubnetStandardVnc", "Set as Current Bastion");

            await driver.wait(async () => {
                return !(await Misc.hasLoadingBar(ociTreeSection));
            }, ociExplicitWait, "There is still a loading bar on OCI");

            expect(await Misc.isDefaultItem(ociTreeSection,
                "bastion", "Bastion4PrivateSubnetStandardVnc")).to.be.true;

            await Misc.toggleSection(consolesTreeSection, true);

            const btn = await Misc.getSectionToolbarButton(consolesTreeSection, "Add a New MySQL Shell Console");
            await btn.click();

            await Misc.switchToWebView();

            await driver.wait(until.elementLocated(By.id("shellEditorHost")), 20000, "Console was not loaded");

            const result = await Misc.execCmd("mds.get.currentBastionId()", 60000);

            expect(result[0]).to.equal(bastionId);

        });

        it("Refresh When Bastion Reaches Active State", async () => {

            await Misc.selectContextMenuItem(ociTreeSection,
                "Bastion4PrivateSubnetStandardVnc", "Refresh When Bastion Reaches Active State");

            await Misc.toggleSection(tasksTreeSection, true);

            expect(await Misc.existsTreeElement(
                tasksTreeSection, "Refresh Bastion (running)")).to.be.true;

            const bottomBar = new BottomBarPanel();
            const outputView = await bottomBar.openOutputView();

            await Misc.waitForOutputText(outputView, "Task 'Refresh Bastion' completed successfully", 20000);

            await outputView.clearText();

            expect(await Misc.existsTreeElement(
                tasksTreeSection, "Refresh Bastion (done)")).to.be.true;

        });

        it("Delete Bastion", async () => {

            const bottomBar = new BottomBarPanel();
            const outputView = await bottomBar.openOutputView();
            await outputView.clearText();

            await Misc.selectContextMenuItem(ociTreeSection,
                "Bastion4PrivateSubnetStandardVnc", "Delete Bastion");

            await Misc.toggleSection(tasksTreeSection, true);

            expect(await Misc.existsTreeElement(tasksTreeSection, "Delete Bastion (running)")).to.be.true;

            await Misc.waitForOutputText(outputView, "OCI profile 'E2ETESTS' loaded.", ociTasksExplicitWait);

            await Misc.verifyNotification("Are you sure you want to delete");

            const workbench = new Workbench();
            const ntfs = await workbench.getNotifications();

            await ntfs[ntfs.length - 1].takeAction("NO");

            expect(await Misc.existsTreeElement(tasksTreeSection, "Delete Bastion (error)")).to.be.true;

            await Misc.waitForOutputText(outputView, "Deletion aborted", explicitWait);

            await outputView.clearText();

        });

    });

});
