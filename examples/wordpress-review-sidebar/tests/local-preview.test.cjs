"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const preview = require("../assets/local-preview.js");

const headers = {
    jpeg: [0xff, 0xd8, 0xff, 0xe0, 0x00, 0x10],
    png: [0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a],
    gif: [0x47, 0x49, 0x46, 0x38, 0x39, 0x61],
    webp: [0x52, 0x49, 0x46, 0x46, 0x00, 0x00, 0x00, 0x00,
        0x57, 0x45, 0x42, 0x50]
};

function asset(original = "source.jpg", generated = "processed.webp") {
    return {
        candidate_id: "img-1",
        provenance: {
            original_filename: original,
            generated_filename: generated,
            image_id: "img-1",
            source_url: "https://example.invalid/photo.jpg?token=sensitive"
        }
    };
}

function localFile(name, header, mime, overrideSize) {
    const data = Uint8Array.from(header);
    return {
        name,
        type: mime,
        size: overrideSize === undefined ? data.length : overrideSize,
        slice: (start, end) => ({
            arrayBuffer: async () => data.slice(start, end).buffer
        })
    };
}

test("accepts matching local JPEG original and WebP generated file", async () => {
    const a = asset();
    assert.deepEqual(preview.expectedNames(a), ["source.jpg", "processed.webp"]);
    assert.deepEqual(
        await preview.validateLocalImage(localFile("source.jpg", headers.jpeg, "image/jpeg"), a),
        { filename: "source.jpg", mime: "image/jpeg", size: 6 }
    );
    const result = await preview.validateLocalImage(
        localFile("processed.webp", headers.webp, "image/webp"), a
    );
    assert.equal(result.mime, "image/webp");
    assert.equal(result.filename, "processed.webp");
});

test("recognizes PNG and GIF signatures; empty browser MIME permitted with signature", async () => {
    const png = await preview.validateLocalImage(
        localFile("map.png", headers.png, ""), asset("map.png", "map.webp")
    );
    assert.equal(png.mime, "image/png");
    const gif = await preview.validateLocalImage(
        localFile("walk.gif", headers.gif, "image/gif"), asset("walk.gif", "walk.webp")
    );
    assert.equal(gif.mime, "image/gif");
});

test("rejects remote URLs, SVG, script, MIME spoofing and wrong file bindings", async () => {
    const a = asset();
    await assert.rejects(preview.validateLocalImage(a.provenance.source_url, a), /from this device/);
    await assert.rejects(
        preview.validateLocalImage(localFile("evil.svg", headers.png, "image/svg+xml"), a),
        /exactly match/
    );
    await assert.rejects(
        preview.validateLocalImage(localFile("source.jpg", headers.png, "image/jpeg"), a),
        /signature/
    );
    await assert.rejects(
        preview.validateLocalImage(localFile("source.jpg", headers.jpeg, "image/png"), a),
        /MIME/
    );
    await assert.rejects(
        preview.validateLocalImage(localFile("wrong.jpg", headers.jpeg, "image/jpeg"), a),
        /exactly match/
    );
    await assert.rejects(
        preview.validateLocalImage(localFile("source.jpg", [0x3c, 0x73, 0x76, 0x67], "image/jpeg"), a),
        /signature/
    );
});

test("no arbitrary path, oversized image, empty image or unsupported preview type", async () => {
    const a = asset("../secret.jpg", "safe.avif");
    assert.deepEqual(preview.expectedNames(a), []);
    await assert.rejects(
        preview.validateLocalImage(localFile("../secret.jpg", headers.jpeg, "image/jpeg"), a),
        /exactly match/
    );
    const safe = asset();
    await assert.rejects(
        preview.validateLocalImage(localFile("source.jpg", headers.jpeg, "image/jpeg", 0), safe),
        /1 byte/
    );
    await assert.rejects(
        preview.validateLocalImage(
            localFile("source.jpg", headers.jpeg, "image/jpeg", preview.MAX_FILE_SIZE + 1), safe
        ),
        /8 MB/
    );
});

test("rejects truncated or failed local reads instead of falling back to remote URLs", async () => {
    await assert.rejects(
        preview.validateLocalImage(localFile("source.jpg", [0xff, 0xd8], ""), asset()),
        /signature/
    );
    const bad = {
        name: "source.jpg",
        size: 80,
        type: "image/jpeg",
        slice: () => ({ arrayBuffer: () => Promise.reject(new Error("read failed")) })
    };
    await assert.rejects(preview.validateLocalImage(bad, asset()), /read failed/);
});
