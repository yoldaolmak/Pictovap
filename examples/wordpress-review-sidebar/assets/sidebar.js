/* Read-only Gutenberg editorial review. Local files only; no WordPress write calls. */
(function (wp, config, model) {
    "use strict";

    if (!wp || !wp.plugins || !wp.editor || !wp.editor.PluginSidebar ||
            !wp.element || !model || !config) {
        return;
    }
    var el = wp.element.createElement;
    var useState = wp.element.useState;
    var Button = wp.components.Button;
    var Notice = wp.components.Notice;
    var PluginSidebar = wp.editor.PluginSidebar;

    function fileToTextAndFingerprint(file) {
        if (!file || file.size > 2 * 1024 * 1024) {
            return Promise.reject(new Error("Choose a JSON file smaller than 2 MB."));
        }
        if (!window.crypto || !window.crypto.subtle) {
            return Promise.reject(new Error("Secure HTTPS editor context is required for SHA-256."));
        }
        return file.arrayBuffer().then(function (buffer) {
            var text = new TextDecoder("utf-8", { fatal: true }).decode(buffer);
            return window.crypto.subtle.digest("SHA-256", buffer).then(function (digest) {
                var bytes = new Uint8Array(digest);
                var fingerprint = Array.from(bytes, function (byte) {
                    return byte.toString(16).padStart(2, "0");
                }).join("");
                return { text: text, fingerprint: fingerprint };
            });
        });
    }

    function downloadDraft(filename, body) {
        var blob = new Blob([JSON.stringify(body, null, 2) + "\n"], {
            type: "application/json;charset=utf-8"
        });
        var url = window.URL.createObjectURL(blob);
        var anchor = document.createElement("a");
        anchor.href = url;
        anchor.download = filename;
        document.body.appendChild(anchor);
        anchor.click();
        document.body.removeChild(anchor);
        window.setTimeout(function () { window.URL.revokeObjectURL(url); }, 1000);
    }

    function EditorSidebar() {
        var packState = useState(null);
        var pack = packState[0];
        var setPack = packState[1];
        var shaState = useState("");
        var sha256 = shaState[0];
        var setSha256 = shaState[1];
        var decisionState = useState(Object.create(null));
        var decisionsBySlot = decisionState[0];
        var setDecisionsBySlot = decisionState[1];
        var errorState = useState("");
        var error = errorState[0];
        var setError = errorState[1];
        var ready = pack ? pack.slots.filter(function (s) {
            return Object.prototype.hasOwnProperty.call(decisionsBySlot, s.slot_id);
        }).length : 0;
        var total = pack ? pack.slots.length : 0;
        var decisions = pack ? pack.slots.filter(function (slot) {
            return decisionsBySlot[slot.slot_id];
        }).map(function (slot) {
            return decisionsBySlot[slot.slot_id];
        }) : [];
        var preview = pack ? model.preview(pack, decisions) : [];

        function choose(slotId, action, replacement) {
            try {
                var stamp = new Date().toISOString();
                var decision = model.makeDecision(
                    pack, slotId, action, config.actor, stamp, replacement
                );
                setDecisionsBySlot(function (previous) {
                    var next = Object.assign(Object.create(null), previous);
                    next[slotId] = decision;
                    return next;
                });
                setError("");
            } catch (e) {
                setError(e.message);
            }
        }

        function importPack(event) {
            var file = event.target.files && event.target.files[0];
            // Clear the old decisions immediately; invalid imports must not retain them.
            setPack(null);
            setSha256("");
            setDecisionsBySlot(Object.create(null));
            if (!file) {
                return;
            }
            fileToTextAndFingerprint(file).then(function (result) {
                var imported = JSON.parse(result.text);
                model.checkPack(imported, config.postId);
                setPack(imported);
                setSha256(result.fingerprint);
                setError("");
            }).catch(function (e) {
                setError("Pack was not loaded: " + e.message);
            });
        }

        function importReplacement(slotId, event) {
            var file = event.target.files && event.target.files[0];
            if (!file) {
                return;
            }
            // This existing evidence document is not created or licensed by the UI.
            if (file.size > 256 * 1024) {
                setError("Replacement evidence must be smaller than 256 KB.");
                return;
            }
            file.text().then(function (text) {
                choose(slotId, "replace", JSON.parse(text));
            }).catch(function (e) {
                setError("Replacement evidence could not be read: " + e.message);
            });
        }

        function exportDecisions() {
            try {
                var payload = model.exportDraft(pack, sha256, decisions);
                downloadDraft("pictovap-post-" + config.postId + "-review-decisions.json", payload);
                setError("");
            } catch (e) {
                setError(e.message);
            }
        }

        return el(PluginSidebar, {
            name: "pictovap-review-sidebar",
            title: "Pictovap Review",
            icon: "format-image"
        }, el("div", { className: "pictovap-review" },
            el("h2", null, "Image review"),
            el("p", null, "Post #" + config.postId + " · Editor: " + config.actor),
            el("p", null, "Import a pending Pictovap Decision Pack made for this post. " +
                "This panel only makes a local draft. It never uploads, saves or publishes."),
            el("label", { htmlFor: "pictovap-decision-pack" }, "Decision Pack JSON"),
            el("input", {
                id: "pictovap-decision-pack",
                type: "file",
                accept: ".json,application/json",
                onChange: importPack
            }),
            error ? el(Notice, {
                status: "error",
                isDismissible: true,
                onRemove: function () { setError(""); }
            }, error) : null,
            pack ? el("div", null,
                el("p", { className: "pictovap-progress" },
                    ready + " of " + total + " decisions selected"),
                pack.slots.map(function (slot) {
                    var current = decisionsBySlot[slot.slot_id];
                    var proposal = slot.proposal;
                    var provenance = proposal.provenance || {};
                    var row = preview.find(function (item) {
                        return item.slot_id === slot.slot_id;
                    });
                    return el("section", {
                        className: "pictovap-slot",
                        key: slot.slot_id
                    },
                        el("h3", null, slot.target_heading || slot.slot_id),
                        el("p", null, "Purpose: " + (slot.purpose || "image")),
                        el("p", null, "Proposed: " + (proposal.candidate_id || "none")),
                        el("p", null, "Provider: " + (provenance.provider || "unknown")),
                        el("p", null, "Rights evidence: " +
                            (provenance.license_status || "unknown")),
                        el("ul", null, slot.candidates.map(function (candidate) {
                            return el("li", { key: candidate.candidate_id },
                                candidate.candidate_id + " · " +
                                candidate.decision + " · score " +
                                (candidate.final_score === undefined ?
                                    "n/a" : String(candidate.final_score)),
                                candidate.human_reason ?
                                    el("p", null, "Reason: " + candidate.human_reason) : null
                            );
                        })),
                        slot.alternatives ? el("div", {
                            className: "pictovap-alternatives"
                        },
                            el("h4", null, "Source-backed alternatives"),
                            slot.alternatives.length ? slot.alternatives.map(function (alternative) {
                                var evidence = alternative.provenance || {};
                                var candidate = slot.candidates.find(function (item) {
                                    return item.candidate_id === alternative.candidate_id;
                                });
                                return el("div", {
                                    className: "pictovap-alternative",
                                    key: alternative.candidate_id
                                },
                                    el("p", null, "Candidate: " + alternative.candidate_id),
                                    el("p", null, "Provider: " + (evidence.provider || "unknown")),
                                    el("p", null, "Rights evidence: " +
                                        (evidence.license_status || "unknown")),
                                    candidate && candidate.human_reason ?
                                        el("p", null, "Reason: " + candidate.human_reason) : null,
                                    el(Button, {
                                        variant: current && current.action === "replace" &&
                                            current.replacement.candidate_id === alternative.candidate_id ?
                                            "primary" : "secondary",
                                        onClick: function () {
                                            choose(slot.slot_id, "replace", alternative);
                                        }
                                    }, "Choose " + alternative.candidate_id)
                                );
                            }) : el("p", null, "No evidenced alternative is eligible.")
                        ) : null,
                        el("div", { className: "pictovap-actions" },
                            el(Button, {
                                variant: current && current.action === "accept" ?
                                    "primary" : "secondary",
                                disabled: !proposal.candidate_id,
                                onClick: function () { choose(slot.slot_id, "accept"); }
                            }, "Accept"),
                            el(Button, {
                                variant: current && current.action === "reject" ?
                                    "primary" : "secondary",
                                onClick: function () { choose(slot.slot_id, "reject"); }
                            }, "Reject")
                        ),
                        !slot.alternatives ? el("div", null,
                            el("label", null, "Legacy pack: import replacement evidence JSON"),
                            el("input", {
                                type: "file",
                                accept: ".json,application/json",
                                onChange: function (event) {
                                    importReplacement(slot.slot_id, event);
                                }
                            })
                        ) : null,
                        el("p", { className: "pictovap-preview" },
                            "Preview (not Core-validated): " + row.action +
                            " · " + (row.chosen || "no image") +
                            " · rights " + row.license)
                    );
                }),
                el("p", null, "Rights marked unknown require independent verification. " +
                    "No decision grants license rights or CMS authority."),
                el(Button, {
                    variant: "primary",
                    disabled: ready !== total,
                    onClick: exportDecisions
                }, "Download review decisions"),
                el("p", null, "Next: run pictovap review-import locally with the " +
                    "original Decision Pack and downloaded decisions. Core verifies " +
                    "bindings, review completeness and the file fingerprint before " +
                    "producing a reviewed pack.")
            ) : null
        ));
    }

    wp.plugins.registerPlugin("pictovap-review-sidebar", { render: EditorSidebar });
})(window.wp, window.PictovapReviewConfig, window.PictovapReviewModel);
