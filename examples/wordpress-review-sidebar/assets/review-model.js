/* Portable, browser-only review draft. Core Python remains the final validator. */
(function (root) {
    "use strict";

    var KIND = "pictovap.review-decisions";
    var MAX_SLOTS = 100;
    var MAX_CANDIDATES = 1000;

    function object(value) {
        return value !== null && typeof value === "object" && !Array.isArray(value);
    }

    function nonempty(value) {
        return typeof value === "string" && value.trim().length > 0;
    }

    function requireValue(condition, message) {
        if (!condition) {
            throw new Error(message);
        }
    }

    function validAsset(asset, slotId, candidateId) {
        if (!object(asset) || !nonempty(asset.candidate_id) || !object(asset.provenance) ||
                !object(asset.placement) || asset.candidate_id !== candidateId) {
            return false;
        }
        var provenance = asset.provenance;
        var placement = asset.placement;
        if (provenance.image_id !== candidateId ||
                provenance.slot_id !== slotId ||
                placement.slot_id !== slotId ||
                placement.candidate_id !== candidateId ||
                !nonempty(provenance.provider) ||
                !nonempty(provenance.generated_filename) ||
                !nonempty(placement.output_path)) {
            return false;
        }
        return placement.output_path.replace(/\\/g, "/").split("/").pop() ===
            provenance.generated_filename.replace(/\\/g, "/").split("/").pop();
    }

    function checkPack(pack, postId) {
        requireValue(object(pack), "A Decision Pack object is required.");
        requireValue(pack.kind === "pictovap.decision-pack" && pack.schema_version === "1",
            "Unsupported Decision Pack kind or schema.");
        requireValue(object(pack.article) && nonempty(String(pack.article.id || "")),
            "Pack has no article identity.");
        requireValue(String(pack.article.id) === String(postId),
            "Pack article ID does not match the Gutenberg post being edited.");
        requireValue(object(pack.review) && pack.review.status === "pending" &&
            Array.isArray(pack.review.decisions) && pack.review.decisions.length === 0,
            "Import an unreviewed Decision Pack with no existing decisions.");
        requireValue(object(pack.application) && pack.application.status === "not_applied" &&
            Array.isArray(pack.application.receipts) && pack.application.receipts.length === 0,
            "A review cannot carry CMS application results.");
        requireValue(Array.isArray(pack.slots) && pack.slots.length > 0 &&
            pack.slots.length <= MAX_SLOTS, "Pack must contain 1–100 image slots.");

        var seen = Object.create(null);
        var totalCandidates = 0;
        pack.slots.forEach(function (slot) {
            requireValue(object(slot) && nonempty(slot.slot_id), "A slot lacks an ID.");
            requireValue(!seen[slot.slot_id], "Duplicate slot IDs are forbidden.");
            seen[slot.slot_id] = true;
            requireValue(Array.isArray(slot.candidates) &&
                slot.candidates.length <= MAX_CANDIDATES, "Invalid candidate list.");
            totalCandidates += slot.candidates.length;
            requireValue(totalCandidates <= MAX_CANDIDATES,
                "Too many scored candidates for a single browser review.");
            requireValue(object(slot.proposal), "Slot proposal is missing.");
            var proposedId = slot.proposal.candidate_id;
            var proposalEmpty = proposedId == null &&
                slot.proposal.provenance == null && slot.proposal.placement == null;
            if (!proposalEmpty) {
                requireValue(nonempty(proposedId) &&
                    validAsset(slot.proposal, slot.slot_id, proposedId),
                    "A proposed image has incomplete or mismatched evidence.");
                requireValue(slot.candidates.some(function (candidate) {
                    return object(candidate) &&
                        candidate.slot_id === slot.slot_id &&
                        candidate.candidate_id === proposedId &&
                        candidate.decision === "selected";
                }), "Proposed image must be a scored selected candidate.");
            }
            if (Object.prototype.hasOwnProperty.call(slot, "alternatives")) {
                requireValue(Array.isArray(slot.alternatives) &&
                    slot.alternatives.length <= MAX_CANDIDATES,
                    "Invalid source-backed alternative list.");
                var alternativeIds = Object.create(null);
                slot.alternatives.forEach(function (alternative) {
                    requireValue(object(alternative) && nonempty(alternative.candidate_id) &&
                        validAsset(alternative, slot.slot_id, alternative.candidate_id),
                        "Alternative evidence is incomplete or mismatched.");
                    var alternativeId = alternative.candidate_id;
                    requireValue(alternativeId !== proposedId && !alternativeIds[alternativeId],
                        "Duplicate or proposed candidate in alternative list.");
                    alternativeIds[alternativeId] = true;
                    requireValue(slot.candidates.some(function (candidate) {
                        return object(candidate) &&
                            candidate.slot_id === slot.slot_id &&
                            candidate.candidate_id === alternativeId &&
                            candidate.decision !== "rejected";
                    }), "Alternative must be a scored non-rejected candidate.");
                });
            }
        });
        return pack;
    }

    function getSlot(pack, id) {
        var slot = pack.slots.find(function (item) { return item.slot_id === id; });
        requireValue(!!slot, "Unknown review slot.");
        return slot;
    }

    function makeDecision(pack, slotId, action, actor, timestamp, replacement) {
        var slot = getSlot(pack, slotId);
        requireValue(["accept", "reject", "replace"].indexOf(action) >= 0,
            "Invalid editor decision.");
        requireValue(nonempty(actor) && nonempty(timestamp),
            "An editor and timestamp are required.");
        var decision = {
            slot_id: slotId,
            action: action,
            actor: actor.trim(),
            decided_at: timestamp
        };
        if (action === "accept") {
            requireValue(nonempty(slot.proposal.candidate_id) &&
                validAsset(slot.proposal, slotId, slot.proposal.candidate_id),
                "Cannot accept an empty or unbound proposal.");
        }
        if (action === "replace") {
            requireValue(object(replacement) && nonempty(replacement.candidate_id),
                "Replacement needs an existing candidate/provenance/placement evidence object.");
            requireValue(replacement.candidate_id !== slot.proposal.candidate_id,
                "Replacement must differ from proposal.");
            requireValue(slot.candidates.some(function (candidate) {
                return object(candidate) &&
                    candidate.candidate_id === replacement.candidate_id &&
                    candidate.slot_id === slotId &&
                    candidate.decision !== "rejected";
            }), "Replacement must be a scored, non-rejected candidate.");
            requireValue(validAsset(replacement, slotId, replacement.candidate_id),
                "Replacement evidence is incomplete or mismatched.");
            if (Object.prototype.hasOwnProperty.call(slot, "alternatives")) {
                requireValue(slot.alternatives.some(function (alternative) {
                    return JSON.stringify(alternative) === JSON.stringify(replacement);
                }), "Replacement must match source-backed alternative evidence.");
            }
            decision.replacement = JSON.parse(JSON.stringify(replacement));
        }
        return decision;
    }

    function preview(pack, decisions) {
        var selected = Object.create(null);
        decisions.forEach(function (decision) {
            selected[decision.slot_id] = decision;
        });
        return pack.slots.map(function (slot) {
            var decision = selected[slot.slot_id];
            var action = decision ? decision.action : "pending";
            var asset = action === "accept" ? slot.proposal :
                action === "replace" ? decision.replacement : null;
            var license = asset && asset.provenance &&
                asset.provenance.license_status;
            return {
                slot_id: slot.slot_id,
                action: action,
                proposed: slot.proposal.candidate_id || null,
                chosen: asset ? asset.candidate_id : null,
                license: asset ? (license || "unknown") : "not_selected"
            };
        });
    }

    function exportDraft(pack, sha256, decisions) {
        requireValue(/^[a-f0-9]{64}$/.test(sha256), "Pack SHA-256 fingerprint is required.");
        requireValue(Array.isArray(decisions) &&
            decisions.length === pack.slots.length, "Every slot needs an editor decision.");
        var unique = Object.create(null);
        var verifiedDecisions = decisions.map(function (decision) {
            requireValue(!unique[decision.slot_id], "Duplicate slot review.");
            unique[decision.slot_id] = true;
            return makeDecision(pack, decision.slot_id, decision.action,
                decision.actor, decision.decided_at, decision.replacement);
        });
        return {
            kind: KIND,
            schema_version: "1",
            article_id: String(pack.article.id),
            source_sha256: sha256,
            decisions: verifiedDecisions
        };
    }

    var api = {
        checkPack: checkPack,
        makeDecision: makeDecision,
        preview: preview,
        exportDraft: exportDraft,
        validAsset: validAsset
    };
    if (typeof module === "object" && module.exports) {
        module.exports = api;
    }
    root.PictovapReviewModel = api;
})(typeof window === "object" ? window : globalThis);
