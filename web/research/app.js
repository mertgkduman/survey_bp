/* Static evidence browser and package exporter. Simulations execute in Python. */
(function () {
  "use strict";
  const $ = id => document.getElementById(id);
  const copy = value => JSON.parse(JSON.stringify(value));
  const S = {catalog: null, contract: null, template: null, series: [], selected: new Set(),
    custom: null, draft: null, spec: null, valid: false, unsupported: "", metric: "ler"};
  const colors = ["#067d79", "#b17415", "#5065a8", "#b04844", "#658641", "#895a96"];
  const idOf = record => record.id || record.experiment_id || record.decoder_id || record.code_id || record.circuit_id || record.dataset_id || record.paper_id;
  const titleOf = record => record.title || record.label || record.name || idOf(record);
  const known = value => typeof value === "number" && Number.isFinite(value);
  const text = value => value == null || value === "" ? "Unavailable" : String(value);
  function fmt(value) { return known(value) ? (value === 0 ? "0" : Math.abs(value) < .001 ? value.toExponential(3) : Number(value.toPrecision(6)).toString()) : text(value); }
  const count = value => known(value) ? value.toLocaleString("en-US") : "Not reported";
  function el(tag, attrs = {}, content) {
    const node = document.createElement(tag);
    for (const [name, value] of Object.entries(attrs)) {
      if (name === "class") node.className = value;
      else if (name === "text") node.textContent = value;
      else node.setAttribute(name, value);
    }
    if (content != null) node.textContent = content;
    return node;
  }
  function replace(node, children = []) { node.replaceChildren(...children); }
  function save(filename, content, type = "application/json") {
    const url = URL.createObjectURL(content instanceof Blob ? content : new Blob([content], {type}));
    const link = el("a", {href: url, download: filename}); document.body.append(link); link.click(); link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  async function digest(content) {
    const bytes = typeof content === "string" ? new TextEncoder().encode(content) : content;
    return [...new Uint8Array(await crypto.subtle.digest("SHA-256", bytes))].map(x => x.toString(16).padStart(2, "0")).join("");
  }
  async function json(path) { const response = await fetch(path, {cache: "no-cache"}); if (!response.ok) throw Error(`${path}: HTTP ${response.status}`); return response.json(); }
  function assetURL(asset) {
    if (!asset || !asset.url || !["tracked", "available", "repository", "tracked_summary"].includes(asset.availability)) return null;
    const url = new URL(asset.url.startsWith("http") ? asset.url : "../../" + asset.url.replace(/^\/+/, ""), location.href);
    return ["https:", "http:"].includes(url.protocol) ? url.href : null;
  }
  async function assetBytes(asset) {
    const url = assetURL(asset); if (!url) throw Error("This input is not downloadable through the repository route.");
    const response = await fetch(url); if (!response.ok) throw Error(`Input unavailable: ${asset.path}`);
    const bytes = new Uint8Array(await response.arrayBuffer());
    if (asset.sha256 && await digest(bytes) !== asset.sha256) throw Error(`Checksum mismatch: ${asset.path}. Rebuild or refresh the catalog.`);
    return bytes;
  }
  function assetList(assets) {
    const box = el("div", {class: "asset-links"});
    for (const asset of assets.filter(Boolean)) {
      const url = assetURL(asset);
      if (url) box.append(el("a", {href: url, target: "_blank", rel: "noopener", download: ""}, asset.label || asset.path));
      else {
        const missing = el("span", {class: "muted"}, `${asset.label || asset.kind}: ${asset.availability || "unavailable"}`);
        if (asset.local_storage_path) missing.title = `Local storage: ${asset.local_storage_path}\nSHA-256: ${asset.sha256 || "not supplied"}`;
        box.append(missing);
      }
    }
    return box;
  }
  function route(section) {
    if (section === "main-content") { $("main-content").focus(); return; }
    if (!$(section)?.classList.contains("panel")) section = "papers";
    for (const panel of document.querySelectorAll("main > .panel")) panel.hidden = panel.id !== section;
    document.querySelector(".intro-card").hidden = section !== "papers";
    for (const link of document.querySelectorAll("[data-nav]")) {
      if (link.dataset.nav === section) link.setAttribute("aria-current", "page"); else link.removeAttribute("aria-current");
    }
    if (location.hash !== "#" + section) history.replaceState(null, "", "#" + section);
    window.scrollTo({top: 0, behavior: "instant"});
  }
  function addLibraries() {
    const nav = document.querySelector(".nav-list");
    for (const [id, title] of [["decoders", "Decoder specifications"], ["codes", "Codes & channels"]]) {
      const link = el("a", {href: "#" + id, "data-nav": id}, title); nav.insertBefore(link, nav.querySelector('[data-nav="builder"]'));
      const section = el("section", {id, class: "panel", "aria-label": title});
      section.append(el("h2", {}, title), el("div", {id: id + "-library"}));
      $("builder").before(section);
    }
  }
  function selectOptions(select, records, empty, wanted) {
    const previous = wanted !== undefined ? wanted : select.value;
    replace(select, [el("option", {value: ""}, empty), ...records.map(item => el("option", {value: idOf(item)}, titleOf(item)))]);
    select.value = records.some(item => String(idOf(item)) === previous) ? previous : "";
    return select.value;
  }
  const record = (kind, id) => S.catalog[kind].find(item => String(idOf(item)) === String(id));
  function paperExperiments(paper) { return S.catalog.experiments.filter(item => !paper || (item.paper_ids || []).includes(paper)); }
  function experimentDatasets(experiment) { return experiment ? experiment.dataset_ids || [experiment.dataset_id].filter(Boolean) : null; }
  function currentSeries() {
    const paper = $("result-paper").value, experiment = record("experiments", $("result-experiment").value);
    const datasetIds = experimentDatasets(experiment), dataset = $("result-dataset").value;
    return S.series.filter(item => (!paper || item.paper_ids.includes(paper)) && (!datasetIds || datasetIds.includes(item.dataset_id)) && (!dataset || item.dataset_id === dataset) && (!$("result-code").value || item.code_id === $("result-code").value) && (!$("result-decoder").value || item.decoder_id === $("result-decoder").value));
  }
  function filters(changed) {
    const paper = $("result-paper").value;
    if (changed === "paper") { $("result-experiment").value = ""; $("result-dataset").value = ""; $("result-code").value = ""; $("result-decoder").value = ""; }
    const experiments = paperExperiments(paper);
    selectOptions($("result-experiment"), experiments, "All registered experiments");
    const selectedExperiment = record("experiments", $("result-experiment").value), allowed = experimentDatasets(selectedExperiment);
    if (changed === "experiment") { $("result-dataset").value = ""; $("result-code").value = ""; $("result-decoder").value = ""; }
    const datasets = S.catalog.datasets.filter(item => (!paper || item.paper_id === paper || item.paper_ids?.includes(paper)) && (!allowed || allowed.includes(item.dataset_id)));
    selectOptions($("result-dataset"), datasets, "All datasets in this selection");
    if (changed === "dataset") { $("result-code").value = ""; $("result-decoder").value = ""; }
    const ids = new Set(datasets.filter(d => !$("result-dataset").value || d.dataset_id === $("result-dataset").value).map(d => d.dataset_id));
    const candidates = S.series.filter(item => ids.has(item.dataset_id));
    const codeIds = new Set(candidates.map(item => item.code_id));
    selectOptions($("result-code"), S.catalog.codes.filter(item => codeIds.has(item.code_id)), "All available codes");
    if (changed === "code") $("result-decoder").value = "";
    const decoderIds = new Set(candidates.filter(item => !$("result-code").value || item.code_id === $("result-code").value).map(item => item.decoder_id));
    selectOptions($("result-decoder"), S.catalog.decoders.filter(item => decoderIds.has(item.decoder_id)), "Compare all available decoders");
    S.selected = new Set(currentSeries().map(item => item.key));
    renderResults();
  }
  function renderPapers() {
    const search = $("paper-search").value.toLowerCase(), status = $("paper-status").value;
    const list = S.catalog.papers.filter(item => JSON.stringify(item).toLowerCase().includes(search) && (!status || item.kind === status));
    replace($("paper-list")); $("paper-count").textContent = `${list.length} papers / local studies`;
    for (const paper of list) {
      const card = el("article", {class: "paper-card"}), body = el("div");
      body.append(el("h3", {}, paper.title), el("p", {}, paper.identity), el("span", {class: "tag"}, paper.kind === "local_study" ? "Local study · unpublished" : "External paper"), el("p", {}, paper.registered_scope || "No numerical result registered."));
      if (paper.source_url) body.append(el("a", {href: paper.source_url, target: "_blank", rel: "noopener"}, "Open source paper"));
      const go = el("button", {type: "button", class: "button button-quiet", "aria-label": "Explore " + paper.title}, "Explore registered work");
      go.onclick = () => { $("result-paper").value = paper.paper_id; filters("paper"); route("results"); $("result-experiment").focus(); };
      card.append(body, go); $("paper-list").append(card);
    }
  }
  function details() {
    const box = $("selection-details"); replace(box);
    const series = currentSeries(), datasets = [...new Set(series.map(item => item.dataset_id))].map(id => record("datasets", id));
    const decoder = record("decoders", $("result-decoder").value);
    const experiment = record("experiments", $("result-experiment").value);
    box.append(el("h3", {}, experiment ? titleOf(experiment) : "Configuration and evidence"));
    for (const data of datasets) {
      box.append(el("p", {}, `${data.label}: ${data.evidence_status}. ${data.caveat || ""}`));
      if (data.failure_definition || data.denominator_definition || data.uncertainty_method) box.append(el("p", {class: "muted"}, [data.failure_definition, data.denominator_definition, data.uncertainty_method].filter(Boolean).join(" · ")));
      box.append(assetList(data.assets || []));
      const raw = series.filter(item => item.dataset_id === data.dataset_id).flatMap(item => item.points.map(p => p.raw_asset).filter(Boolean));
      const uniqueRaw = [...new Map(raw.map(asset => [asset.path, asset])).values()];
      if (uniqueRaw.length) { const rawBox = el("details"); rawBox.append(el("summary", {}, `Per-shot raw data · ${uniqueRaw.length} registered files`), assetList(uniqueRaw)); box.append(rawBox); }
      else if (!(data.assets || []).some(a => /jsonl|ledger|raw/.test(a.kind || ""))) box.append(el("p", {class: "muted"}, "Per-shot raw data: no download is registered for this dataset. Retained summaries and source instructions remain available."));
    }
    if (decoder) {
      box.append(el("h3", {}, /unavailable/.test(decoder.configuration?.settings_status || "") ? "Available specification provenance" : "Frozen decoder specification and effective settings"), el("pre", {id: "frozen-spec", tabindex: "0", "aria-label": "Frozen decoder specification"}, JSON.stringify(decoder.configuration || decoder.effective_settings || decoder, null, 2)));
      const download = el("button", {type: "button", id: "download-frozen-spec", class: "button button-quiet"}, decoder.configuration?.settings_status === "exact_policy_file" ? "Export exact specification" : "Export original configuration source");
      download.onclick = () => exportDecoder(decoder).catch(showError);
      box.append(download, assetList([decoder.asset, ...(decoder.assets || [])]));
      const receipt = el("button", {type: "button", id: "download-configuration-receipt", class: "button button-quiet"}, "Download effective configuration receipt");
      receipt.onclick = () => save("decoder-receipt.json", JSON.stringify({schema: "research-decoder-receipt-v1", ...decoder}, null, 2) + "\n"); box.append(receipt);
      const extend = el("button", {type: "button", id: "extend-selected", class: "button button-quiet"}, "Create a new experiment from these settings");
      extend.onclick = () => useDecoder(decoder, $("result-code").value); box.append(extend);
    } else if (series.length) box.append(el("p", {class: "muted"}, "Choose one decoder to inspect and export its complete frozen specification."));
    if (experiment?.reproduction_recipe) {
      box.append(el("h3", {}, "Original study entry point"), el("pre", {}, JSON.stringify(experiment.reproduction_recipe, null, 2)));
      if (experiment.reproduction_recipe.kind === "registered_study") {
        const download = el("button", {type: "button", id: "download-registered-workflow", class: "button button-quiet"}, "Download original registered workflow");
        download.onclick = () => downloadRegistered(experiment).catch(showError); box.append(download);
      }
    }
    if (!series.length) box.append(el("p", {}, "This selection has no registered numerical result. Its paper remains indexed without an invented curve."));
  }
  function showError(error) { $("form-summary").textContent = error.message; $("form-summary").className = "form-summary error"; }
  async function exportDecoder(decoder) {
    if (decoder.asset && assetURL(decoder.asset)) {
      const bytes = await assetBytes(decoder.asset); save(decoder.asset.path.split("/").pop(), bytes, "application/octet-stream");
    } else save(`${decoder.decoder_id}.json`, JSON.stringify(decoder.configuration || decoder, null, 2) + "\n");
  }
  function valueFor(point) { return S.metric === "work" ? point.mean_work : S.metric === "runtime" ? point.mean_seconds : point.y; }
  function isBound(point) { return /bound|upper/i.test(point.status || "") || (point.is_rate_estimate === false && /bound|upper/i.test(point.source_point_type || "")) || (point.failures === 0 && point.y === 0 && known(point.ci_high)); }
  function plotValue(point) { return S.metric === "ler" && isBound(point) && point.y === 0 ? point.ci_high : valueFor(point); }
  function rows() { return currentSeries().filter(item => S.selected.has(item.key)).flatMap(series => series.points.filter(point => known(point.x) && known(valueFor(point))).map(point => ({series, point}))); }
  function renderResults() {
    const series = currentSeries(), legend = $("series-legend"); replace(legend);
    for (let i = 0; i < series.length; i++) {
      const item = series[i], label = el("label"), input = el("input", {type: "checkbox", value: item.key}); input.checked = S.selected.has(item.key);
      input.onchange = () => { if (input.checked) S.selected.add(item.key); else S.selected.delete(item.key); renderTable(); renderPlot(); };
      label.append(input, el("span", {style: `color:${colors[i % colors.length]}`}, `${titleOf(record("decoders", item.decoder_id) || item)} · ${item.evidence}`)); legend.append(label);
    }
    const workUnits = new Set(series.flatMap(item => item.points.filter(p => known(p.mean_work)).map(p => p.work_unit)));
    selectOptions($("metric-select"), [{id: "ler", label: "Logical failure probability"}, ...(workUnits.size === 1 ? [{id: "work", label: "Mean work · " + [...workUnits][0]}] : []), {id: "runtime", label: "Mean reported time (s; scope per row)"}], "Choose a metric", S.metric);
    if (!$("metric-select").value) S.metric = $("metric-select").value = "ler";
    $("metric-select").disabled = !series.length;
    details(); renderTable(); renderPlot();
  }
  function renderTable() {
    const body = $("result-table").querySelector("tbody"); replace(body);
    for (const {series, point: p} of rows()) {
      const tr = el("tr", {"data-code": series.code_id, "data-decoder": series.decoder_id, "data-dataset": series.dataset_id});
      const estimator = p.estimator || p.sampling_method || p.estimation_method || "";
      const weighted = /importance|weighted/.test(estimator);
      const uncertainty = p.ci_method || p.uncertainty_method || record("datasets", series.dataset_id).uncertainty_method || "Method not supplied";
      const interval = known(p.ci_low) && known(p.ci_high) ? `[${fmt(p.ci_low)}, ${fmt(p.ci_high)}]` : isBound(p) && known(p.ci_high) ? `Upper ≤ ${fmt(p.ci_high)}` : "Unavailable";
      const cells = [series.label, fmt(p.x), S.metric === "ler" ? (estimator || "Block LER") : S.metric,
        (isBound(p) && S.metric === "ler" ? "≤ " : "") + fmt(plotValue(p)), weighted ? `${count(p.raw_samples)} raw draws` : count(p.n), weighted ? `${count(p.raw_failures)} raw events` : count(p.failures), `${count(p.type_i)} / ${count(p.type_ii)}`,
        `${interval} · ${known(p.confidence_level) ? p.confidence_level * 100 + "% · " : ""}${uncertainty}`, known(p.mean_work) ? `${fmt(p.mean_work)} ${p.work_unit || "unit unavailable"}` : "Unavailable",
        known(p.mean_seconds) ? `${fmt(p.mean_seconds)} s · ${p.runtime_scope || "see source timing boundary"}` : "Unavailable", `${series.evidence} · ${p.status || ""}`, /importance|weighted/.test(estimator) ? "Weighted estimate; counts are raw proposal draws" : "Retained summary"];
      for (const cell of cells) tr.append(el("td", {}, cell)); body.append(tr);
    }
    if (!body.children.length) { const tr = el("tr"); tr.append(el("td", {colspan: 12}, "No measured points for the current selection and metric.")); body.append(tr); }
    $("export-visible-results").disabled = !rows().length;
  }
  function svg(tag, attrs, content) { const n = document.createElementNS("http://www.w3.org/2000/svg", tag); for (const [k, v] of Object.entries(attrs || {})) n.setAttribute(k, v); if (content != null) n.textContent = content; return n; }
  function renderPlot() {
    const chart = $("result-plot"), data = rows().filter(r => known(plotValue(r.point)) && (S.metric !== "ler" || plotValue(r.point) > 0));
    replace(chart, [svg("title", {id: "plot-title"}, "Retained experiment results")]);
    if (!data.length) { chart.append(svg("text", {x: 420, y: 180, "text-anchor": "middle", class: "plot-label"}, "No plottable measured points in this selection")); $("plot-caption").textContent = "No curve is inferred for missing results."; return; }
    const log = S.metric === "ler", W = 840, H = 380, left = 78, right = 22, top = 25, bottom = 58;
    let xmin = Math.min(...data.map(r => r.point.x)), xmax = Math.max(...data.map(r => r.point.x));
    if (xmin === xmax) { xmin -= .005; xmax += .005; }
    let ys = data.map(r => plotValue(r.point));
    if (log) ys = data.flatMap(r => [plotValue(r.point), r.point.ci_low, r.point.ci_high].filter(v => known(v) && v > 0));
    let ymin = Math.min(...ys), ymax = Math.max(...ys);
    if (log) { ymin = Math.floor(Math.log10(ymin)); ymax = Math.ceil(Math.log10(ymax)); if (ymin === ymax) ymax++; }
    else if (ymin === ymax) { ymin = 0; ymax = ymax || 1; }
    const x = p => left + (p - xmin) / (xmax - xmin) * (W - left - right);
    const y = p => H - bottom - ((log ? Math.log10(p) : p) - ymin) / (ymax - ymin) * (H - top - bottom);
    for (let i = 0; i <= 4; i++) {
      const v = xmin + (xmax - xmin) * i / 4, cx = x(v);
      chart.append(svg("line", {x1: cx, y1: top, x2: cx, y2: H - bottom, class: "plot-grid"}), svg("text", {x: cx, y: H - bottom + 21, "text-anchor": "middle", class: "plot-label"}, fmt(v)));
    }
    const ticks = log ? Array.from({length: Math.min(10, ymax - ymin + 1)}, (_, i) => ymin + i * Math.max(1, Math.ceil((ymax - ymin) / 9))) : [ymin, (ymin + ymax) / 2, ymax];
    for (const v of ticks) { const raw = log ? 10 ** v : v, cy = y(raw); chart.append(svg("line", {x1: left, y1: cy, x2: W - right, y2: cy, class: "plot-grid"}), svg("text", {x: left - 10, y: cy + 4, "text-anchor": "end", class: "plot-label"}, log ? `10^${v}` : fmt(v))); }
    const series = currentSeries();
    for (let i = 0; i < series.length; i++) {
      const item = series[i], points = data.filter(r => r.series.key === item.key).map(r => r.point).sort((a, b) => a.x - b.x), color = colors[i % colors.length];
      if (!points.length) continue;
      chart.append(svg("path", {d: points.map((p, j) => `${j ? "L" : "M"}${x(p.x)},${y(plotValue(p))}`).join(" "), stroke: color, class: /source|transcription/.test(item.evidence) ? "plot-line plot-source" : "plot-line"}));
      for (const p of points) {
        const cx = x(p.x), cy = y(plotValue(p)), bound = log && isBound(p);
        if (log && known(p.ci_low) && p.ci_low > 0 && known(p.ci_high)) chart.append(svg("line", {x1: cx, y1: y(p.ci_low), x2: cx, y2: y(p.ci_high), stroke: color, class: "plot-error"}));
        const description = `${item.label}; p=${fmt(p.x)}; ${bound ? "interval upper limit " : "estimate "}${fmt(plotValue(p))}; ${count(p.failures)} failures, ${count(p.n)} samples; ${p.estimator || p.sampling_method || item.evidence}`;
        const mark = bound ? svg("path", {d: `M${cx-5},${cy-4}L${cx+5},${cy-4}L${cx},${cy+5}Z`, fill: "white", stroke: color}) : svg("circle", {cx, cy, r: 4.5, fill: color});
        mark.setAttribute("class", "plot-point"); mark.setAttribute("tabindex", "0"); mark.setAttribute("role", "button"); mark.setAttribute("aria-label", description); mark.append(svg("title", {}, description));
        const describe = () => { $("plot-caption").textContent = description; }; mark.onfocus = describe; mark.onclick = describe; mark.onkeydown = event => { if (["Enter", " "].includes(event.key)) { event.preventDefault(); describe(); } }; chart.append(mark);
      }
    }
    chart.append(svg("text", {x: 430, y: H - 12, "text-anchor": "middle", class: "plot-label"}, "Physical error probability p"), svg("text", {x: 18, y: 175, transform: "rotate(-90 18 175)", "text-anchor": "middle", class: "plot-label"}, log ? "Logical failure probability (log scale)" : S.metric));
    $("plot-caption").textContent = `${data.length} retained points. Dashed: source values. Open triangles: bounds, not observed nonzero rates. Focus a point for details.`;
    $("plot-description").textContent = $("plot-caption").textContent;
  }
  function library() {
    const decoders = $("decoders-library"), codes = $("codes-library");
    const channels = el("div"); channels.append(el("h3", {}, "Noise models"));
    for (const model of S.catalog.channels || []) channels.append(el("h4", {}, model.label), el("p", {}, model.definition), el("p", {class: "field-help"}, model.decoder_prior));
    codes.after(channels);
    for (const [box, choices, kind] of [[decoders, S.catalog.decoders, "decoder"], [codes, S.catalog.codes, "code"]]) {
      const select = el("select", {id: `library-${kind}`, "aria-label": `Registered ${kind}`}), body = el("div");
      selectOptions(select, choices, `Select a registered ${kind}`); replace(box, [select, body]);
      select.onchange = () => { replace(body); const item = choices.find(r => idOf(r) === select.value); if (!item) return;
        body.append(el("h3", {}, titleOf(item)), el("pre", {}, JSON.stringify(item.configuration || item, null, 2)), assetList([item.asset, ...(item.assets || [])]));
        if (kind === "decoder") { const go = el("button", {type: "button", class: "button"}, "Use as a new experiment"); go.onclick = () => useDecoder(item); body.append(go); }
        const retained = S.series.find(series => kind === "decoder" ? series.decoder_id === item.decoder_id : series.code_id === item.code_id);
        if (retained) { const inspect = el("button", {type: "button", class: "button button-quiet"}, "Inspect registered results");
          inspect.onclick = () => { $("result-paper").value = retained.paper_ids[0]; filters("paper");
            $("result-dataset").value = retained.dataset_id; filters("dataset"); $("result-code").value = retained.code_id; filters("code");
            if (kind === "decoder") { $("result-decoder").value = retained.decoder_id; filters("decoder"); } route("results"); };
          body.append(inspect);
        }
      };
    }
  }
  function defaultDraft() {
    return {id: "my-decoder-experiment", family: "binary_css", variant: "plain", preset: "", code: "three-qubit", codeText: JSON.stringify({hx:[[1,1,0]],hz:[[0,0,1]],lx:[[1,0,0]],lz:[[1,1,0]]}, null, 2),
      channel: "depolarizing", rates: "0.06", prior: "matched", p0: .06, shots: S.contract.defaults.sampling.shots, seed: 7, start: 0, iterations: 100, maxshots: 100000,
      rule: "sum_product", version: "v2", policy: false, format: "float64", scale: 16, scope: "scalar_edges", coefficients: "float64", damping: 0, alpha: 1, beta: 0,
      hard: "min_llr", shortcut: true, stop: true, rounds: 2, perRound: 10, epsilon: 1e-10, circuit: "", circuitText: "R 0\nX_ERROR(0.1) 0\nM 0\nDETECTOR rec[-1]\nOBSERVABLE_INCLUDE(0) rec[-1]\n", tie: "zero"};
  }
  function field(container, key, label, options, help, type = "text") {
    const wrap = el("label", {for: "build-" + key, class: type === "textarea" ? "full-width" : ""}, label);
    let input;
    if (options) { input = el("select", {id: "build-" + key}); for (const item of options) { const val = Array.isArray(item) ? item[0] : item; input.append(el("option", {value: String(val)}, Array.isArray(item) ? item[1] : String(item))); } }
    else input = el(type === "textarea" ? "textarea" : "input", {id: "build-" + key, ...(type === "textarea" ? {rows: 8, spellcheck: "false"} : {type, ...(type === "number" ? {step: "any"} : {})})});
    input.value = String(S.draft[key]); input.disabled = Boolean(S.custom);
    input.onchange = () => { const old = S.draft[key]; S.draft[key] = type === "number" ? Number(input.value) : ["policy", "stop", "shortcut"].includes(key) ? input.value === "true" : input.value;
      if (key === "preset") { useDecoder(record("decoders", input.value)); return; }
      if (key === "family") { S.draft.rule = input.value === "circuit_dem_bp" ? "spa" : "sum_product"; S.draft.variant = "plain"; S.draft.hard = input.value === "bp4" ? "strict_pauli" : "min_llr"; }
      if (key === "rule" && input.value === "min_sum") { S.draft.policy = S.draft.family !== "circuit_dem_bp"; S.draft.format = "int8"; S.draft.scope = "scalar_edges"; }
      if (key === "family" || key === "policy" || key === "code" || key === "channel" || key === "prior" || key === "variant" || key === "format") renderBuilder();
      else preview();
      if (old !== S.draft[key]) S.valid = false;
    };
    wrap.append(input); if (help) wrap.append(el("span", {class: "field-help"}, help)); container.append(wrap); return input;
  }
  function renderBuilder() {
    if (!S.draft) S.draft = defaultDraft(); const d = S.draft, box = $("form-fields"); replace(box);
    field(box, "preset", "Start from a frozen specification", [["", "Custom / current visual configuration"], ...S.catalog.decoders.map(item => [item.decoder_id, item.label || item.decoder_id])], "Importing settings creates a new experiment. Exact historical files remain in Results.");
    field(box, "id", "Experiment label", null, "A content-derived identity is recorded locally; this label is for you.");
    field(box, "family", "Decoder family / regime", [["binary_css", "Binary CSS code capacity"], ["bp4", "Joint Pauli BP4 code capacity"], ["circuit_dem_bp", "Circuit: Stim / Sinter BP"]]);
    if (d.family === "circuit_dem_bp") {
      field(box, "circuit", "Circuit input", [["", "Custom inline Stim text"], ...S.catalog.circuits.map(item => [item.circuit_id, item.label])]);
      field(box, "circuitText", "Stim circuit text", null, "Noise is embedded in the circuit. Stim parses and validates its detector model locally.", "textarea");
      field(box, "rule", "Circuit check rule", [["spa", "Sum-product"], ["min_sum", "Min-sum"]]); field(box, "tie", "Zero-belief tie rule", ["zero", "one"]);
      box.append(el("p", {class: "field-help full-width"}, "Circuit adapter: flooding, float64 v1, decompose_errors=false. Damping, alternate precision, and Relay/Beam policies are unsupported."));
    } else {
      field(box, "code", "Code", [["custom", "Custom CSS matrices"], ...S.catalog.codes.filter(item => item.code_id !== "gb46").map(item => [item.code_id, item.label])]);
      if (d.code === "custom") field(box, "codeText", "CSS input JSON", null, "Binary hx/hz with equal n, commuting checks, optional paired lx/lz. Full validation repeats in Python.", "textarea");
      field(box, "channel", "Physical noise", [["depolarizing", "Depolarizing: X/Y/Z each p/3"], ["x_only", "X-only independent channel"]]);
      field(box, "rates", "Physical error probabilities", null, "Comma-separated sweep, for example 0.04, 0.06, 0.08.");
      field(box, "prior", "Decoder prior", [["matched", "p₀ follows physical p"], ["fixed", "Freeze p₀ across the sweep"]], "BP4 uses a depolarizing joint prior; binary uses component marginals (p₀ for X-only, 2p₀/3 for depolarizing).");
      if (d.prior === "fixed") field(box, "p0", "Fixed decoder p₀", null, "Sampling p and decoder p₀ remain separate.", "number");
      field(box, "rule", "Check update", [["sum_product", "Sum-product"], ["min_sum", "Min-sum / normalized / offset"]]);
      field(box, "version", "Numerical profile", [["v2", "Canonical v2 base profile"], ["v1", "Frozen float64 v1 · plain SPA only"]]);
      field(box, "policy", "Numerical policy overlay", [[false, "Profile defaults"], [true, "Configure resolution, damping, MS coefficients"]]);
      if (d.family === "bp4") field(box, "variant", "BP4 procedure", [["plain", "Plain BP4"], ["qbpgd", "Q-BPGD · persistent v2 messages"]]);
      if (d.policy) {
        field(box, "format", "Message resolution", S.contract.resolution.formats);
        if (d.format.startsWith("int")) field(box, "scale", "Fixed-point scale s", null, "Step 1/s; symmetric range ±(2^(bits−1)−1)/s; ties to even.", "number");
        field(box, "scope", "Quantization boundary", S.contract.resolution.scopes);
        field(box, "coefficients", "Coefficient resolution", [["float64", "Keep coefficients in float64"], ["same", "Round coefficients in the message resolution"]]);
        field(box, "damping", "V2C damping: old-message weight d", null, "m ← d m_old + (1−d) m_new; effective rounded coefficients are recorded locally.", "number");
        if (d.rule === "min_sum") { field(box, "alpha", "Min-sum scale α", null, "α max(0, min |m| − β)", "number"); field(box, "beta", "Min-sum offset β", null, null, "number"); }
        if (d.family === "bp4") field(box, "hard", "BP4 hard decision", [["min_llr", "Minimum identity-referenced LLR"], ["strict_pauli", "Strict I, X, Z, else Y ladder"]]);
        field(box, "shortcut", "Zero-syndrome shortcut", [[true, "Enabled"], [false, "At least one completed sweep"]]);
      }
      if (d.family === "bp4" && d.variant === "plain") field(box, "stop", "Stopping", [[true, "First syndrome-matching candidate"], [false, "Run the entire iteration cap"]]);
      if (d.family === "bp4" && d.variant === "qbpgd") {
        field(box, "perRound", "Sweeps per decimation round", null, null, "number"); field(box, "rounds", "Maximum rounds", null, "Product with sweeps per round must fit the total iteration cap.", "number"); field(box, "epsilon", "Fixation ε", null, null, "number");
      }
    }
    field(box, "shots", "Shots per rate point", null, "Fixed N; every attempted decode enters the denominator.", "number");
    field(box, "seed", "Sampling seed", null, null, "number"); field(box, "start", "First shot index", null, null, "number");
    field(box, "iterations", "Iteration / total Q-BPGD sweep cap", null, "Binary: cap per X/Z component; BP4: joint sweeps; Q-BPGD: total sweeps.", "number");
    field(box, "maxshots", "Total shot budget", null, "Must cover rate points × shots. Circuit skipped prefix also consumes the budget.", "number");
    if (!$("reset-visual")) { const reset = el("button", {id: "reset-visual", type: "button", class: "button button-quiet"}, "Return to visual builder"); reset.onclick = () => { S.custom = null; S.unsupported = ""; S.draft = defaultDraft(); renderBuilder(); }; $("copy-spec").after(reset); }
    if (!$("download-experiment-json")) { const download = el("button", {id: "download-experiment-json", type: "button", class: "button button-quiet"}, "Download experiment JSON"); download.onclick = () => { preview(); if (S.spec) save("experiment.json", JSON.stringify(S.spec, null, 2) + "\n"); }; document.querySelector(".form-actions").append(download); }
    if (d.family !== "circuit_dem_bp" && !d.policy) box.append(el("p", {class: "field-help full-width"}, d.version === "v2" ? "Without an overlay, the v2 profile uses V2C damping d = 0.1. BP4 uses the strict Pauli decision rule and completes at least one sweep. Enable a policy overlay to choose different values." : "Without an overlay, the frozen v1 numerical safeguards and stopping rules apply."));
    preview();
  }
  function visualSpec() {
    const d = S.draft, circuit = d.family === "circuit_dem_bp", bp4 = d.family === "bp4";
    let code;
    if (!circuit) code = d.code === "custom" ? {kind: "embedded_css", ...JSON.parse(d.codeText)} : {kind: "registered", id: d.code};
    const decoder = circuit ? {family: "circuit_dem_bp", implementation: "canonical_sinter", rule: d.rule, numerical_profile: S.contract.circuit_rule_profiles[d.rule], schedule: "flooding", max_iterations: d.iterations, tie_break: d.tie} :
      {family: d.family, implementation: "compiled", variant: bp4 ? d.variant : "plain", rule: d.rule, numerical_profile: `${bp4 ? "quaternary-bp4" : "binary-spa-flooding"}-f64-${d.version}`, policy: null, schedule: "flooding", stop_on_convergence: bp4 && d.variant === "plain" ? d.stop : true};
    if (!circuit && d.policy) decoder.policy = {version: S.contract.ui_fields.policy.version, check_rule: d.rule,
      resolution: {version: S.contract.ui_fields.policy.resolution_version, format: d.format, scale: d.format.startsWith("int") ? d.scale : null, scope: d.scope, coefficients: d.coefficients}, damping: d.damping, alpha: d.rule === "sum_product" ? 1 : d.alpha, beta: d.rule === "sum_product" ? 0 : d.beta,
      hard_decision: bp4 ? d.hard : "min_llr", zero_syndrome_shortcut: d.shortcut};
    if (bp4 && d.variant === "qbpgd") decoder.qbpgd = {iterations_per_round: d.perRound, epsilon: d.epsilon, round_limit: d.rounds};
    return {schema: S.contract.schema, id: d.id,
      problem: circuit ? {kind: "circuit", circuit: {kind: "inline_stim", text: d.circuitText}, dem: {decompose_errors: false}} : {kind: bp4 ? "pauli_code_capacity" : "css_code_capacity", code},
      channel: {kind: circuit ? "embedded_circuit" : d.channel}, decoder,
      rate_points: circuit ? [{label: "embedded_circuit"}] : d.rates.split(",").map(value => ({physical_p: Number(value.trim()), decoder_p0: d.prior === "matched" ? Number(value.trim()) : d.p0})),
      sampling: {seed: d.seed, shot_start: d.start, shots: d.shots}, budgets: {max_shots: d.maxshots, max_iterations: d.iterations},
      provenance: {relation: "canonical_adaptation", source_spec_id: d.preset || null, notes: d.preset ? "New configuration derived from a catalog specification; historical results do not transfer to this experiment." : null}};
  }
  function matrix(value, name) {
    if (!Array.isArray(value) || !value.length || !Array.isArray(value[0]) || !value[0].length || value.some(row => !Array.isArray(row) || row.length !== value[0].length || row.some(bit => bit !== 0 && bit !== 1))) throw Error(`${name} must be a rectangular binary integer matrix.`);
    return value;
  }
  function rank(matrix) { const a = matrix.map(r => r.slice()); let pivot = 0; for (let col = 0; col < a[0].length && pivot < a.length; col++) { const found = a.findIndex((row, i) => i >= pivot && row[col]); if (found < 0) continue; [a[pivot], a[found]] = [a[found], a[pivot]]; for (let i = pivot + 1; i < a.length; i++) if (a[i][col]) for (let j = col; j < a[i].length; j++) a[i][j] ^= a[pivot][j]; pivot++; } return pivot; }
  function parity(a, b) { let p = 0; for (let i = 0; i < a.length; i++) p ^= a[i] & b[i]; return p; }
  function css(code) {
    if (code.kind !== "embedded_css") return;
    const hx = matrix(code.hx, "hx"), hz = matrix(code.hz, "hz"), n = hx[0].length;
    if (hz[0].length !== n) throw Error("hx and hz must have the same number of columns.");
    if ([...hx, ...hz].some(row => row.every(bit => bit === 0))) throw Error("Code-capacity sampling rejects identity-only check rows.");
    if (hx.some(x => hz.some(z => parity(x, z)))) throw Error("hx and hz do not commute over GF(2).");
    if ((code.lx == null) !== (code.lz == null)) throw Error("Supply both lx and lz, or neither.");
    if (code.lx) { const lx = matrix(code.lx, "lx"), lz = matrix(code.lz, "lz"), k = n - rank(hx) - rank(hz);
      if (lx.length !== k || lz.length !== k || lx[0].length !== n || lz[0].length !== n) throw Error("Logical matrices must have shape (k,n).");
      if (lx.some(x => hz.some(z => parity(x, z))) || lz.some(z => hx.some(x => parity(x, z)))) throw Error("Logical rows do not commute with the opposite checks.");
      if (lx.some((x, i) => lz.some((z, j) => parity(x, z) !== Number(i === j)))) throw Error("Logical X/Z rows must have identity pairing.");
    }
  }
  function validate(spec) {
    const errors = [], check = (condition, message) => { if (!condition) errors.push(message); };
    const keys = S.contract.field_sets.experiment;
    if (!spec || typeof spec !== "object" || keys.some(k => !(k in spec)) || Object.keys(spec).some(k => !keys.includes(k))) return ["Use the complete research-experiment-v1 contract; unknown or missing fields are rejected."];
    const closed = (value, fields, name, optional = []) => {
      check(value && typeof value === "object" && !Array.isArray(value) && fields.every(k => optional.includes(k) || k in value) && Object.keys(value).every(k => fields.includes(k)), `${name}: unknown or missing fields in the shared contract.`);
    };
    const d = spec.decoder, circuit = spec.problem.kind === "circuit";
    closed(spec.sampling, S.contract.field_sets.sampling, "sampling");
    closed(spec.budgets, S.contract.field_sets.budgets, "budgets");
    closed(spec.provenance, S.contract.field_sets.provenance, "provenance");
    closed(spec.problem, S.contract.field_sets[circuit ? "circuit_problem" : "code_problem"], "problem");
    closed(spec.channel, S.contract.field_sets[spec.channel.kind === "explicit" ? "explicit_channel" : "channel"], "channel");
    const decoderFields = [...S.contract.field_sets[circuit ? "circuit_decoder" : "decoder"], ...(!circuit && d.variant === "qbpgd" ? ["qbpgd"] : [])];
    closed(d, decoderFields, "decoder");
    if (errors.length) return errors;
    check(spec.schema === S.contract.schema, "Unsupported experiment schema."); check(typeof spec.id === "string" && spec.id.length > 0, "Supply an experiment label.");
    check(d.schedule === "flooding", "This execution backend supports flooding only; other schedules require a registered study route.");
    check(["binary_css", "bp4", "circuit_dem_bp"].includes(d.family), "Unsupported decoder family.");
    check(Array.isArray(spec.rate_points) && spec.rate_points.length > 0, "Supply at least one rate point.");
    check(S.contract.profiles[d.family]?.includes(d.numerical_profile), "The numerical profile does not belong to this decoder family.");
    check(["canonical_adaptation", "development_fixture"].includes(spec.provenance.relation), "A custom experiment cannot inherit a source-faithful result claim.");
    check(spec.provenance.source_spec_id === null || typeof spec.provenance.source_spec_id === "string", "source_spec_id must be a string or null.");
    check(spec.provenance.notes === null || typeof spec.provenance.notes === "string", "provenance.notes must be a string or null.");
    for (const k of ["shots", "seed", "shot_start"]) check(Number.isSafeInteger(spec.sampling[k]) && spec.sampling[k] >= (k === "shots" ? 1 : 0), `${k} must be an integer in its supported range.`);
    check(Number.isSafeInteger(spec.budgets.max_shots) && spec.budgets.max_shots >= spec.rate_points.length * spec.sampling.shots, "The total shot budget must cover all rate points × shots.");
    check(Number.isSafeInteger(spec.budgets.max_iterations) && spec.budgets.max_iterations >= (circuit ? 0 : 1), "Supply an integer iteration cap.");
    if (circuit) {
      closed(spec.problem.circuit, S.contract.field_sets[spec.problem.circuit?.kind === "registered" ? "registered_input" : "inline_stim"], "circuit");
      closed(spec.problem.dem, ["decompose_errors"], "dem");
      check(spec.rate_points.length === 1, "One Stim circuit has one embedded noise setting; use separate circuits for a sweep.");
      for (const p of spec.rate_points) closed(p, S.contract.field_sets.circuit_rate_point, "circuit rate point");
      check(d.family === "circuit_dem_bp" && d.implementation === "canonical_sinter" && S.contract.rules_by_family.circuit_dem_bp.includes(d.rule) && d.numerical_profile === S.contract.circuit_rule_profiles[d.rule], "Circuit execution supports only the pinned plain float64 v1 Sinter adapter.");
      check(!("policy" in d) && !["damping", "resolution", "variant"].some(k => k in d), "Circuit damping, resolution overlays, and interventions are unsupported.");
      check(spec.channel.kind === "embedded_circuit" && spec.problem.dem?.decompose_errors === false, "Circuit noise comes from Stim text and requires decompose_errors=false.");
      check(spec.problem.circuit?.kind === "registered" || (spec.problem.circuit?.kind === "inline_stim" && typeof spec.problem.circuit.text === "string" && spec.problem.circuit.text.trim().length > 0), "Supply Stim text or a registered circuit.");
      check(spec.sampling.shot_start + spec.sampling.shots <= spec.budgets.max_shots, "Circuit skipped prefix consumes the total shot budget.");
      check(["zero", "one"].includes(d.tie_break), "Unsupported circuit tie policy.");
      check(Number.isSafeInteger(d.max_iterations) && d.max_iterations >= 0 && d.max_iterations <= spec.budgets.max_iterations, "Circuit decoder iteration cap exceeds the budget.");
    } else {
      const input = spec.problem.code;
      closed(input, S.contract.field_sets[input?.kind === "registered" ? "registered_input" : "embedded_css"], "code", ["lx", "lz"]);
      check(S.contract.code_kinds.includes(input?.kind), "Unsupported code input format.");
      check(spec.problem.kind === (d.family === "bp4" ? "pauli_code_capacity" : "css_code_capacity"), "Decoder family and problem regime disagree.");
      check(["depolarizing", "x_only", "explicit"].includes(spec.channel.kind), "Unsupported code-capacity noise model.");
      check(S.contract.rules.includes(d.rule), "Unsupported update rule.");
      check(d.implementation === "compiled", "This custom experiment route uses the compiled canonical implementation.");
      if (d.family === "binary_css") check(d.variant === "plain" && d.stop_on_convergence === true, "Binary compiled BP uses first-valid stopping and plain BP only.");
      if (d.family === "binary_css" && d.rule === "min_sum") check(d.policy !== null, "Binary min-sum requires its explicit v2 numerical policy overlay.");
      if (d.family === "bp4") check(["plain", "qbpgd"].includes(d.variant) && typeof d.stop_on_convergence === "boolean", "Unsupported BP4 procedure or stopping rule.");
      if (!d.numerical_profile?.endsWith("-v1") && !d.numerical_profile?.endsWith("-v2")) errors.push("Unknown numerical profile.");
      if (d.numerical_profile?.endsWith("-v1")) check(d.rule === "sum_product" && d.policy === null && d.variant === "plain", "Frozen v1 requires plain sum-product and no numerical overlay.");
      try { css(spec.problem.code); } catch (error) { errors.push(error.message); }
      for (const p of spec.rate_points) { closed(p, S.contract.field_sets[spec.channel.kind === "explicit" ? "explicit_rate_point" : "rate_point"], "rate point"); if (spec.channel.kind !== "explicit") check(known(p.physical_p) && p.physical_p >= 0 && p.physical_p <= 1, "Physical p must lie in [0,1]."); check(known(p.decoder_p0) && p.decoder_p0 > 0 && p.decoder_p0 < 1, "Decoder p₀ must lie strictly between 0 and 1."); }
      if (spec.channel.kind === "explicit") {
        const probabilities = spec.channel.probabilities, table = Array.isArray(probabilities?.[0]) ? probabilities : [probabilities];
        check(table.every(row => Array.isArray(row) && row.length === 4 && row.every(p => known(p) && p >= 0 && p <= 1) && Math.abs(row.reduce((a, b) => a + b, 0) - 1) <= 8 * Number.EPSILON), "Explicit Pauli probabilities must be normalized I,X,Y,Z rows.");
        if (input.kind === "embedded_css") check(table.length === 1 || table.length === input.hx[0].length, "Per-qubit probability rows must match n.");
      }
      if (d.policy) {
        const p = d.policy, r = p.resolution;
        closed(p, S.contract.field_sets.policy, "policy"); closed(r, S.contract.field_sets.resolution, "resolution");
        check(d.numerical_profile.endsWith("-v2") && p.check_rule === d.rule && p.version === S.contract.ui_fields.policy.version, "Policy overlay must match the v2 profile and check rule.");
        check(r && r.version === S.contract.ui_fields.policy.resolution_version && S.contract.resolution.formats.includes(r.format) && S.contract.resolution.scopes.includes(r.scope) && S.contract.resolution.coefficients.includes(r.coefficients), "Unknown resolution policy.");
        if (r?.format.startsWith("int")) check(Number.isSafeInteger(r.scale) && r.scale > 0 && r.scale <= 2147483647, "Fixed-point scale must be a positive int32-range integer."); else check(r?.scale === null, "Floating formats use scale=null.");
        check(known(p.damping) && p.damping >= 0 && p.damping < 1 && known(p.alpha) && p.alpha > 0 && known(p.beta) && p.beta >= 0, "Invalid damping, scale, or offset coefficient.");
        if (d.rule === "sum_product") check(p.alpha === 1 && p.beta === 0, "SPA does not accept min-sum scale or offset.");
        if (d.family === "binary_css") check(p.hard_decision === "min_llr", "A Pauli hard-decision policy cannot modify a binary decoder.");
        check(["min_llr", "strict_pauli"].includes(p.hard_decision) && typeof p.zero_syndrome_shortcut === "boolean", "Unsupported hard-decision or shortcut policy.");
      }
      if (d.variant === "qbpgd") { closed(d.qbpgd, S.contract.field_sets.qbpgd, "qbpgd"); check(d.family === "bp4" && d.rule === "sum_product" && d.stop_on_convergence === true && d.numerical_profile === "quaternary-bp4-f64-v2" && d.policy === null && Number.isSafeInteger(d.qbpgd?.round_limit) && d.qbpgd.round_limit > 0 && Number.isSafeInteger(d.qbpgd?.iterations_per_round) && d.qbpgd.iterations_per_round > 0 && d.qbpgd.round_limit * d.qbpgd.iterations_per_round <= spec.budgets.max_iterations && known(d.qbpgd.epsilon) && d.qbpgd.epsilon > 0 && d.qbpgd.epsilon < 1, "Q-BPGD needs sum-product v2, first-valid stopping, no resolution overlay, and rounds × sweeps within the total iteration cap."); }
    }
    return errors;
  }
  function preview() {
    S.valid = false; $("download-package").disabled = true;
    try { S.spec = S.custom ? copy(S.custom) : visualSpec(); $("spec-output").textContent = JSON.stringify(S.spec, null, 2); }
    catch (error) { S.spec = null; $("spec-output").textContent = error.message; }
    $("form-summary").className = "form-summary";
    $("form-summary").textContent = S.unsupported || (S.custom ? "Custom JSON mode. Its exact fields will be exported; return to the visual builder to configure controls." : S.draft.preset ? "New experiment derived from a frozen specification. The parent result is available in Results; these edited settings have no measured result yet." : "New experiment: no measured result is claimed. Download and run locally after validation.");
  }
  function validateCurrent() {
    preview(); const errors = S.unsupported ? [S.unsupported] : S.spec ? validate(S.spec) : ["Correct the input JSON first."];
    S.valid = errors.length === 0; $("form-summary").className = "form-summary " + (S.valid ? "valid" : "error");
    $("form-summary").textContent = S.valid ? "Structural and policy checks passed. Python repeats the shared contract, CSS/Stim algebra, and kernel compatibility checks before sampling." : errors.join(" ");
    $("download-package").disabled = !S.valid; return S.valid;
  }
  function useDecoder(decoder, code) {
    if (!decoder) { S.draft.preset = ""; S.unsupported = ""; renderBuilder(); return; }
    const config = decoder.configuration?.effective_policy || decoder.configuration?.effective_candidate || decoder.configuration;
    S.custom = null; S.draft = defaultDraft(); S.draft.preset = decoder.decoder_id;
    if (config?.schema !== "vanilla-bp-decoder-v1" || !["binary_css_separate", "bp4"].includes(config.family) || config.check_rule !== "sum_product") {
      S.unsupported = "This frozen procedure has a study-specific runner. Export its exact specification and use the original entry point shown in Results. Its settings cannot be imported as a plain compiled decoder; choose Custom to build a new configuration.";
    } else {
      S.unsupported = ""; const d = S.draft; d.family = config.family === "bp4" ? "bp4" : "binary_css"; d.code = code || "three-qubit";
      d.version = /v1/.test(config.numerical_profile) ? "v1" : "v2"; d.rule = "sum_product"; d.iterations = config.max_iterations;
      d.damping = config.damping_old; d.prior = "matched"; d.hard = d.family === "bp4" && d.version === "v2" ? "strict_pauli" : "min_llr";
      d.shortcut = d.family !== "bp4" || d.version !== "v2";
      // Explicit v2 overlay preserves the frozen undamped arm rather than
      // inheriting the canonical profile's old-message weight of 0.1.
      d.policy = d.version === "v2"; d.format = "float64"; d.scope = "scalar_edges";
    }
    renderBuilder(); route("builder");
  }
  async function portableSpec(spec) {
    const result = copy(spec), problem = result.problem;
    if (problem.code?.kind === "registered") {
      const code = record("codes", problem.code.id);
      if (code?.asset && /\.json$/.test(code.asset.path) && assetURL(code.asset)) {
        const data = JSON.parse(new TextDecoder().decode(await assetBytes(code.asset)));
        if (Array.isArray(data.hx) && Array.isArray(data.hz)) { problem.code = {kind: "embedded_css", hx: data.hx, hz: data.hz}; if (data.lx && data.lz) Object.assign(problem.code, {lx: data.lx, lz: data.lz}); }
      }
    }
    if (problem.circuit?.kind === "registered") {
      const item = record("circuits", problem.circuit.id); if (!item) throw Error("Registered circuit is unavailable.");
      problem.circuit = {kind: "inline_stim", text: new TextDecoder().decode(await assetBytes(item.asset))};
    }
    return result;
  }
  async function downloadPackage() {
    if (!validateCurrent()) return;
    const button = $("download-package"); button.disabled = true;
    try {
      const spec = await portableSpec(S.spec), errors = validate(spec); if (errors.length) throw Error(errors.join(" "));
      const files = {...S.template.files, "experiment.json": JSON.stringify(spec, null, 2) + "\n", "decoder.json": JSON.stringify(spec.decoder, null, 2) + "\n"};
      if (spec.problem.code?.kind === "embedded_css") { const code = {...spec.problem.code}; delete code.kind; files["inputs/code.json"] = JSON.stringify(code, null, 2) + "\n"; }
      if (spec.problem.circuit?.kind === "inline_stim") files["inputs/circuit.stim"] = spec.problem.circuit.text;
      if (spec.problem.kind === "circuit" && spec.provenance.source_spec_id?.startsWith("circuit:")) {
        const source = record("circuits", spec.provenance.source_spec_id.slice(8));
        if (source && await digest(spec.problem.circuit.text) === source.asset.sha256) {
          files["inputs/circuit-source.json"] = JSON.stringify({circuit_id: source.circuit_id, ...source.source, circuit_sha256: source.asset.sha256}, null, 2) + "\n";
          for (const item of source.license_assets || []) files["inputs/" + item.path.split("/").pop()] = new TextDecoder().decode(await assetBytes(item));
        }
      }
      const hashes = {}; for (const name of Object.keys(files).sort()) hashes[name] = await digest(files[name]);
      files["package-manifest.json"] = JSON.stringify({schema: "research-package-manifest-v1", files: hashes}, null, 2) + "\n";
      save(spec.id.replace(/[^a-zA-Z0-9._-]/g, "-") + ".zip", ResearchZip.create(Object.entries(files).map(([name, content]) => ({name, content}))));
      $("form-summary").textContent = "Package prepared from this exact configuration. It contains no computed results; run it locally to create new evidence.";
    } catch (error) { showError(error); } finally { button.disabled = !S.valid; }
  }
  async function downloadRegistered(experiment) {
    const recipe = experiment.reproduction_recipe, files = {...S.template.registered_files}, inputs = {};
    for (const [key, label] of [["study_path", "original-study"], ["decoder_path", "original-decoder"]]) {
      const path = recipe[key], response = await fetch(new URL("../../" + path, location.href));
      if (!response.ok) throw Error(`Registered input unavailable: ${path}`);
      const bytes = new Uint8Array(await response.arrayBuffer()); inputs[path] = await digest(bytes);
      const knownAsset = S.catalog.decoders.map(d => d.asset).filter(Boolean).find(a => a.path === path);
      if (knownAsset?.sha256 && knownAsset.sha256 !== inputs[path]) throw Error("Registered input changed; refresh the catalog.");
      files[label + "." + path.split(".").pop()] = bytes;
    }
    files["registered-experiment.json"] = JSON.stringify({schema: "registered-study-package-v1", experiment_id: experiment.experiment_id, ...recipe, repository_inputs: inputs, evidence_status: experiment.evidence_status}, null, 2) + "\n";
    const hashes = {}; for (const name of Object.keys(files).sort()) hashes[name] = await digest(files[name]);
    files["package-manifest.json"] = JSON.stringify({schema: "research-package-manifest-v1", files: hashes}, null, 2) + "\n";
    save("original-" + experiment.experiment_id + ".zip", ResearchZip.create(Object.entries(files).map(([name, content]) => ({name, content}))));
  }
  function renderCircuits() {
    selectOptions($("circuit-select"), S.catalog.circuits, "Choose a pinned circuit"); $("use-circuit").disabled = !S.catalog.circuits.length;
    $("use-circuit").onclick = async () => {
      try { const item = record("circuits", $("circuit-select").value); if (!item) throw Error("Choose a circuit first.");
        const content = new TextDecoder().decode(await assetBytes(item.asset)); circuitDraft(content, item.circuit_id); $("circuit-note").textContent = item.scope;
      } catch (error) { $("circuit-note").textContent = error.message; }
    };
  }
  function circuitDraft(content, id = "") { S.custom = null; S.unsupported = ""; S.draft = defaultDraft(); S.draft.family = "circuit_dem_bp"; S.draft.rule = "spa"; S.draft.circuit = id; S.draft.preset = id ? "circuit:" + id : ""; S.draft.circuitText = content; renderBuilder(); route("builder"); }
  function exportTable() {
    const header = ["dataset", "code", "decoder", "p", "estimate", "raw_samples", "raw_failures", "type_i", "type_ii", "ci_low", "ci_high", "estimator", "uncertainty_method", "mean_work", "work_unit", "mean_seconds", "evidence"];
    const lines = rows().map(({series: s, point: p}) => [s.dataset_id, s.code_id, s.decoder_id, p.x, p.y, p.n, p.failures, p.type_i, p.type_ii, p.ci_low, p.ci_high, p.estimator || p.sampling_method, p.ci_method || p.uncertainty_method, p.mean_work, p.work_unit, p.mean_seconds, s.evidence]);
    save("retained-results.csv", [header, ...lines].map(line => line.map(v => `"${String(v ?? "").replaceAll('"', '""')}"`).join(",")).join("\n") + "\n", "text/csv");
  }
  async function load() {
    try {
      [S.catalog, S.contract, S.template] = await Promise.all([json("catalog.json"), json("contract.json"), json("package-template.json")]);
      for (const k of ["papers", "experiments", "datasets", "decoders", "codes", "circuits"]) S.catalog[k] ||= [];
      S.series = S.catalog.result_series.map((item, i) => { const data = record("datasets", item.dataset_id); if (!data) throw Error(`Dataset relationship missing: ${item.dataset_id}`); return {...item, points: item.points.map(p => ({...p, ...(p.metadata || {})})), key: `${item.dataset_id}:${item.code_id}:${item.decoder_id}:${i}`, paper_ids: data.paper_ids || [data.paper_id], evidence: data.evidence_status}; });
      $("stat-papers").textContent = S.catalog.papers.filter(p => p.kind === "paper").length;
      $("stat-studies").textContent = S.catalog.experiments.length; $("stat-results").textContent = S.series.length;
      $("catalog-status").textContent = `${S.catalog.datasets.length} retained datasets · static catalog`;
      selectOptions($("paper-status"), [{id: "paper", label: "External papers"}, {id: "local_study", label: "Local studies"}], "All kinds");
      $("paper-regime").closest("label").hidden = true;
      selectOptions($("result-paper"), S.catalog.papers, "All papers / studies", "yao-2312-10950-v2");
      selectOptions($("result-experiment"), paperExperiments("yao-2312-10950-v2"), "All experiments", "yao-vanilla");
      filters(); $("result-code").value = "a5"; filters("code");
      renderPapers(); library(); renderCircuits(); renderBuilder(); route(location.hash.slice(1) || "papers");
    } catch (error) { $("catalog-status").textContent = "Catalog unavailable"; $("paper-list").textContent = error.message + ". Run bp-registry-research build and serve the interface over HTTP."; console.error(error); }
  }
  document.addEventListener("DOMContentLoaded", () => {
    addLibraries(); for (const id of ["paper-search", "paper-status"]) $(id).addEventListener(id === "paper-search" ? "input" : "change", renderPapers);
    for (const [id, changed] of [["result-paper", "paper"], ["result-experiment", "experiment"], ["result-dataset", "dataset"], ["result-code", "code"], ["result-decoder", "decoder"]]) $(id).onchange = () => filters(changed);
    $("metric-select").onchange = () => { S.metric = $("metric-select").value; renderTable(); renderPlot(); };
    $("refresh-catalog").onclick = load; $("validate-experiment").onclick = validateCurrent; $("download-package").onclick = downloadPackage; $("export-visible-results").onclick = exportTable;
    $("copy-spec").onclick = () => navigator.clipboard?.writeText($("spec-output").textContent);
    $("apply-custom-json").onclick = () => { try { const value = JSON.parse($("custom-json").value), errors = validate(value); if (errors.length) throw Error(errors.join(" ")); S.custom = value; S.unsupported = ""; renderBuilder(); validateCurrent(); $("custom-json-feedback").textContent = "Custom specification loaded. Exact fields retained; authoritative kernel validation repeats locally."; } catch (error) { $("custom-json-feedback").textContent = error.message; $("custom-json-feedback").className = "field-feedback error"; S.valid = false; $("download-package").disabled = true; } };
    $("circuit-file").onchange = async () => { const file = $("circuit-file").files[0]; if (file) circuitDraft(await file.text()); };
    document.querySelectorAll("[data-nav]").forEach(link => link.onclick = event => { event.preventDefault(); route(link.dataset.nav); });
    window.addEventListener("hashchange", () => route(location.hash.slice(1)));
    load();
  });
})();
