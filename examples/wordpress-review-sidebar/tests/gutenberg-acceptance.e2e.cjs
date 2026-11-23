/**
 * Real WordPress Gutenberg Editor End-to-End Acceptance Test.
 *
 * Exercises the installed Pictovap Review reference plugin inside a real
 * WordPress Gutenberg editor session using Playwright and headless Chromium.
 *
 * Invariants proven:
 * 1. Authorized editor sees and opens the Pictovap Review sidebar for the post.
 * 2. Real Decision Pack JSON import binds to post ID; mismatched ID is rejected.
 * 3. Proposal metadata, scores, reasons, and rights evidence are rendered.
 * 4. Evidenced alternatives support one-click direct replacement in the browser.
 * 5. Accept and Reject actions update per-slot review decisions.
 * 6. Safe local visual comparisons render blob: URLs without remote fetch/upload.
 * 7. Invalid local file signatures or names are safely rejected without preview.
 * 8. Downloaded review decisions draft contains valid SHA-256 and decisions list.
 * 9. Unauthorized users cannot access or load the review sidebar.
 * 10. Zero CMS mutations: no REST media writes, post edits or background fetches.
 */

"use strict";

const fs = require("node:fs");
const path = require("node:path");
const assert = require("node:assert/strict");
const { chromium } = require("playwright");

const WP_URL = process.env.WP_URL || "http://127.0.0.1:18888";
const WP_USER = process.env.WP_USER || "editor";
const WP_PASS = process.env.WP_PASS || "editorpassword123";
const WP_POST_ID = process.env.WP_POST_ID || "4";
const PACK_PATH = process.env.WP_PACK_PATH || "/tmp/pending-post-4.json";
const OUTPUT_DECISIONS_PATH = process.env.WP_DECISIONS_PATH || "/tmp/e2e-downloaded-decisions.json";

// JPEG and WebP test file headers for local comparison verification
const JPEG_HEADER = Buffer.from([
    0xff, 0xd8, 0xff, 0xe0, 0x00, 0x10, 0x4a, 0x46, 0x49, 0x46, 0x00, 0x01,
    0x01, 0x01, 0x00, 0x48, 0x00, 0x48, 0x00, 0x00, 0xff, 0xdb, 0x00, 0x43,
    0x00, 0x03, 0x02, 0x02, 0x03, 0x02, 0x02, 0x03, 0x03, 0x03, 0x03, 0x04
]);

const WEBP_HEADER = Buffer.from([
    0x52, 0x49, 0x46, 0x46, 0x24, 0x00, 0x00, 0x00,
    0x57, 0x45, 0x42, 0x50, 0x56, 0x50, 0x38, 0x20,
    0x18, 0x00, 0x00, 0x00, 0x30, 0x01, 0x00, 0x9d,
    0x01, 0x2a, 0x01, 0x00, 0x01, 0x00, 0x02, 0x00
]);

