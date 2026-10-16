// Turns each SafeShelf API answer into plain rows {icon, text, sub?, link?} for display. No DOM here, so it is easy to test.
// Loaded as a normal script before content.js and lab.js; exposes globalThis.SafeShelfPanels.
(() => {
  const REL = {
    exact_model: "Same model",
    rebranded_equivalent: "Same hardware, sold under another brand",
    model_variant: "A variant of the same product",
    shared_component: "Shares a component",
    visually_similar: "Only looks similar (not proof it is the same)",
  };
  const pct = (c) => (typeof c === "number" ? ` · ${Math.round(c * 100)}% sure` : "");
  const ev = (a) => (a && a.length ? `Evidence: ${a.join(", ")}` : undefined);
  const day = (t) => (t ? String(t).slice(0, 10) : "");
  const vm = (title, rows, empty) => ({ title, rows, empty: rows.length ? null : empty });
  const rupees = (n) => (typeof n === "number" ? `₹${n.toLocaleString("en-IN")}` : "");

  const P = {
    certifications(d) {
      const icon = { verified: "ok", mismatch: "stop", unknown: "unknown" };
      return vm("Safety marks", (d.checks || []).map((c) => ({
        icon: icon[c.result] || "unknown",
        text: `${c.authority}${c.number ? " " + c.number : ""}: ` + (c.result === "mismatch"
          ? `the listing says ${c.claimed_value ?? "?"}, the registry says ${c.registry_value ?? "?"}${c.field ? ` (${c.field.replace("_", " ")})` : ""}`
          : c.result === "verified" ? "matches the official registry" : c.reason || "could not be verified"),
        sub: c.checked_at ? `Checked ${day(c.checked_at)}` : undefined,
        link: c.registry_record_url,
      })), "No safety marks were found on this product to check.");
    },
    relationships(d) {
      return vm("Copies and related products", (d.relationships || []).map((r) => ({
        icon: r.status === "verified" ? "ok" : "unknown",
        text: `${REL[r.relationship] || r.relationship}: ${r.target_id}${pct(r.confidence)}`,
        sub: [r.status === "verified" ? "Verified" : "Not verified yet", ev(r.evidence_ids)].filter(Boolean).join(" · "),
      })), "No copies or related products are known for this product.");
    },
    duplicates(d) {
      return vm("Copies found by AI", (d.matches || []).map((m) => ({
        icon: m.status === "verified" ? "ok" : "unknown",
        text: `${REL[m.relationship] || m.relationship}: ${m.product_id}${pct(m.confidence)}`,
        sub: [
          m.agreements?.length ? `Agree: ${m.agreements.join("; ")}` : "",
          m.conflicts?.length ? `Differ: ${m.conflicts.join("; ")}` : "",
          m.would_change_if?.length ? `Would change if: ${m.would_change_if.join("; ")}` : "",
          ev(m.evidence_ids) || "",
        ].filter(Boolean).join(" · "),
      })), "No copies were found.");
    },
    history(d) {
      const rows = (d.events || []).map((e) => ({ icon: e.change_type === "hazard_signal" ? "warn" : "dot", text: e.summary, sub: [day(e.at), e.actor, ev(e.evidence_ids)].filter(Boolean).join(" · ") }));
      (d.recalls || []).forEach((r) => rows.unshift({ icon: "stop", text: `Recall: ${r.title || r.recall_id || JSON.stringify(r)}`, sub: day(r.date) }));
      return vm("Product history", rows, "Nothing recorded yet for this product.");
    },
    alternatives(d) {
      return vm("Safer options", (d.alternatives || []).map((a) => ({
        icon: a.seller_authorised ? "ok" : "unknown",
        text: `${a.reason || REL[a.relationship] || a.product_id}`,
        sub: [a.seller, rupees(a.price), a.hazard_reports === 0 ? "no hazard reports" : a.hazard_reports != null ? `${a.hazard_reports} hazard reports` : "", a.certifications_valid ? "certifications valid" : ""].filter(Boolean).join(" · "),
        link: a.url,
      })), "No safer genuine option was found.");
    },
    product(d) {
      const rows = [
        d.brand && { icon: "dot", text: `Brand: ${d.brand}` }, d.model && { icon: "dot", text: `Model: ${d.model}` },
        d.category && { icon: "dot", text: `Category: ${String(d.category).replace("_", " ")}` }, d.gtin && { icon: "dot", text: `GTIN: ${d.gtin}` },
        ...Object.entries(d.attributes || {}).map(([k, v]) => ({ icon: "dot", text: `${k.replace("_", " ")}: ${v}` })),
        d.verification_status && { icon: "dot", text: `Identity: ${d.verification_status}`, sub: d.identity_version != null ? `version ${d.identity_version}` : undefined },
      ].filter(Boolean);
      return vm("Product details", rows, "No details are stored for this product.");
    },
    identify(d) {
      return vm("How SafeShelf identified it", [
        { icon: d.identity_status === "verified" ? "ok" : "unknown", text: `${[d.brand, d.model].filter(Boolean).join(" ") || d.product_id}`, sub: `Status: ${d.identity_status || "unknown"}${pct(d.confidence)}` },
        ...(d.certifications_claimed || []).map((c) => ({ icon: "dot", text: `The listing claims: ${c}` })),
      ].filter((r) => r.text), "Could not identify this listing.");
    },
    safety(d) {
      const level = { green: "ok", amber: "warn", red: "stop", not_enough_evidence: "unknown" };
      const rows = [{ icon: level[d.verdict] || "unknown", text: `Verdict: ${String(d.verdict).replace(/_/g, " ")}`, sub: d.reviews_checked != null ? `${d.reviews_checked} reviews checked` : undefined },
        { icon: d.official_status?.recalled ? "stop" : "ok", text: d.official_status?.recalled ? "Officially recalled" : `Not recalled (checked ${(d.official_status?.checked || []).join(", ") || "no registries"})` },
        ...(d.ai_findings || []).map((f) => ({ icon: "warn", text: `${f.independent_reports ?? "?"} reports of ${f.mechanism || f.hazard_type} (${String(f.status).replace(/_/g, " ")})`, sub: [f.severity && `severity ${f.severity}`, f.with_photos != null && `${f.with_photos} with photos`, ev(f.evidence_ids)].filter(Boolean).join(" · ") }))];
      return vm("Safety findings", rows, "");
    },
    ownerGuidance(d) {
      const icon = { recalled: "stop", hazard_reports: "warn", no_known_issue: "ok", not_enough_evidence: "unknown" };
      const rows = [{ icon: icon[d.situation] || "unknown", text: d.headline }, ...(d.steps || []).map((s) => ({ icon: String(s.n), text: s.title, sub: [s.detail, ev(s.evidence_ids)].filter(Boolean).join(" · "), link: s.url }))];
      (d.safer_alternatives || []).forEach((a) => rows.push({ icon: "shield", text: `Safer option: ${[a.brand, a.model].filter(Boolean).join(" ")}`, sub: a.reason, link: a.url }));
      return { ...vm("Already bought it?", rows, ""), note: d.label };
    },
    caseFile(d) {
      const rows = [{ icon: "scale", text: `Verdict: ${String(d.verdict).replace(/_/g, " ")}`, sub: d.decided_by?.rule },
        { icon: "ai", text: d.decided_by?.ai_role || "" },
        ...(d.linked_recalls || []).map((r) => ({ icon: "stop", text: `Recall ${r.recall_id}: ${r.title}`, sub: [day(r.notice_date), r.match].filter(Boolean).join(" · "), link: r.url }))];
      (d.findings || []).forEach((f) => {
        rows.push({ icon: "warn", text: `${f.independent_reports} reports of ${f.mechanism}`, sub: [`severity ${f.severity}`, `${f.with_photos} with photos`, `first seen ${f.first_seen}`, ev(f.evidence_ids)].join(" · ") });
        (f.quotes || []).forEach((q) => rows.push({ icon: "quote", text: q.quote, sub: [q.evidence_id, q.date].filter(Boolean).join(" · ") }));
      });
      rows.push({ icon: "person", text: `Awaiting a person's review. Not sent to anyone.`, sub: d.review_gate?.next_step, link: d.regulator?.url });
      return { ...vm(`Case file ${d.case_file_id}`, rows.filter((r) => r.text), ""), note: d.label };
    },
    report(d) {
      return vm("Report received", [{ icon: "ok", text: `Report ${d.report_id} ${d.status}`, sub: d.pii_masked ? "Personal details were masked automatically." : undefined }], "");
    },
    catalogScan(d) {
      const rows = (d.results || []).map((r) => ({ icon: r.finding === "certification_mismatch" ? "stop" : "warn", text: `Row ${r.row}: ${r.listing_title}`, sub: [String(r.finding).replace(/_/g, " "), r.status && String(r.status).replace(/_/g, " "), ev(r.evidence_ids)].filter(Boolean).join(" · ") }));
      return { ...vm(d.summary || "Catalog scan", rows, "No findings."), note: `${d.listings_checked ?? "?"} listings checked${d.seconds_per_1000_listings ? ` · ${d.seconds_per_1000_listings} s per 1,000` : ""} · job ${d.job_id} (${d.status})` };
    },
    trace(d) {
      return vm(`Investigation ${d.investigation_id}`, (d.steps || []).map((s) => ({ icon: String(s.n), text: `${s.tool}: ${s.summary}`, sub: [s.model, s.seconds != null ? `${s.seconds} s` : "", s.cost_usd != null ? `$${s.cost_usd} (≈ ₹${(s.cost_usd * 88).toFixed(2)})` : ""].filter(Boolean).join(" · ") })), "No steps recorded.");
    },
    bench(d) {
      const NAME = { keyword_rules: "Keyword rules", gemini_alone: "Gemini alone", safeshelf: "SafeShelf", safeshelf_no_pooling: "SafeShelf without pooling" };
      const pc = (x) => (typeof x === "number" ? `${Math.round(x * 100)}%` : "n/a");
      const line = (m) => m.recalls_flagged === undefined && m.median_lead_weeks === undefined && m.false_alarm_rate === undefined
        ? Object.entries(m).map(([k, v]) => `${k.replace(/_/g, " ")}: ${v ?? "n/a"}`).join(" · ") // unknown shape: show whatever is there
        : [`recalls flagged ${m.recalls_flagged ?? "n/a"}`, `false alarms ${m.false_alarms ?? "n/a"} (${pc(m.false_alarm_rate)})`, `median lead ${m.median_lead_weeks ?? "n/a"} weeks`].join(" · ");
      const rows = [{ heading: "Early warning: how many recalls were caught from reviews, and how many false alarms" }];
      for (const [task, methods] of Object.entries(d.tasks || {})) {
        if (Object.keys(d.tasks).length > 1) rows.push({ heading: task.replace(/_/g, " ") });
        for (const [method, m] of Object.entries(methods)) rows.push({ icon: method === "safeshelf" ? "shield" : "dot", text: NAME[method] || method.replace(/_/g, " "), sub: line(m) });
      }
      if (d.safeshelf_on_test_half) {
        rows.push({ heading: "Held-out test half (the unbiased figure)" });
        rows.push({ icon: "lab", text: "SafeShelf on recalls it was not tuned on", sub: line(d.safeshelf_on_test_half) });
      }
      if (d.safeshelf_params) rows.push({ icon: "settings", text: "SafeShelf alarm settings (tuned on the train half)", sub: Object.entries(d.safeshelf_params).map(([k, v]) => `${k.replace(/_/g, " ")}: ${v}`).join(" · ") });
      if ((d.caveats || []).length) { rows.push({ heading: "Read this before quoting the numbers" }); d.caveats.forEach((c) => rows.push({ icon: "info", text: c })); }
      if ((d.per_recall || []).length) {
        rows.push({ heading: `Each recall (${d.per_recall.length})` });
        const lead = (x) => (x == null ? "missed" : `${x} days early`);
        d.per_recall.forEach((r) => rows.push({ icon: r.safeshelf_lead_days != null ? "ok" : "dot", text: `${r.title} (${r.recall_date})`,
          sub: `${r.split} · ${r.listings} listings · ${r.reviews_before_recall} reviews before the recall · keyword ${lead(r.keyword_rules_lead_days)} · Gemini ${lead(r.gemini_alone_lead_days)} · SafeShelf ${lead(r.safeshelf_lead_days)}` }));
      }
      if (Array.isArray(d.controls)) rows.push({ heading: `Controls: ${d.controls.length} products never recalled, used to count false alarms` });
      return { title: "SafeShelfBench", rows, note: d.generated_at ? `Generated ${day(d.generated_at)}` : "Not generated yet" };
    },
  };
  // Line icons for row markers, by name. Renderers put the SVG in when the name is known and show the text otherwise (step numbers).
  P.ICONS = {
    ok: "<svg viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.7\" stroke-linecap=\"round\" stroke-linejoin=\"round\" aria-hidden=\"true\"><circle cx=\"12\" cy=\"12\" r=\"9\"/><path d=\"m8 12.5 2.7 2.7L16 9.8\"/></svg>",
    stop: "<svg viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.7\" stroke-linecap=\"round\" stroke-linejoin=\"round\" aria-hidden=\"true\"><circle cx=\"12\" cy=\"12\" r=\"9\"/><path d=\"m9 9 6 6m0-6-6 6\"/></svg>",
    unknown: "<svg viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.7\" stroke-linecap=\"round\" stroke-linejoin=\"round\" aria-hidden=\"true\"><circle cx=\"12\" cy=\"12\" r=\"9\"/><path d=\"M9.6 9.3a2.5 2.5 0 0 1 4.8.9c0 1.7-2.4 2.2-2.4 3.6M12 17h.01\"/></svg>",
    warn: "<svg viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.7\" stroke-linecap=\"round\" stroke-linejoin=\"round\" aria-hidden=\"true\"><path d=\"M10.3 4.3 2.8 17.5A2 2 0 0 0 4.5 20.5h15a2 2 0 0 0 1.7-3L13.7 4.3a2 2 0 0 0-3.4 0zM12 9.5v4M12 17h.01\"/></svg>",
    shield: "<svg viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.7\" stroke-linecap=\"round\" stroke-linejoin=\"round\" aria-hidden=\"true\"><path d=\"M12 3.5 5 6.2v5.3c0 4.3 2.9 7.6 7 9 4.1-1.4 7-4.7 7-9V6.2z\"/></svg>",
    dot: "<svg viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.7\" stroke-linecap=\"round\" stroke-linejoin=\"round\" aria-hidden=\"true\"><circle cx=\"12\" cy=\"12\" r=\"2.2\" fill=\"currentColor\" stroke=\"none\"/></svg>",
    scale: "<svg viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.7\" stroke-linecap=\"round\" stroke-linejoin=\"round\" aria-hidden=\"true\"><path d=\"M12 4v16M8 20h8M5 7h14M5 7l-2.5 6a2.5 2.5 0 0 0 5 0zM19 7l-2.5 6a2.5 2.5 0 0 0 5 0z\"/></svg>",
    ai: "<svg viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.7\" stroke-linecap=\"round\" stroke-linejoin=\"round\" aria-hidden=\"true\"><path d=\"M12 3.5 13.8 9 19.5 10.8 13.8 12.6 12 18.5 10.2 12.6 4.5 10.8 10.2 9z\"/></svg>",
    person: "<svg viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.7\" stroke-linecap=\"round\" stroke-linejoin=\"round\" aria-hidden=\"true\"><circle cx=\"12\" cy=\"8\" r=\"3.5\"/><path d=\"M5 20a7 7 0 0 1 14 0\"/></svg>",
    quote: "<svg viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.7\" stroke-linecap=\"round\" stroke-linejoin=\"round\" aria-hidden=\"true\"><path d=\"M9.5 7H6.5A1.5 1.5 0 0 0 5 8.5v3A1.5 1.5 0 0 0 6.5 13H9v1.5A2.5 2.5 0 0 1 6.5 17M19 7h-3a1.5 1.5 0 0 0-1.5 1.5v3A1.5 1.5 0 0 0 16 13h2.5v1.5A2.5 2.5 0 0 1 16 17\"/></svg>",
    lab: "<svg viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.7\" stroke-linecap=\"round\" stroke-linejoin=\"round\" aria-hidden=\"true\"><path d=\"M9 3h6M10 3v6.5L4.8 18.2A1.8 1.8 0 0 0 6.4 21h11.2a1.8 1.8 0 0 0 1.6-2.8L14 9.5V3M7.4 15h9.2\"/></svg>",
    settings: "<svg viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.7\" stroke-linecap=\"round\" stroke-linejoin=\"round\" aria-hidden=\"true\"><path d=\"M4 6h10M18 6h2M4 12h4M12 12h8M4 18h12\"/><circle cx=\"16\" cy=\"6\" r=\"2\"/><circle cx=\"10\" cy=\"12\" r=\"2\"/><circle cx=\"18\" cy=\"18\" r=\"2\"/></svg>",
    info: "<svg viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.7\" stroke-linecap=\"round\" stroke-linejoin=\"round\" aria-hidden=\"true\"><circle cx=\"12\" cy=\"12\" r=\"9\"/><path d=\"M12 11v5M12 8h.01\"/></svg>",
    clock: "<svg viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.7\" stroke-linecap=\"round\" stroke-linejoin=\"round\" aria-hidden=\"true\"><circle cx=\"12\" cy=\"12\" r=\"9\"/><path d=\"M12 7.5V12l3 2\"/></svg>",
    shelf: "<svg viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.7\" stroke-linecap=\"round\" stroke-linejoin=\"round\" aria-hidden=\"true\"><rect x=\"3\" y=\"4\" width=\"18\" height=\"5\" rx=\"1.5\"/><path d=\"M5 9v9.5A1.5 1.5 0 0 0 6.5 20h11a1.5 1.5 0 0 0 1.5-1.5V9M10 13h4\"/></svg>",
  };
  globalThis.SafeShelfPanels = P;
})();
