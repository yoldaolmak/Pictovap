/* Local-file-only image preview checks. No fetch, remote URL, or CMS operation. */
(function (root) {
    "use strict";

    var MAX_FILE_SIZE = 8 * 1024 * 1024;
    var MIME_BY_EXTENSION = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp"
    };

    function nonempty(value) {
        return typeof value === "string" && value.trim().length > 0;
    }

    function fileExtension(filename) {
        var match = filename.toLowerCase().match(/\.[a-z0-9]+$/);
        return match ? match[0] : "";
    }

    function expectedNames(asset) {
        var provenance = asset && asset.provenance;
        if (!provenance || typeof provenance !== "object") {
            return [];
        }
        return [provenance.original_filename, provenance.generated_filename].filter(
            function (name) {
                return nonempty(name) &&
                    !name.includes("/") && !name.includes("\\") &&
                    !!MIME_BY_EXTENSION[fileExtension(name)];
            }
        );
    }

    function detectMime(bytes) {
        if (bytes.length >= 3 &&
                bytes[0] === 0xff && bytes[1] === 0xd8 && bytes[2] === 0xff) {
            return "image/jpeg";
        }
        if (bytes.length >= 8 &&
                bytes[0] === 0x89 && bytes[1] === 0x50 &&
                bytes[2] === 0x4e && bytes[3] === 0x47 &&
                bytes[4] === 0x0d && bytes[5] === 0x0a &&
                bytes[6] === 0x1a && bytes[7] === 0x0a) {
            return "image/png";
        }
        if (bytes.length >= 6 &&
                bytes[0] === 0x47 && bytes[1] === 0x49 &&
                bytes[2] === 0x46 && bytes[3] === 0x38 &&
                (bytes[4] === 0x37 || bytes[4] === 0x39) &&
                bytes[5] === 0x61) {
            return "image/gif";
        }
        if (bytes.length >= 12 &&
                bytes[0] === 0x52 && bytes[1] === 0x49 &&
                bytes[2] === 0x46 && bytes[3] === 0x46 &&
                bytes[8] === 0x57 && bytes[9] === 0x45 &&
                bytes[10] === 0x42 && bytes[11] === 0x50) {
            return "image/webp";
        }
        return null;
    }

    function validateLocalImage(file, asset) {
        // Never accept a remote URL or contents derived from imported JSON as a File.
        if (!file || typeof file.name !== "string" ||
                typeof file.size !== "number" ||
                typeof file.slice !== "function") {
            return Promise.reject(new Error("Choose an image file from this device."));
        }
        if (file.size <= 0 || file.size > MAX_FILE_SIZE) {
            return Promise.reject(new Error("Local preview image must be 1 byte–8 MB."));
        }
        var names = expectedNames(asset);
        if (!names.length || names.indexOf(file.name) === -1) {
            return Promise.reject(new Error(
                "Local filename must exactly match the candidate's recorded original or generated filename."
            ));
        }
        var expectedMime = MIME_BY_EXTENSION[fileExtension(file.name)];
        if (file.type && file.type !== expectedMime) {
            return Promise.reject(new Error("Image MIME type does not match the filename."));
        }

        // Read only the first few bytes. The remaining image stays in the
        // browser's local File/Blob object, never in the exported review JSON.
        return Promise.resolve().then(function () {
            return file.slice(0, 32).arrayBuffer();
        }).then(function (header) {
            var mime = detectMime(new Uint8Array(header));
            if (mime !== expectedMime) {
                throw new Error("Image signature does not match the claimed file type.");
            }
            return {
                filename: file.name,
                mime: mime,
                size: file.size
            };
        });
    }

    var api = {
        validateLocalImage: validateLocalImage,
        expectedNames: expectedNames,
        detectMime: detectMime,
        MAX_FILE_SIZE: MAX_FILE_SIZE
    };
    if (typeof module === "object" && module.exports) {
        module.exports = api;
    }
    root.PictovapLocalPreview = api;
})(typeof window === "object" ? window : globalThis);
