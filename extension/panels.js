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
      const icon = { verified: "✅", mismatch: "⛔", unknown: "❔" };
      return vm("Safety marks", (d.checks || []).map((c) => ({
        icon: icon[c.result] || "❔",
        text: `${c.authority}${c.number ? " " + c.number : ""}: ` + (c.result === "mismatch"
          ? `the listing says ${c.claimed_value ?? "?"}, the registry says ${c.registry_value ?? "?"}${c.field ? ` (${c.field.replace("_", " ")})` : ""}`
          : c.result === "verified" ? "matches the official registry" : c.reason || "could not be verified"),
        sub: c.checked_at ? `Checked ${day(c.checked_at)}` : undefined,
        link: c.registry_record_url,
      })), "No safety marks were found on this product to check.");
    },
    relationships(d) {
      return vm("Copies and related products", (d.relationships || []).map((r) => ({
        icon: r.status === "verified" ? "✅" : "❔",
        text: `${REL[r.relationship] || r.relationship}: ${r.target_id}${pct(r.confidence)}`,
        sub: [r.status === "verified" ? "Verified" : "Not verified yet", ev(r.evidence_ids)].filter(Boolean).join(" · "),
      })), "No copies or related products are known for this product.");
    },
    duplicates(d) {
      return vm("Copies found by AI", (d.matches || []).map((m) => ({
        icon: m.status === "verified" ? "✅" : "❔",
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
      const rows = (d.events || []).map((e) => ({ icon: e.change_type === "hazard_signal" ? "⚠️" : "•", text: e.summary, sub: [day(e.at), e.actor, ev(e.evidence_ids)].filter(Boolean).join(" · ") }));
      (d.recalls || []).forEach((r) => rows.unshift({ icon: "⛔", text: `Recall: ${r.title || r.recall_id || JSON.stringify(r)}`, sub: day(r.date) }));
      return vm("Product history", rows, "Nothing recorded yet for this product.");
    },
    alternatives(d) {
      return vm("Safer options", (d.alternatives || []).map((a) => ({
        icon: a.seller_authorised ? "✅" : "❔",
        text: `${a.reason || REL[a.relationship] || a.product_id}`,
        sub: [a.seller, rupees(a.price), a.hazard_reports === 0 ? "no hazard reports" : a.hazard_reports != null ? `${a.hazard_reports} hazard reports` : "", a.certifications_valid ? "certifications valid" : ""].filter(Boolean).join(" · "),
        link: a.url,
      })), "No safer genuine option was found.");
    },
    product(d) {
      const rows = [
        d.brand && { icon: "•", text: `Brand: ${d.brand}` }, d.model && { icon: "•", text: `Model: ${d.model}` },
        d.category && { icon: "•", text: `Category: ${String(d.category).replace("_", " ")}` }, d.gtin && { icon: "•", text: `GTIN: ${d.gtin}` },
        ...Object.entries(d.attributes || {}).map(([k, v]) => ({ icon: "•", text: `${k.replace("_", " ")}: ${v}` })),
        d.verification_status && { icon: "•", text: `Identity: ${d.verification_status}`, sub: d.identity_version != null ? `version ${d.identity_version}` : undefined },
      ].filter(Boolean);
      return vm("Product details", rows, "No details are stored for this product.");
    },
    identify(d) {
      return vm("How SafeShelf identified it", [
        { icon: d.identity_status === "verified" ? "✅" : "❔", text: `${[d.brand, d.model].filter(Boolean).join(" ") || d.product_id}`, sub: `Status: ${d.identity_status || "unknown"}${pct(d.confidence)}` },
        ...(d.certifications_claimed || []).map((c) => ({ icon: "•", text: `The listing claims: ${c}` })),
      ].filter((r) => r.text), "Could not identify this listing.");
    },
    safety(d) {
      const level = { green: "✅", amber: "⚠️", red: "⛔", not_enough_evidence: "❔" };
      const rows = [{ icon: level[d.verdict] || "❔", text: `Verdict: ${String(d.verdict).replace(/_/g, " ")}`, sub: d.reviews_checked != null ? `${d.reviews_checked} reviews checked` : undefined },
        { icon: d.official_status?.recalled ? "⛔" : "✅", text: d.official_status?.recalled ? "Officially recalled" : `Not recalled (checked ${(d.official_status?.checked || []).join(", ") || "no registries"})` },
        ...(d.ai_findings || []).map((f) => ({ icon: "⚠️", text: `${f.independent_reports ?? "?"} reports of ${f.mechanism || f.hazard_type} (${String(f.status).replace(/_/g, " ")})`, sub: [f.severity && `severity ${f.severity}`, f.with_photos != null && `${f.with_photos} with photos`, ev(f.evidence_ids)].filter(Boolean).join(" · ") }))];
      return vm("Safety findings", rows, "");
    },
    report(d) {
      return vm("Report received", [{ icon: "✅", text: `Report ${d.report_id} ${d.status}`, sub: d.pii_masked ? "Personal details were masked automatically." : undefined }], "");
    },
    catalogScan(d) {
      const rows = (d.results || []).map((r) => ({ icon: r.finding === "certification_mismatch" ? "⛔" : "⚠️", text: `Row ${r.row}: ${r.listing_title}`, sub: [String(r.finding).replace(/_/g, " "), r.status && String(r.status).replace(/_/g, " "), ev(r.evidence_ids)].filter(Boolean).join(" · ") }));
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
        for (const [method, m] of Object.entries(methods)) rows.push({ icon: method === "safeshelf" ? "🛡" : "•", text: NAME[method] || method.replace(/_/g, " "), sub: line(m) });
      }
      if (d.safeshelf_on_test_half) {
        rows.push({ heading: "Held-out test half (the unbiased figure)" });
        rows.push({ icon: "🧪", text: "SafeShelf on recalls it was not tuned on", sub: line(d.safeshelf_on_test_half) });
      }
      if (d.safeshelf_params) rows.push({ icon: "⚙️", text: "SafeShelf alarm settings (tuned on the train half)", sub: Object.entries(d.safeshelf_params).map(([k, v]) => `${k.replace(/_/g, " ")}: ${v}`).join(" · ") });
      if ((d.caveats || []).length) { rows.push({ heading: "Read this before quoting the numbers" }); d.caveats.forEach((c) => rows.push({ icon: "ℹ️", text: c })); }
      if ((d.per_recall || []).length) {
        rows.push({ heading: `Each recall (${d.per_recall.length})` });
        const lead = (x) => (x == null ? "missed" : `${x} days early`);
        d.per_recall.forEach((r) => rows.push({ icon: r.safeshelf_lead_days != null ? "✅" : "•", text: `${r.title} (${r.recall_date})`,
          sub: `${r.split} · ${r.listings} listings · ${r.reviews_before_recall} reviews before the recall · keyword ${lead(r.keyword_rules_lead_days)} · Gemini ${lead(r.gemini_alone_lead_days)} · SafeShelf ${lead(r.safeshelf_lead_days)}` }));
      }
      if (Array.isArray(d.controls)) rows.push({ heading: `Controls: ${d.controls.length} products never recalled, used to count false alarms` });
      return { title: "SafeShelfBench", rows, note: d.generated_at ? `Generated ${day(d.generated_at)}` : "Not generated yet" };
    },
  };
  globalThis.SafeShelfPanels = P;
})();
