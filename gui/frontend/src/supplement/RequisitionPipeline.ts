/*
 * Copyright (c) 2021, Oracle and/or its affiliates.
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

import { IRequestListEntry, IRequestTypeMap, RequisitionHub } from "./Requisitions";

// A class to manage a list of requests that must be executed in sequential order.
export class RequisitionPipeline {
    // A FIFO list with open requests.
    private pendingRequests: Array<IRequestListEntry<keyof IRequestTypeMap>> = [];

    // A timer to announce pending requests to the application in a regular interval.
    private announceTimer?: ReturnType<typeof setInterval>;

    // A timer to clean up requests that aren't handled in a certain amount of time.
    private watchDog?: ReturnType<typeof setTimeout>;

    private announcePromise?: Promise<boolean>;

    public constructor(private hub: RequisitionHub) {
        hub.register("job", this.addJob);
    }

    /**
     * Adds a job (consisting of a number of requests) to the internal list for execution.
     *
     * @param job The job to add to the pipeline.
     *
     * @returns A promise which is immediately resolved to true.
     */
    public addJob = (job: Array<IRequestListEntry<keyof IRequestTypeMap>>): Promise<boolean> => {
        this.pendingRequests.push(...job);

        if (!this.announceTimer) {
            this.announceTimer = setInterval(this.announceRequest, 100);
        }

        return Promise.resolve(true);
    };

    /**
     * Triggers the execution for the top request in the list, if there's one.
     */
    private announceRequest = (): void => {
        if (this.announcePromise) {
            // If there's currently a request running do nothing.
            return;
        }

        if (this.pendingRequests.length > 0) { // Sanity check. Should always be the case.
            const request = this.pendingRequests[0];
            this.announcePromise = this.hub.execute(request.requestType, request.parameter);
            this.announcePromise.then((value) => {
                if (value) {
                    // Done with this request.
                    this.removeTopRequest();
                } else {
                    this.announcePromise = undefined;
                }
            }).catch(() => {
                this.removeTopRequest();
            });

            this.watchDog = setTimeout(() => {
                this.removeTopRequest();
            }, 5000);
        }
    };

    /**
     * Removes the top entry in the pending list, if there's any, and stops the watchdog.
     */
    private removeTopRequest = (): void => {
        if (this.watchDog) {
            clearTimeout(this.watchDog);
            this.watchDog = undefined;
        }

        this.announcePromise = undefined;
        this.pendingRequests.shift();

        if (this.pendingRequests.length === 0 && this.announceTimer) {
            // Stop the announcement timer if no more requests are waiting.
            clearInterval(this.announceTimer);
            this.announceTimer = undefined;
        }
    };
}
