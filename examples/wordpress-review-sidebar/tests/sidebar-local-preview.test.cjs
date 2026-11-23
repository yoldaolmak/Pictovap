"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const { webcrypto } = require("node:crypto");
const { Blob } = require("node:buffer");
const { TextDecoder } = require("node:util");

const model = require("../assets/review-model.js");
const localPreview = require("../assets/local-preview.js");

function inputFile(name, bytes, mime) {
    const file = new Blob([bytes], { type: mime });
    Object.defineProperty(file, "name", { value: name });
    return file;
}

function pack() {
    const proposed = {
        candidate_id: "photo-1",
        provenance: {
            image_id: "photo-1", slot_id: "featured",
            provider: "local", original_filename: "photo.jpg",
            generated_filename: "pictovap_photo.webp", license_status: "unknown",
            source_url: "https://example.invalid/source.jpg?signature=PRIVATE"
        },
        placement: {
            slot_id: "featured", candidate_id: "photo-1",
            output_path: "pictovap_photo.webp"
        }
    };
    const alternative = {
        candidate_id: "photo-2",
        provenance: {
            image_id: "photo-2", slot_id: "featured",
            provider: "local", original_filename: "other.png",
            generated_filename: "pictovap_other.webp", license_status: "unknown",
            source_url: "https://example.invalid/other.png?signature=PRIVATE"
        },
        placement: {
            slot_id: "featured", candidate_id: "photo-2",
            output_path: "pictovap_other.webp"
        }
    };
    return {
        schema_version: "1", kind: "pictovap.decision-pack",
        article: { id: "42", title: "Local image comparison" },
        slots: [{
            slot_id: "featured", purpose: "featured_image",
            candidates: [
                { slot_id: "featured", candidate_id: "photo-1", decision: "selected", final_score: 9 },
                { slot_id: "featured", candidate_id: "photo-2", decision: "needs_review", final_score: 8 }
            ],
            proposal: proposed, alternatives: [alternative]
        }],
        review: { status: "pending", decisions: [] },
        application: { status: "not_applied", receipts: [] }
    };
}

function fakeReact() {
    const hooks = [];
    let index = 0;
    function useState(initial) {
        const current = index++;
        if (!(current in hooks)) { hooks[current] = initial; }
        return [hooks[current], function (update) {
            hooks[current] = typeof update === "function" ? update(hooks[current]) : update;
        }];
    }
    function useRef(initial) {
        const current = index++;
        if (!(current in hooks)) { hooks[current] = { current: initial }; }
        return hooks[current];
    }
    function useEffect(run) {
        const current = index++;
        if (!(current in hooks)) {
            hooks[current] = { cleanup: run() };
        }
    }
    return {
        element: {
            createElement: (type, props, ...children) => ({ type, props: props || {}, children }),
            useState, useRef, useEffect
        },
        render: (component) => { index = 0; return component(); },
        unmount: () => hooks.forEach((item) => {
            if (item && typeof item.cleanup === "function") { item.cleanup(); }
        })
    };
}

function flatten(element) {
    if (Array.isArray(element)) { return element.flatMap(flatten); }
    if (!element || typeof element !== "object" || !("type" in element)) { return []; }
    return [element].concat(flatten(element.children));
}

async function eventually(read) {
    for (let n = 0; n < 80; n++) {
        const value = read();
        if (value) { return value; }
        await new Promise((done) => setTimeout(done, 5));
    }
    throw new Error("Editor state not ready");
}