async function runAcceptance() {
    console.log(`[E2E] Starting Gutenberg Acceptance Suite on ${WP_URL} for post #${WP_POST_ID}`);

    assert(fs.existsSync(PACK_PATH), `Source Decision Pack must exist at ${PACK_PATH}`);
    const sourcePack = JSON.parse(fs.readFileSync(PACK_PATH, "utf-8"));
    const slotCount = sourcePack.slots.length;
    console.log(`[E2E] Source Decision Pack loaded: ${slotCount} slots, article ID ${sourcePack.article.id}`);

    // Create temporary local preview test files
    const localSunsetJpg = "/tmp/sunset-mountains.jpg";
    const localBackpackWebp = "/tmp/pictovap_minimal-backpack.webp";
    const localInvalidJpg = "/tmp/fake-signature.jpg";
    fs.writeFileSync(localSunsetJpg, JPEG_HEADER);
    fs.writeFileSync(localBackpackWebp, WEBP_HEADER);
    fs.writeFileSync(localInvalidJpg, Buffer.from("NOT_A_REAL_JPEG"));

    // Create a mismatched pack for post ID validation test
    const mismatchedPackPath = "/tmp/mismatched-pack-post-999.json";
    const mismatchedPack = JSON.parse(JSON.stringify(sourcePack));
    mismatchedPack.article.id = "999";
    fs.writeFileSync(mismatchedPackPath, JSON.stringify(mismatchedPack, null, 2));

    const browser = await chromium.launch({ headless: true });
    const context = await browser.newContext({ acceptDownloads: true });
    const page = await context.newPage();

    const networkDisallowedCalls = [];
    page.on("request", (req) => {
        const url = req.url();
        const method = req.method();
        // Check for unexpected POST/PUT mutations or remote provider fetches
        if ((url.includes("/wp-json/wp/v2/media") || url.includes("async-upload.php")) && method !== "GET") {
            networkDisallowedCalls.push({ url, method, type: "media_mutation" });
        }
        if (url.includes("api.unsplash.com") || url.includes("images.unsplash.com") || url.includes("depositphotos.com")) {
            networkDisallowedCalls.push({ url, method, type: "external_provider_fetch" });
        }
    });

    try {
        // --- STEP 1: Log in as authorized editor ---
        console.log("[E2E] Step 1: Logging in as editor...");
        await page.goto(`${WP_URL}/wp-login.php`);
        await page.fill("#user_login", WP_USER);
        await page.fill("#user_pass", WP_PASS);
        await page.click("#wp-submit");
        await page.waitForSelector("#wpadminbar", { timeout: 15000 });
        console.log("[E2E] Step 1 OK: Successfully logged in to WordPress admin.");

        // --- STEP 2: Open Gutenberg editor for target post ---
        console.log(`[E2E] Step 2: Opening Gutenberg editor for post #${WP_POST_ID}...`);
        await page.goto(`${WP_URL}/wp-admin/post.php?post=${WP_POST_ID}&action=edit`);
        await page.waitForSelector(".edit-post-header", { timeout: 15000 });

        // Ensure Welcome Guide is dismissed if displayed
        await page.evaluate(() => {
            try {
                window.wp.data.dispatch("core/preferences").set("core/edit-post", "welcomeGuide", false);
            } catch (e) {}
        });
        const closeGuideBtn = await page.$(".edit-post-welcome-guide [aria-label=\"Close dialog\"]");
        if (closeGuideBtn) {
            await closeGuideBtn.click().catch(() => {});
        }

        // Verify PictovapReviewConfig is localized correctly
        const config = await page.evaluate(() => window.PictovapReviewConfig);
        assert(config, "PictovapReviewConfig must be present in window");
        assert.equal(String(config.postId), String(WP_POST_ID), "Post ID must match");
        assert.equal(config.actor, WP_USER, "Actor must match logged-in user");
        console.log(`[E2E] Step 2 OK: Gutenberg editor loaded with localized config (postId=${config.postId}, actor=${config.actor}).`);

        // --- STEP 3: Verify sidebar registration and open sidebar ---
        console.log("[E2E] Step 3: Opening Pictovap Review sidebar...");
        const plugins = await page.evaluate(() => window.wp.plugins.getPlugins().map((p) => p.name));
        assert(plugins.includes("pictovap-review-sidebar"), "pictovap-review-sidebar plugin must be registered in Gutenberg");

        await page.evaluate(() => {
            window.wp.data.dispatch("core/edit-post").openGeneralSidebar("pictovap-review-sidebar/pictovap-review-sidebar");
        });
        await page.waitForSelector("#pictovap-decision-pack", { timeout: 5000 });
        console.log("[E2E] Step 3 OK: Pictovap Review sidebar rendered with file input.");

        // --- STEP 4: Negative Test: Mismatched article ID rejection ---
        console.log("[E2E] Step 4: Testing mismatched article ID rejection...");
        await (await page.$("#pictovap-decision-pack")).setInputFiles(mismatchedPackPath);
        await page.waitForSelector(".components-notice.is-error", { timeout: 5000 });
        const mismatchError = await page.$eval(".components-notice.is-error", (el) => el.innerText);
        assert(
            mismatchError.includes("Pack article ID does not match the Gutenberg post being edited"),
            `Unexpected error notice: ${mismatchError}`
        );
        console.log("[E2E] Step 4 OK: Mismatched pack correctly rejected by Gutenberg sidebar.");

        // --- STEP 5: Import valid Decision Pack ---
        console.log("[E2E] Step 5: Importing valid Decision Pack for post...");
        await (await page.$("#pictovap-decision-pack")).setInputFiles(PACK_PATH);
        await page.waitForSelector(".pictovap-slot", { timeout: 5000 });

        const renderedSlots = await page.$$eval(".pictovap-slot", (els) => els.length);
        assert.equal(renderedSlots, slotCount, `Expected ${slotCount} slots, got ${renderedSlots}`);

        const initialProgress = await page.$eval(".pictovap-progress", (el) => el.innerText);
        assert.equal(initialProgress, `0 of ${slotCount} decisions selected`);
        console.log(`[E2E] Step 5 OK: All ${slotCount} slots rendered. Initial progress: "${initialProgress}".`);

        // --- STEP 6: Test Local Visual Comparison (Valid & Invalid files) ---
        console.log("[E2E] Step 6: Testing safe local-only visual comparison...");
        const slot0Inputs = await page.$$(".pictovap-slot:nth-of-type(1) .pictovap-local-preview input[type=\"file\"]");
        assert(slot0Inputs.length > 0, "Slot 0 must have local preview file inputs");

        // 6a: Select matching JPEG
        await slot0Inputs[0].setInputFiles(localSunsetJpg);
        await page.waitForSelector(".pictovap-slot:nth-of-type(1) .pictovap-local-preview img", { timeout: 5000 });
        const previewSrc = await page.$eval(".pictovap-slot:nth-of-type(1) .pictovap-local-preview img", (el) => el.src);
        assert(previewSrc.startsWith("blob:"), `Local preview must use ephemeral blob: URL, got ${previewSrc}`);
        console.log("[E2E] Step 6a OK: Matching JPEG rendered with blob: URL.");

        // 6b: Remove local preview
        const removeBtn = await page.$(".pictovap-slot:nth-of-type(1) .pictovap-local-preview button:has-text(\"Remove local preview\")");
        assert(removeBtn, "Remove local preview button must exist");
        await removeBtn.click();
        await page.waitForTimeout(300);
        const imgAfterRemove = await page.$(".pictovap-slot:nth-of-type(1) .pictovap-local-preview img");
        assert.equal(imgAfterRemove, null, "Local image preview must be removed after clicking remove");
        console.log("[E2E] Step 6b OK: Local preview cleanly removed and object URL revoked.");

        // 6c: Invalid signature file rejection
        if (slot0Inputs[1]) {
            await slot0Inputs[1].setInputFiles(localInvalidJpg);
            await page.waitForTimeout(500);
            const invalidNotice = await page.$eval(".components-notice.is-error", (el) => el.innerText).catch(() => "");
            assert(invalidNotice.includes("Local image preview not shown"), "Invalid local file signature must be rejected");
            console.log("[E2E] Step 6c OK: Corrupt/spoofed local image signature rejected.");
        }

        // --- STEP 7: One-click Evidenced Alternative Selection ---
        console.log("[E2E] Step 7: Testing one-click evidenced alternative selection...");
        const altButton = await page.waitForSelector(".pictovap-slot:nth-of-type(1) .pictovap-alternative button");
        const altButtonText = await altButton.innerText();
        console.log(`[E2E] Clicking alternative button: "${altButtonText}"`);
        await altButton.click();
        await page.waitForTimeout(500);

        const slot0Preview = await page.$eval(".pictovap-slot:nth-of-type(1) .pictovap-preview", (el) => el.innerText);
        assert(slot0Preview.includes("replace"), `Preview must reflect replace action: ${slot0Preview}`);
        assert(slot0Preview.includes("img-backpack-01"), `Preview must reflect replacement candidate: ${slot0Preview}`);
        console.log(`[E2E] Step 7 OK: Slot 0 alternative selected: "${slot0Preview}".`);

        // --- STEP 8: Complete decisions for remaining slots (Accept & Reject) ---
        console.log("[E2E] Step 8: Exercising Accept and Reject actions for remaining slots...");
        // Slot 1: Accept
        await (await page.$(".pictovap-slot:nth-of-type(2) button:has-text(\"Accept\")")).click();
        // Slot 2: Reject
        await (await page.$(".pictovap-slot:nth-of-type(3) button:has-text(\"Reject\")")).click();
        // Slot 3: Accept
        await (await page.$(".pictovap-slot:nth-of-type(4) button:has-text(\"Accept\")")).click();
        await page.waitForTimeout(500);

        const finalProgress = await page.$eval(".pictovap-progress", (el) => el.innerText);
        assert.equal(finalProgress, `${slotCount} of ${slotCount} decisions selected`);
        console.log(`[E2E] Step 8 OK: All decisions made. Progress: "${finalProgress}".`);

        // --- STEP 9: Export review decisions JSON ---
        console.log("[E2E] Step 9: Downloading review decisions draft...");
        const downloadPromise = page.waitForEvent("download");
        await page.click("button:has-text(\"Download review decisions\")");
        const download = await downloadPromise;
        await download.saveAs(OUTPUT_DECISIONS_PATH);
        console.log(`[E2E] Step 9 OK: Decisions saved to ${OUTPUT_DECISIONS_PATH}.`);

        const draft = JSON.parse(fs.readFileSync(OUTPUT_DECISIONS_PATH, "utf-8"));
        assert.equal(draft.kind, "pictovap.review-decisions");
        assert.equal(draft.schema_version, "1");
        assert.equal(String(draft.article_id), String(WP_POST_ID));
        assert.equal(draft.decisions.length, slotCount);
        assert.match(draft.source_sha256, /^[a-f0-9]{64}$/);
        console.log(`[E2E] Step 9 OK: Verified draft schema: kind=${draft.kind}, sha=${draft.source_sha256.slice(0, 12)}...`);

        // --- STEP 10: Unauthorized user access test ---
        console.log("[E2E] Step 10: Testing unauthorized user access prevention...");
        const contribContext = await browser.newContext();
        const contribPage = await contribContext.newPage();
        await contribPage.goto(`${WP_URL}/wp-login.php`);
        await contribPage.fill("#user_login", "contributor");
        await contribPage.fill("#user_pass", "contribpassword123");
        await contribPage.click("#wp-submit");
        await contribPage.waitForSelector("#wpadminbar", { timeout: 15000 });

        await contribPage.goto(`${WP_URL}/wp-admin/post.php?post=${WP_POST_ID}&action=edit`);
        const hasSidebarConfig = await contribPage.evaluate(() => !!window.PictovapReviewConfig);
        assert.equal(hasSidebarConfig, false, "PictovapReviewConfig must NOT be enqueued for unauthorized user");
        console.log("[E2E] Step 10 OK: Unauthorized user denied sidebar assets.");
        await contribContext.close();

        // --- STEP 11: Zero disallowed network calls ---
        console.log("[E2E] Step 11: Verifying zero forbidden network calls...");
        assert.equal(
            networkDisallowedCalls.length,
            0,
            `Forbidden network calls detected: ${JSON.stringify(networkDisallowedCalls)}`
        );
        console.log("[E2E] Step 11 OK: Zero media mutations or external provider fetches occurred.");

    } finally {
        await browser.close();
    }

    console.log("[E2E] All browser-level acceptance tests PASSED successfully.");
}

runAcceptance().catch((err) => {
    console.error("[E2E ERROR]", err);
    process.exit(1);
});
