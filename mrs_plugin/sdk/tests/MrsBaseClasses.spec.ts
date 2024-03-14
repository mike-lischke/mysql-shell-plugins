/*
 * Copyright (c) 2023, 2024, Oracle and/or its affiliates.
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

import { beforeEach, describe, expect, it, vi } from "vitest";
import {
    IFindManyOptions, IFindUniqueOptions, MrsResourceCollectionObject, JsonObject, JsonValue, MrsBaseObjectDelete,
    MrsBaseObjectQuery, MrsBaseObjectUpdate, MrsBaseSchema, MrsBaseService, MrsResourceObject, MrsBaseObjectCreate,
} from "../MrsBaseClasses";

// fixtures
interface ITableMetadata1 {
    id?: number,
    str?: string,
    num?: number,
    bool?: boolean,
    json?: JsonValue,
    oneToMany?: ITableMetadata2[];
}

interface ITableMetadata2 {
    id?: number,
    str?: string,
    oneToOne?: ITableMetadata3;
}

interface ITableMetadata3 {
    id?: number,
    str?: string;
}

const service: MrsBaseService = new MrsBaseService("/foo");
const schema: MrsBaseSchema = { requestPath: "/bar", service };

const createFetchMock = (response: JsonObject = {}) => {
    vi.stubGlobal("fetch", vi.fn(() => {
        return Promise.resolve({
            ok: true,
            json: () => {
                return response;
            },
        });
    }));
};

describe("MRS SDK API", () => {
    beforeEach(() => {
        vi.restoreAllMocks();
        createFetchMock();
    });

    describe("when retrieving resources", () => {
        it("selects fields to include in the result set using the field names", async () => {
            const options: IFindManyOptions<ITableMetadata1, unknown, unknown> = {
                select: ["str", "json", "oneToMany.oneToOne.str"],
            };

            const query = new MrsBaseObjectQuery<ITableMetadata1, unknown>(schema, "/baz", options.select);
            await query.fetch();

            expect(fetch).toHaveBeenCalledWith("/foo/bar/baz?f=str,json,oneToMany.oneToOne.str",
                expect.anything());
        });

        it("selects fields to include in the result set using a field mapper", async () => {
            const options: IFindManyOptions<ITableMetadata1, unknown, unknown> = {
                select: {
                    str: true,
                    json: true,
                    oneToMany: {
                        oneToOne: {
                            str: true,
                        },
                    },
                },
            };

            const query = new MrsBaseObjectQuery<ITableMetadata1, unknown>(schema, "/baz", options.select);
            await query.fetch();

            expect(fetch).toHaveBeenCalledWith("/foo/bar/baz?f=str,json,oneToMany.oneToOne.str",
                expect.anything());
        });

        it("selects fields to exclude from the result set using a field mapper", async () => {
            const options: IFindManyOptions<ITableMetadata1, unknown, unknown> = {
                select: {
                    id: false,
                    json: false,
                    oneToMany: {
                        id: false,
                        oneToOne: {
                            id: false,
                        },
                    },
                },
            };

            const query = new MrsBaseObjectQuery<ITableMetadata1, unknown>(schema, "/baz", options.select);
            await query.fetch();

            expect(fetch).toHaveBeenCalledWith("/foo/bar/baz?f=!id,!json,!oneToMany.id,!oneToMany.oneToOne.id",
                expect.anything());
        });

        it("sets the order of the records in the result set based on a given field using a literal order keyword",
                async () => {
            const query = new MrsBaseObjectQuery<ITableMetadata1, unknown>(schema, "/baz");
            await query.orderBy({ num: "DESC" }).fetch();

            expect(fetch).toHaveBeenCalledWith('/foo/bar/baz?q={"$orderby":{"num":"DESC"}}',
                expect.anything());
        });

        it("sets the order of the records in the result set based on a given field using a numeric order identifier",
                async () => {
            const query = new MrsBaseObjectQuery<ITableMetadata1, unknown>(schema, "/baz");
            await query.orderBy({ num: -1 }).fetch();

            expect(fetch).toHaveBeenCalledWith('/foo/bar/baz?q={"$orderby":{"num":-1}}',
                expect.anything());
        });

        it("returns the first page of records that match a given implicit filter", async () => {
            const options: IFindManyOptions<unknown, ITableMetadata1, unknown> = {
                where: {
                    id: 1,
                },
            };

            const query = new MrsBaseObjectQuery<ITableMetadata1, unknown>(schema, "/baz");
            await query.where(options.where).fetch();

            expect(fetch).toHaveBeenCalledWith('/foo/bar/baz?q={"id":1}', expect.anything());
        });

        it("returns the first page of records that match a given explicit filter", async () => {
            const options: IFindManyOptions<unknown, ITableMetadata1, unknown> = {
                where: {
                    str: {
                        $like: "%foo%",
                    },
                },
            };

            const query = new MrsBaseObjectQuery<ITableMetadata1, unknown>(schema, "/baz");
            await query.where(options.where).fetch();

            expect(fetch).toHaveBeenCalledWith('/foo/bar/baz?q={"str":{"$like":"%foo%"}}', expect.anything());
        });

        it("returns a limited number of records from the first page", async () => {
            const options: IFindManyOptions<unknown, ITableMetadata1, unknown> = {
                take: 2,
            };

            const query = new MrsBaseObjectQuery<ITableMetadata1, unknown>(schema, "/baz");
            await query.limit(options.take).fetch();

            expect(fetch).toHaveBeenCalledWith("/foo/bar/baz?limit=2", expect.anything());
        });

        it("returns a limited number of records from the first page that match a given filter", async () => {
            const options: IFindManyOptions<unknown, ITableMetadata1, unknown> = {
                take: 2,
                where: {
                    id: {
                        $gt: 10,
                    },
                },
            };

            const query = new MrsBaseObjectQuery<ITableMetadata1, unknown>(schema, "/baz");
            await query.where(options.where).limit(options.take).fetch();

            expect(fetch).toHaveBeenCalledWith('/foo/bar/baz?q={"id":{"$gt":10}}&limit=2', expect.anything());
        });

        it("skips a number of records from the first page", async () => {
            const options: IFindManyOptions<unknown, ITableMetadata1, unknown> = {
                skip: 2,
            };

            const query = new MrsBaseObjectQuery<ITableMetadata1, unknown>(schema, "/baz");
            await query.offset(options.skip).fetch();

            expect(fetch).toHaveBeenCalledWith("/foo/bar/baz?offset=2", expect.anything());
        });

        it("skips a number of records that match a given filter", async () => {
            const options: IFindManyOptions<unknown, ITableMetadata1, unknown> = {
                skip: 2,
                where: {
                    bool: true,
                },
            };

            const query = new MrsBaseObjectQuery<ITableMetadata1, unknown>(schema, "/baz");
            await query.where(options.where).offset(options.skip).fetch();

            expect(fetch).toHaveBeenCalledWith('/foo/bar/baz?q={"bool":true}&offset=2', expect.anything());
        });

        it("returns the record that matches the given identifier or primary key", async () => {
            const options: IFindUniqueOptions<unknown, ITableMetadata1> = {
                where: {
                    id: 2,
                },
            };

            const query = new MrsBaseObjectQuery<ITableMetadata1, unknown>(schema, "/baz");
            await query.where(options.where).fetch();

            expect(fetch).toHaveBeenCalledWith('/foo/bar/baz?q={"id":2}', expect.anything());
        });

        it("returns all records where a given field is NULL", async () => {
            const options: IFindManyOptions<unknown, { maybe: number | null }, unknown> = {
                where: {
                    maybe: null,
                },
            };

            const query = new MrsBaseObjectQuery<ITableMetadata1, unknown>(schema, "/baz");
            await query.where(options.where).fetch();

            expect(fetch).toHaveBeenCalledWith('/foo/bar/baz?q={"maybe":{"$null":"null"}}', expect.anything());
        });

        it("returns all records where a given field is not NULL", async () => {
            const options: IFindManyOptions<unknown, { maybe: number | null }, unknown> = {
                where: {
                    maybe: {
                        not: null,
                    },
                },
            };

            const query = new MrsBaseObjectQuery<ITableMetadata1, unknown>(schema, "/baz");
            await query.where(options.where).fetch();

            expect(fetch).toHaveBeenCalledWith('/foo/bar/baz?q={"maybe":{"$notnull":"null"}}', expect.anything());
        });

        it(`returns all records where a field called "not" is NULL`, async () => {
            const options: IFindManyOptions<unknown, { not: number | null }, unknown> = {
                where: {
                    not: null,
                },
            };

            const query = new MrsBaseObjectQuery<ITableMetadata1, unknown>(schema, "/baz");
            await query.where(options.where).fetch();

            expect(fetch).toHaveBeenCalledWith('/foo/bar/baz?q={"not":{"$null":"null"}}', expect.anything());
        });

        it(`returns all records where a field called "not" is not NULL`, async () => {
            const options: IFindManyOptions<unknown, { not: number | null }, unknown> = {
                where: {
                    not: {
                        not: null,
                    },
                },
            };

            const query = new MrsBaseObjectQuery<ITableMetadata1, unknown>(schema, "/baz");
            await query.where(options.where).fetch();

            expect(fetch).toHaveBeenCalledWith('/foo/bar/baz?q={"not":{"$notnull":"null"}}', expect.anything());
        });

        it("embeds unions when the filter does not contain any", async () => {
            const firstUnionItem: ITableMetadata1 = { str: "foo" };
            const secondUnionItem: ITableMetadata1 = { num: 42 };

            const query = new MrsBaseObjectQuery<unknown, ITableMetadata1>(schema, "/baz");

            await query.where(firstUnionItem).or(secondUnionItem).fetch();
            expect(fetch).toHaveBeenCalledWith('/foo/bar/baz?q={"$or":[{"str":"foo"},{"num":42}]}', expect.anything());
        });

        it("aggregates unions when the filter already contains other unions", async () => {
            const firstUnionItem: ITableMetadata1 = { str: "foo" };
            const secondUnionItem: ITableMetadata1 = { num: 42 };

            const query = new MrsBaseObjectQuery<unknown, ITableMetadata1>(schema, "/baz");

            await query.where({ $or: [firstUnionItem] }).or(secondUnionItem).fetch();
            expect(fetch).toHaveBeenCalledWith('/foo/bar/baz?q={"$or":[{"str":"foo"},{"num":42}]}', expect.anything());
        });

        it("aggregates unions when the filter contains explicit intersections", async () => {
            const firstUnionItem: ITableMetadata1 = { str: "foo" };
            const secondUnionItem: ITableMetadata1 = { num: 42 };

            const query = new MrsBaseObjectQuery<unknown, ITableMetadata1>(schema, "/baz");

            await query.where({ $and: [firstUnionItem, secondUnionItem] }).or({ bool: false }).fetch();
            expect(fetch).toHaveBeenCalledWith(
                '/foo/bar/baz?q={"$or":[{"$and":[{"str":"foo"},{"num":42}]},{"bool":false}]}', expect.anything());
        });

        it("aggregates unions when the filter contains implicit intersections", async () => {
            const firstUnionItem: ITableMetadata1 = { str: "foo" };
            const secondUnionItem: ITableMetadata1 = { num: 42 };

            const query = new MrsBaseObjectQuery<unknown, ITableMetadata1>(schema, "/baz");

            await query.where({ ...firstUnionItem, ...secondUnionItem }).or({ bool: false }).fetch();
            // the router does not work with something like {"$or":[{"str":"foo","num":42},{"bool":false}]}
            expect(fetch).toHaveBeenCalledWith(
                '/foo/bar/baz?q={"$or":[{"$and":[{"str":"foo"},{"num":42}]},{"bool":false}]}', expect.anything());
        });

        beforeEach(() => {
            const collectionResponse: MrsResourceCollectionObject<ITableMetadata1> = {
                count: 2,
                hasMore: false,
                limit: 25,
                offset: 0,
                items: [{
                    id: 1,
                    str: "qux",
                    _metadata: {
                        etag: "XYZ",
                    },
                    links: [{
                        href: "http://localhost:8444/foo/bar/baz/1",
                        rel: "self",
                    }],
                }, {
                    id: 2,
                    str: "quux",
                    _metadata: {
                        etag: "ZYX",
                    },
                    links: [{
                        href: "http://localhost:8444/foo/bar/baz/2",
                        rel: "self",
                    }],
                }],
                links: [{
                    rel: "self",
                    href: "foo/bar/baz/",
                }, {
                    rel: "next",
                    href: "foo/bar/baz/?offset=25",
                }],
            };

            createFetchMock(collectionResponse as JsonObject);
        });

        it("hypermedia options are not part of the JSON representation of an application resource instance",
                async () => {
            const query = new MrsBaseObjectQuery<ITableMetadata1, unknown>(schema, "/baz");
            const collection = await query.fetch();

            expect(JSON.stringify(collection)).toEqual('[{"id":1,"str":"qux"},{"id":2,"str":"quux"}]');

            const resource = await query.fetchOne();

            expect(JSON.stringify(resource)).toEqual('{"id":1,"str":"qux"}');
        });

        it("hypermedia options are not enumerable in an application resource instance", async () => {
            const query = new MrsBaseObjectQuery<ITableMetadata1, unknown>(schema, "/baz");
            const collection = await query.fetch();

            expect(Object.keys(collection)).toEqual([]);

            const resource = await query.fetchOne() || {};

            expect(Object.keys(resource)).toEqual(["id", "str"]);
        });

        it("hypermedia options are not iterable in an application resource instance", async () => {
            const query = new MrsBaseObjectQuery<ITableMetadata1, unknown>(schema, "/baz");
            const collection = await query.fetch();

            expect("count" in collection).toBeFalsy();
            expect("hasMore" in collection).toBeFalsy();
            expect("items" in collection).toBeFalsy();
            expect("limit" in collection).toBeFalsy();
            expect("links" in collection).toBeFalsy();
            expect("offset" in collection).toBeFalsy();

            const resource = await query.fetchOne() as MrsResourceObject<ITableMetadata1>;

            expect("_metadata" in resource).toBeFalsy();
            expect("links" in resource).toBeFalsy();
        });

        it("hypermedia options are not writable in an application resource instance", async () => {
            const query = new MrsBaseObjectQuery<ITableMetadata1, unknown>(schema, "/baz");
            const collection = await query.fetch();

            expect(() => { collection.count = 0; }).toThrowError('The "count" property cannot be changed.');
            expect(() => { collection.hasMore = true; }).toThrowError('The "hasMore" property cannot be changed.');
            expect(() => { collection.limit = 0; }).toThrowError('The "limit" property cannot be changed.');
            expect(() => { collection.offset = 1; }).toThrowError('The "offset" property cannot be changed.');
            expect(() => { collection.links = []; }).toThrowError('The "links" property cannot be changed.');

            const resource = await query.fetchOne() as MrsResourceObject<ITableMetadata1>;
            // eslint-disable-next-line no-underscore-dangle
            expect(() => { resource._metadata = { etag: "AAA" }; })
                .toThrowError('The "_metadata" property cannot be changed');
            expect(() => { resource.links = []; }).toThrowError('The "links" property cannot be changed');
        });

        it("hypermedia options are not removable from an application resource instance", async () => {
            const query = new MrsBaseObjectQuery<ITableMetadata1, unknown>(schema, "/baz");
            const collection = await query.fetch() as Omit<MrsResourceCollectionObject<ITableMetadata1>,
                "count" | "hasMore" | "limit" | "offset" | "links">;

            expect(() => { delete collection.count; }).toThrowError('The "count" property cannot be deleted.');
            expect(() => { delete collection.hasMore; }).toThrowError('The "hasMore" property cannot be deleted.');
            expect(() => { delete collection.limit; }).toThrowError('The "limit" property cannot be deleted.');
            expect(() => { delete collection.offset; }).toThrowError('The "offset" property cannot be deleted.');
            expect(() => { delete collection.links; }).toThrowError('The "links" property cannot be deleted.');

            const resource = await query.fetchOne() as Omit<MrsResourceObject<ITableMetadata1>, "_metadata" | "links">;
            // eslint-disable-next-line no-underscore-dangle
            expect(() => { delete resource._metadata; }).toThrowError('The "_metadata" property cannot be deleted');
            expect(() => { delete resource.links; }).toThrowError('The "links" property cannot be deleted');
        });

        it("hypermedia and database object fields are directly accessible in an application resource instance",
                async () => {
            const query = new MrsBaseObjectQuery<ITableMetadata1, unknown>(schema, "/baz");
            const collection = await query.fetch();

            expect(collection.items).toHaveLength(2);
            expect(collection.items[0].id).toEqual(1);
            expect(collection.items[0].str).toEqual("qux");
            expect(collection.items[1].id).toEqual(2);
            expect(collection.items[1].str).toEqual("quux");
            expect(collection.count).toBeDefined();
            expect(collection.hasMore).toBeDefined();
            expect(collection.limit).toBeDefined();
            expect(collection.links).toBeDefined();

            const resource = await query.fetchOne() as MrsResourceObject<ITableMetadata1>;

            expect(resource.id).toEqual(1);
            expect(resource.str).toEqual("qux");
            // eslint-disable-next-line no-underscore-dangle
            expect(resource._metadata).toBeDefined();
            expect(resource.links).toBeDefined();
        });

        it("creates a query filter with a cursor", async () => {
            type Filterable = Pick<ITableMetadata1, "str">;
            type Iterable = Pick<ITableMetadata1, "id">;
            const query = new MrsBaseObjectQuery<ITableMetadata1, Filterable, Iterable>(
                    schema, "/baz", undefined, undefined, { id: 10 });

            await query.fetch();

            expect(fetch).toHaveBeenCalledWith(
                '/foo/bar/baz?q={"id":{"$gt":10},"$orderby":{"id":"ASC"}}', expect.anything());
        });

        it("includes a cursor in an existing query filter", async () => {
            type Filterable = Pick<ITableMetadata1, "str">;
            type Iterable = Pick<ITableMetadata1, "id">;
            const query = new MrsBaseObjectQuery<ITableMetadata1, Filterable, Iterable>(
                    schema, "/baz", undefined, undefined, { id: 10 });

            await query.where({ str: "foo" }).fetch();

            expect(fetch).toHaveBeenCalledWith(
                '/foo/bar/baz?q={"id":{"$gt":10},"str":"foo","$orderby":{"id":"ASC"}}', expect.anything());
        });

        it("ignores existing implicit filters using the same cursor field", async () => {
            type Filterable = Pick<ITableMetadata1, "id" | "str">;
            type Iterable = Pick<ITableMetadata1, "id">;
            const query = new MrsBaseObjectQuery<ITableMetadata1, Filterable, Iterable>(
                    schema, "/baz", undefined, undefined, { id: 10 });

            await query.where({ id: 5 }).fetch();

            expect(fetch).toHaveBeenCalledWith(
                '/foo/bar/baz?q={"id":{"$gt":10},"$orderby":{"id":"ASC"}}', expect.anything());
        });

        it("ignores existing explicit filters using the same cursor field", async () => {
            type Filterable = Pick<ITableMetadata1, "id" | "str">;
            type Iterable = Pick<ITableMetadata1, "id">;
            const query = new MrsBaseObjectQuery<ITableMetadata1, Filterable, Iterable>(
                    schema, "/baz", undefined, undefined, { id: 10 });

            await query.where({ id: { $gt: 5 }}).fetch();

            expect(fetch).toHaveBeenNthCalledWith(1,
                '/foo/bar/baz?q={"id":{"$gt":10},"$orderby":{"id":"ASC"}}', expect.anything());
        });

        it("ensures the cursor field becomes a required filter condition", async () => {
            type Filterable = Pick<ITableMetadata1, "id" | "str">;
            type Iterable = Pick<ITableMetadata1, "id">;
            const query = new MrsBaseObjectQuery<ITableMetadata1, Filterable, Iterable>(
                    schema, "/baz", undefined, undefined, { id: 10 });

            await query.or({ id: 1, str: "foo" }).fetch();

            expect(fetch).toHaveBeenNthCalledWith(1,
                '/foo/bar/baz?q={"$and":[{"id":{"$gt":10}},{"str":"foo"}],"$orderby":{"id":"ASC"}}', expect.anything());
        });

        it("accounts for the order of a cursor field", async () => {
            type Filterable = Pick<ITableMetadata1, "str">;
            type Iterable = Pick<ITableMetadata1, "id">;
            const query = new MrsBaseObjectQuery<ITableMetadata1, Filterable, Iterable>(
                    schema, "/baz", undefined, undefined, { id: 10 });

            await query.orderBy({ str: "DESC" }).fetch();

            expect(fetch).toHaveBeenCalledWith('/foo/bar/baz?q={"id":{"$gt":10},"$orderby":{"id":"ASC","str":"DESC"}}',
                expect.anything());
        });

        it("ignores the offset when a cursor is provided", async () => {
            type Iterable = Pick<ITableMetadata1, "id">;
            const query = new MrsBaseObjectQuery<ITableMetadata1, unknown, Iterable>(
                schema, "/baz", undefined, undefined, { id: 10 });

            await query.offset(20).fetch();

            expect(fetch).toHaveBeenCalledWith('/foo/bar/baz?q={"id":{"$gt":10},"$orderby":{"id":"ASC"}}',
                expect.anything());
        });

        it("overrides the sort order of the cursor field", async () => {
            type Iterable = Pick<ITableMetadata1, "id">;
            type Filterable = Pick<ITableMetadata1, "id" | "str">;
            const query = new MrsBaseObjectQuery<ITableMetadata1, Filterable, Iterable>(
                schema, "/baz", undefined, undefined, { id: 10 });

            await query.orderBy({ id: "DESC" }).fetch();

            expect(fetch).toHaveBeenCalledWith('/foo/bar/baz?q={"id":{"$gt":10},"$orderby":{"id":"ASC"}}',
                expect.anything());
        });

        it("supports multiple cursors", async () => {
            type Iterable = Pick<ITableMetadata1, "id" | "num">;
            const query = new MrsBaseObjectQuery<ITableMetadata1, unknown, Iterable>(
                schema, "/baz", undefined, undefined, { id: 10, num: 20 });

            await query.fetch();

            expect(fetch).toHaveBeenCalledWith(
                '/foo/bar/baz?q={"id":{"$gt":10},"num":{"$gt":20},"$orderby":{"id":"ASC","num":"ASC"}}',
                expect.anything());
        });

        it("ignores undefined cursors", async () => {
            type Iterable = Pick<ITableMetadata1, "id">;
            const query = new MrsBaseObjectQuery<ITableMetadata1, unknown, Iterable>(
                schema, "/baz", undefined, undefined, { id: undefined });

            await query.fetch();

            expect(fetch).toHaveBeenCalledWith("/foo/bar/baz", expect.anything());
        });

        it("ignores the sort order for undefined cursors", async () => {
            type Filterable = Pick<ITableMetadata1, "id">;
            type Iterable = Pick<ITableMetadata1, "id">;
            const query = new MrsBaseObjectQuery<ITableMetadata1, Filterable, Iterable>(
                schema, "/baz", undefined, undefined, { id: undefined });

            await query.orderBy({ id: "DESC" }).fetch();

            expect(fetch).toHaveBeenCalledWith("/foo/bar/baz", expect.anything());
        });
    });

    describe("when creating a resource", () => {
        beforeEach(() => {
            const singleResourceResponse: MrsResourceObject<ITableMetadata1> = {
                id: 1,
                str: "qux",
                _metadata: {
                    etag: "XYZ",
                },
                links: [{
                    href: "http://localhost:8444/foo/bar/baz/1",
                    rel: "self",
                }],
            };

            createFetchMock(singleResourceResponse as JsonObject);
        });

        it("encodes the resource as a JSON string in the request body", async () => {
            const data = { id: 1, str: "qux" };
            const query = new MrsBaseObjectCreate<ITableMetadata1>(schema, "/baz", data);
            await query.fetch();

            expect(fetch).toHaveBeenCalledWith("/foo/bar/baz", expect.objectContaining({
                method: "POST",
                body: JSON.stringify(data),
            }));
        });

        it("hypermedia properties are not part of the JSON representation of an application resource instance",
                async () => {
            const query = new MrsBaseObjectCreate<ITableMetadata1>(schema, "/baz", { id: 1, str: "qux" });
            const res = await query.fetch();

            expect(JSON.stringify(res)).toEqual('{"id":1,"str":"qux"}');
        });

        it("hypermedia properties are not enumerable in an application resource instance", async () => {
            const query = new MrsBaseObjectCreate<ITableMetadata1>(schema, "/baz", { id: 1, str: "qux" });
            const res = await query.fetch();

            expect(Object.keys(res)).toEqual(["id", "str"]);
        });

        it("hypermedia properties are not iterable in an application resource instance", async () => {
            const query = new MrsBaseObjectCreate<ITableMetadata1>(schema, "/baz", { id: 1, str: "qux" });
            const res = await query.fetch();

            expect("_metadata" in res).toBeFalsy();
            expect("links" in res).toBeFalsy();
        });

        it("hypermedia properties are not writable in an application resource instance", async () => {
            const query = new MrsBaseObjectCreate<ITableMetadata1>(schema, "/baz", { id: 1, str: "qux" });
            const res = await query.fetch();

            // eslint-disable-next-line no-underscore-dangle
            expect(() => { res._metadata = { etag: "ZYX" }; })
                .toThrowError('The "_metadata" property cannot be changed.');
            expect(() => { res.links = []; }).toThrowError('The "links" property cannot be changed.');
        });

        it("hypermedia properties are not removable from an application resource instance", async () => {
            const query = new MrsBaseObjectCreate<ITableMetadata1>(schema, "/baz", { id: 1, str: "qux" });
            const res = await query.fetch() as Omit<MrsResourceObject<ITableMetadata1>, "_metadata" | "links">;

            // eslint-disable-next-line no-underscore-dangle
            expect(() => { delete res._metadata; }).toThrowError('The "_metadata" property cannot be deleted.');
            expect(() => { delete res.links; }).toThrowError('The "links" property cannot be deleted.');
        });

        it("hypermedia and database object fields are directly accessible in an application resource instance",
                async () => {
            const query = new MrsBaseObjectCreate<ITableMetadata1>(schema, "/baz", { id: 1, str: "qux" });
            const res = await query.fetch();

            expect(res.id).toEqual(1);
            expect(res.str).toEqual("qux");
            // eslint-disable-next-line no-underscore-dangle
            expect(res._metadata).toBeDefined();
            expect(res.links).toBeDefined();
        });
    });

    describe("when updating a resource", () => {
        beforeEach(() => {
            const singleResourceResponse: MrsResourceObject<ITableMetadata1> = {
                id: 1,
                str: "qux",
                _metadata: {
                    etag: "XYZ",
                },
                links: [{
                    href: "http://localhost:8444/foo/bar/baz/1",
                    rel: "self",
                }],
            };

            createFetchMock(singleResourceResponse as JsonObject);
        });

        it("hypermedia properties are not part of the JSON representation of an application resource instance",
                async () => {
            const query = new MrsBaseObjectUpdate<ITableMetadata1>(schema, "/baz", { id: 1, str: "qux" }, ["id"]);
            const res = await query.fetch();

            expect(JSON.stringify(res)).toEqual('{"id":1,"str":"qux"}');
        });

        it("hypermedia properties are not enumerable in an application resource instance", async () => {
            const query = new MrsBaseObjectUpdate<ITableMetadata1>(schema, "/baz", { id: 1, str: "qux" }, ["id"]);
            const res = await query.fetch();

            expect(Object.keys(res)).toEqual(["id", "str"]);
        });

        it("hypermedia properties are not iterable in an application resource instance", async () => {
            const query = new MrsBaseObjectUpdate<ITableMetadata1>(schema, "/baz", { id: 1, str: "qux" }, ["id"]);
            const res = await query.fetch();

            expect("_metadata" in res).toBeFalsy();
            expect("links" in res).toBeFalsy();
        });

        it("hypermedia properties are not writable in an application resource instance", async () => {
            const query = new MrsBaseObjectUpdate<ITableMetadata1>(schema, "/baz", { id: 1, str: "qux" }, ["id"]);
            const res = await query.fetch();

            // eslint-disable-next-line no-underscore-dangle
            expect(() => { res._metadata = { etag: "ZYX" }; })
                .toThrowError('The "_metadata" property cannot be changed.');
            expect(() => { res.links = []; }).toThrowError('The "links" property cannot be changed.');
        });

        it("hypermedia properties are not removable from an application resource instance", async () => {
            const query = new MrsBaseObjectUpdate<ITableMetadata1>(schema, "/baz", { id: 1, str: "qux" }, ["id"]);
            const res = await query.fetch() as Omit<MrsResourceObject<ITableMetadata1>, "_metadata" | "links">;

            // eslint-disable-next-line no-underscore-dangle
            expect(() => { delete res._metadata; }).toThrowError('The "_metadata" property cannot be deleted.');
            expect(() => { delete res.links; }).toThrowError('The "links" property cannot be deleted.');
        });

        it("hypermedia and database object fields are directly accessible in an application resource instance",
                async () => {
            const query = new MrsBaseObjectUpdate<ITableMetadata1>(schema, "/baz", { id: 1, str: "qux" }, ["id"]);
            const res = await query.fetch();

            expect(res.id).toEqual(1);
            expect(res.str).toEqual("qux");
            // eslint-disable-next-line no-underscore-dangle
            expect(res._metadata).toBeDefined();
            expect(res.links).toBeDefined();
        });
    });

    describe("when deleting resources", () => {
        it("removes all records where a given field is NULL", async () => {
            const options: IFindManyOptions<unknown, { maybe: number | null }, unknown> = {
                where: {
                    maybe: null,
                },
            };

            const query = new MrsBaseObjectDelete<{ maybe: number | null }>(schema, "/baz");
            await query.where(options.where).fetch();

            expect(fetch).toHaveBeenCalledWith('/foo/bar/baz?q={"maybe":{"$null":"null"}}', expect.objectContaining({
                method: "DELETE",
            }));
        });

        it("removes all records where a given field is not NULL", async () => {
            const options: IFindManyOptions<unknown, { maybe: number | null }, unknown> = {
                where: {
                    maybe: {
                        not: null,
                    },
                },
            };

            const query = new MrsBaseObjectDelete<{ maybe: number | null }>(schema, "/baz");
            await query.where(options.where).fetch();

            expect(fetch).toHaveBeenCalledWith('/foo/bar/baz?q={"maybe":{"$notnull":"null"}}', expect.objectContaining({
                method: "DELETE",
            }));
        });
    });
});
