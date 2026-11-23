"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const model = require("../assets/review-model.js");

function pack() {
    return {
        kind: "pictovap.decision-pack",
        schema_version: "1",
        article: { id: "42", title: "Sample Gutenberg guide" },
        slots: [{
            slot_id: "featured",
            purpose: "featured_image",
            target_heading: "A weekend guide",
            candidates: [
                { slot_id: "featured", candidate_id: "asset-1", decision: "selected", final_score: 9 },
                { slot_id: "featured", candidate_id: "asset-2", decision: "needs_review", final_score: 7 }
            ],
            proposal: {
                candidate_id: "asset-1",
                provenance: {
                    image_id: "asset-1",
                    slot_id: "featured",
                    provider: "local",
                    generated_filename: "asset-1.webp",
                    license_status: "unknown"
                },
                placement: {
                    candidate_id: "asset-1",
                    slot_id: "featured",
                    output_path: "images/asset-1.webp"
                }
            },
            evidence: []
        }],
        review: { status: "pending", decisions: [] },
        application: { status: "not_applied", receipts: [] }
    };
}

function alternative() {
    return {
        candidate_id: "asset-2",
        provenance: {
            image_id: "asset-2",
            slot_id: "featured",
            provider: "external",
            generated_filename: "asset-2.webp",
            license_status: "unknown"
        },
        placement: {
            candidate_id: "asset-2",
            slot_id: "featured",
            output_path: "images/asset-2.webp"
        }
    };
}

test("valid Gutenberg post import and explicit license uncertainty", () => {
    const proposal = pack();
    assert.equal(model.checkPack(proposal, 42), proposal);
    const decision = model.makeDecision(
        proposal, "featured", "accept", "editor", "2026-11-23T08:00:00Z"
    );
    const view = model.preview(proposal, [decision]);
    assert.equal(view[0].chosen, "asset-1");
    assert.equal(view[0].license, "unknown");
    assert.equal(proposal.review.status, "pending");
    assert.equal(proposal.application.status, "not_applied");
});

test("other WordPress post and forged application are rejected", () => {
    assert.throws(() => model.checkPack(pack(), 43), /does not match/);
    const application = pack();
    application.application.receipts.push({ status: "completed" });
    assert.throws(() => model.checkPack(application, 42), /CMS application/);
    const tampered = pack();
    tampered.slots[0].proposal.provenance.image_id = "wrong-image";
    assert.throws(() => model.checkPack(tampered, 42), /mismatched evidence/);
});

test("reject does not imply a selected image", () => {
    const proposal = pack();
    const review = model.makeDecision(proposal, "featured", "reject", "editor", "2026-11-23T08:00:00Z");
    const view = model.preview(proposal, [review]);
    assert.equal(view[0].action, "reject");
    assert.equal(view[0].chosen, null);
    assert.equal(view[0].license, "not_selected");
});

test("replacement requires scored, non-rejected, atomic evidence", () => {
    const proposal = pack();
    const asset = alternative();
    const decision = model.makeDecision(
        proposal, "featured", "replace", "editor", "2026-11-23T08:00:00Z", asset
    );
    assert.equal(decision.replacement.candidate_id, "asset-2");
    asset.provenance.generated_filename = "changed-after-review.webp";
    assert.equal(decision.replacement.provenance.generated_filename, "asset-2.webp");

    const invalid = alternative();
    invalid.placement.candidate_id = "asset-1";
    assert.throws(
        () => model.makeDecision(proposal, "featured", "replace", "editor",
            "2026-11-23T08:00:00Z", invalid),
        /incomplete or mismatched/
    );
    const rejected = pack();
    rejected.slots[0].candidates[1].decision = "rejected";
    assert.throws(
        () => model.makeDecision(rejected, "featured", "replace", "editor",
            "2026-11-23T08:00:00Z", alternative()),
        /non-rejected/
    );
});

test("fingerprinted export requires every slot; no duplicate slot decisions", () => {
    const proposal = pack();
    const sha = "f".repeat(64);
    const decision = model.makeDecision(proposal, "featured", "reject", "editor", "2026-11-23T08:00:00Z");
    assert.throws(() => model.exportDraft(proposal, sha, []), /Every slot/);
    assert.throws(() => model.exportDraft(proposal, "bad-hash", [decision]), /SHA-256/);
    const draft = model.exportDraft(proposal, sha, [decision]);
    assert.deepEqual(Object.keys(draft).sort(),
        ["article_id", "decisions", "kind", "schema_version", "source_sha256"]);
    assert.equal(draft.kind, "pictovap.review-decisions");
    assert.equal(draft.article_id, "42");
    assert.equal(draft.decisions[0].action, "reject");
});

test("unset proposal cannot be accepted; duplicate slot IDs cannot be imported", () => {
    const proposal = pack();
    proposal.slots[0].proposal = {
        candidate_id: null, provenance: null, placement: null
    };
    assert.equal(model.checkPack(proposal, 42), proposal);
    assert.throws(
        () => model.makeDecision(proposal, "featured", "accept", "editor",
            "2026-11-23T08:00:00Z"),
        /empty or unbound/
    );
    const repeated = pack();
    repeated.slots.push(JSON.parse(JSON.stringify(repeated.slots[0])));
    assert.throws(() => model.checkPack(repeated, 42), /Duplicate slot/);
});