function harness() {
    const react = fakeReact();
    let plugin = null;
    let created = 0;
    const revoked = [];
    let remoteRequests = 0;
    const wp = {
        element: react.element,
        plugins: { registerPlugin: (name, config) => {
            assert.equal(name, "pictovap-review-sidebar");
            plugin = config;
        } },
        editor: { PluginSidebar: function PluginSidebar() {} },
        components: {
            Button: function Button() {},
            Notice: function Notice() {}
        }
    };
    const window = {
        wp,
        PictovapReviewConfig: { postId: 42, actor: "editor" },
        PictovapReviewModel: model,
        PictovapLocalPreview: localPreview,
        crypto: webcrypto,
        URL: {
            createObjectURL: () => "blob:locally-selected-" + (++created),
            revokeObjectURL: (url) => { revoked.push(url); }
        },
        fetch: () => {
            remoteRequests++;
            throw new Error("Network access in editor preview");
        }
    };
    const code = fs.readFileSync(
        path.join(__dirname, "../assets/sidebar.js"), "utf-8"
    );
    vm.runInNewContext(code, {
        window, TextDecoder,
        document: {},
        console
    }, { filename: "sidebar.js" });
    assert.ok(plugin && typeof plugin.render === "function");
    function all() { return flatten(react.render(plugin.render)); }
    function importFile() {
        const control = all().find((node) =>
            node.type === "input" && node.props.id === "pictovap-decision-pack"
        );
        assert.ok(control);
        control.props.onChange({
            target: { files: [inputFile("pack.json", JSON.stringify(pack()), "application/json")] }
        });
    }
    return {
        all, importFile, unmount: react.unmount,
        getCreated: () => created,
        getRevoked: () => revoked,
        getRemoteRequests: () => remoteRequests
    };
}

test("Gutenberg preview renders only explicit local blob image and never provider URL", async () => {
    const ui = harness();
    ui.importFile();
    const localInputs = await eventually(() => {
        const list = ui.all().filter((node) =>
            node.type === "input" && node.props.accept === "image/jpeg,image/png,image/gif,image/webp"
        );
        return list.length === 2 ? list : null;
    });
    const jpeg = Uint8Array.from([0xff, 0xd8, 0xff, 0xe0, 0, 1]);
    localInputs[0].props.onChange({
        target: { files: [inputFile("photo.jpg", jpeg, "image/jpeg")] }
    });
    const image = await eventually(() =>
        ui.all().find((node) => node.type === "img")
    );
    assert.equal(image.props.src, "blob:locally-selected-1");
    assert.equal(ui.getRemoteRequests(), 0);
    assert.equal(ui.getCreated(), 1);
    assert.ok(ui.all().every((node) =>
        node.type !== "img" || node.props.src.startsWith("blob:")
    ));

    ui.importFile();
    assert.deepEqual(ui.getRevoked(), ["blob:locally-selected-1"]);
    assert.equal(ui.all().filter((node) => node.type === "img").length, 0);
    ui.unmount();
    assert.equal(ui.getRemoteRequests(), 0);
});

test("invalid image cannot render; removing and unmounting revoke all blob URLs", async () => {
    const ui = harness();
    ui.importFile();
    const localInputs = await eventually(() =>
        ui.all().filter((node) => node.type === "input" &&
            node.props.accept === "image/jpeg,image/png,image/gif,image/webp").length === 2
            ? ui.all().filter((node) => node.type === "input" &&
                node.props.accept === "image/jpeg,image/png,image/gif,image/webp") : null
    );
    localInputs[1].props.onChange({
        target: { files: [inputFile("other.png", [0x3c, 0x73, 0x76, 0x67], "image/png")] }
    });
    await eventually(() => ui.all().some((node) =>
        node.type === "div" && node.props.className === "pictovap-review"
    ));
    assert.equal(ui.getCreated(), 0);

    localInputs[1].props.onChange({
        target: {
            files: [inputFile("other.png",
                Uint8Array.from([0x89, 0x50, 0x4e, 0x47, 13, 10, 26, 10]), "image/png")]
        }
    });
    await eventually(() => ui.all().find((node) => node.type === "img"));
    const remove = ui.all().find((node) =>
        node.props && node.props.onClick &&
        node.children.includes("Remove local preview")
    );
    assert.ok(remove);
    remove.props.onClick();
    assert.deepEqual(ui.getRevoked(), ["blob:locally-selected-1"]);
    assert.equal(ui.all().filter((node) => node.type === "img").length, 0);

    const updated = ui.all().filter((node) =>
        node.type === "input" && node.props.accept === "image/jpeg,image/png,image/gif,image/webp"
    );
    updated[0].props.onChange({
        target: { files: [inputFile("photo.jpg", [0xff, 0xd8, 0xff], "image/jpeg")] }
    });
    await eventually(() => ui.all().find((node) => node.type === "img"));
    ui.unmount();
    assert.deepEqual(ui.getRevoked(),
        ["blob:locally-selected-1", "blob:locally-selected-2"]);
    assert.equal(ui.getRemoteRequests(), 0);
});
