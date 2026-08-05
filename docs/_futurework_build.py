# -*- coding: utf-8 -*-
"""Builds 'Vyuha - Future Work & Research Directions' (HTML -> PDF via weasyprint)."""
from weasyprint import HTML

ACCENT, ACCENT2 = "#1f3b63", "#2f6f9f"

CSS = """
@page {
  size: A4; margin: 1.7cm 1.9cm 2cm 1.9cm;
  @bottom-center { content: "Vyuha - Future Work & Research Directions"; font-size: 8pt; color: #9aa6b2; }
  @bottom-right  { content: counter(page) " / " counter(pages); font-size: 8pt; color: #9aa6b2; }
}
@page :first { @bottom-center { content: ""; } @bottom-right { content: ""; } }
* { box-sizing: border-box; }
body { font-family: "DejaVu Serif", Georgia, serif; font-size: 10.3pt; line-height: 1.5; color: #1c2430; }
h1,h2,h3,h4 { font-family: "DejaVu Sans","Segoe UI",Helvetica,Arial,sans-serif; color: %(ACCENT)s; line-height:1.25; page-break-after: avoid; }
h2 { font-size: 15.5pt; margin: 2px 0 12px; padding: 7px 0 7px 13px; border-left: 5px solid %(ACCENT2)s;
     background: linear-gradient(90deg,#eef3f8,rgba(238,243,248,0)); page-break-before: always; }
h3 { font-size: 12pt; margin: 14px 0 5px; color: %(ACCENT2)s; }
h4 { font-size: 10.6pt; margin: 10px 0 3px; color:#2a3a4d; }
p { margin: 6px 0; text-align: justify; }
a { color: %(ACCENT2)s; text-decoration: none; }
b, strong { color:#122236; }
code, .mono { font-family:"DejaVu Sans Mono",monospace; font-size: 8.8pt; background:#f0f3f7; padding:1px 4px; border-radius:3px; }
ul { margin:6px 0 6px 0; padding-left: 18px; } li { margin:3px 0; }
.cover { border-top: 8px solid %(ACCENT)s; padding-top: 26px; }
.cover .kicker { font-family:"DejaVu Sans",sans-serif; letter-spacing:2px; text-transform:uppercase; color:%(ACCENT2)s; font-size:9pt; }
.cover h1 { font-size: 26pt; margin: 8px 0 6px; color:%(ACCENT)s; line-height:1.15; }
.cover .sub { font-size: 12pt; color:#41526a; font-family:"DejaVu Sans",sans-serif; }
.cover .meta { margin-top: 14px; font-size:10pt; color:#3a4a5f; }
.cover .note { margin-top: 18px; font-style: italic; font-size:9.2pt; color:#5a6675; border-top:1px solid #dbe3ec; padding-top:10px; }
table { border-collapse: collapse; width: 100%%; margin: 10px 0 14px; font-size: 9pt; page-break-inside: avoid; }
thead { display: table-header-group; }
tbody tr { page-break-inside: avoid; }
thead th { background: %(ACCENT)s; color: #fff; font-family:"DejaVu Sans",sans-serif; font-weight:600;
           text-align: left; padding: 5px 8px; border: 1px solid %(ACCENT)s; font-size:8.7pt; line-height:1.25; }
tbody td { padding: 5px 8px; border: 1px solid #cdd7e2; vertical-align: top; line-height:1.35; }
tbody tr:nth-child(even) td { background: #f3f6fa; }
.pri1 td:first-child { border-left: 4px solid #1f8a70; font-weight:600; }
.pri2 td:first-child { border-left: 4px solid #b06a1e; }
.callout { border:1px solid #dbe6c9; background:#f4f8ec; border-left:5px solid #6f9b3f; border-radius:6px; padding:8px 12px; margin:10px 0; font-size:9.4pt; page-break-inside: avoid; }
.callout.warn { border-color:#e6d6bf; background:#fbf5ea; border-left-color:#c78a2e; }
.callout.info { border-color:#c9dcea; background:#eef5fb; border-left-color:#2f6f9f; }
.grade { font-family:"DejaVu Sans",sans-serif; font-size:7.6pt; font-weight:700; padding:1px 6px; border-radius:9px; color:#fff; }
.g-hi { background:#1f8a70; } .g-med { background:#b06a1e; } .g-lo { background:#9aa6b2; }
.small { font-size: 8.8pt; color:#5a6675; }
.step { border:1px solid #d5dee8; border-radius:7px; padding:8px 12px; margin:8px 0; background:#fbfcfe; page-break-inside: avoid; }
.step .h { font-family:"DejaVu Sans",sans-serif; font-weight:700; color:%(ACCENT)s; font-size:10.2pt; }
""" % {"ACCENT": ACCENT, "ACCENT2": ACCENT2}


def table(headers, rows, cls=None):
    th = "".join(f"<th>{h}</th>" for h in headers)
    body = ""
    for r in rows:
        rc = ""
        if isinstance(r, tuple):
            r, rc = r[0], f' class="{r[1]}"' if len(r) > 1 else ""
        body += f"<tr{rc}>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>"
    return f"<table><thead><tr>{th}</tr></thead><tbody>{body}</tbody></table>"


HI = '<span class="grade g-hi">PRIMARY</span>'
MED = '<span class="grade g-med">SECONDARY</span>'
LO = '<span class="grade g-lo">BLOG</span>'

H = []
H.append('<div class="cover">'
         '<div class="kicker">Vyuha Project · CSL6010 · IIT Jodhpur · research memo</div>'
         '<h1>Future Work &amp; Research Directions</h1>'
         '<div class="sub">A source-graded 2026 state-of-the-art scan, a prioritised roadmap, and a concrete next-build plan (P12)</div>'
         '<div class="meta"><b>U E Sai Pavan Vamshi Krishna</b> (G25AIT2149) &nbsp;·&nbsp; as of 5 August 2026</div>'
         '<div class="note">Prepared with a rigorous, auditable research method: ~18 sources opened and graded, load-bearing claims '
         'traced to primary sources (arXiv, OWASP, NSA), disconfirming queries run, and confidence stated per finding. '
         'Vendor/SEO blog figures are labelled and never cited as fact.</div></div>')

# 1
H.append('<h2 class="first">1 &middot; Executive summary</h2>')
H.append('<p>Vyuha is <b>well-positioned, not behind</b>. Its selective cascade, non-overlapping-guard ensemble, continuous '
         'red-team, and honest black-box posture match what independent 2026 sources recommend: <i>defense-in-depth plus '
         'continuous red-teaming and monitoring, aiming at risk reduction rather than elimination</i>. The question is not whether '
         'to rebuild, but where to extend.</p>')
H.append('<p>The highest-value directions, ranked by decision-weight, are: <b>(1) go agentic</b> - extend L3 from tool-<i>output</i> '
         'scanning to <b>MCP tool-poisoning and stateful action/capability control</b>; <b>(2) add multi-turn / session-level '
         'detection</b>; <b>(3) run a rigorous adaptive-attack and standardised-benchmark evaluation</b> (the honest weak point, and '
         'the most paper-worthy move); <b>(4) upgrade the guard ensemble</b> with one non-overlapping guard. Sections 3 and 5 make '
         'these concrete.</p>')
H.append('<div class="callout info"><b>Honest correction.</b> Our going-in prior over-weighted &ldquo;provable guarantees.&rdquo; '
         'The evidence <b>demoted</b> that: no certified defense currently stops adaptive attacks, so provable guardrails are a '
         'research aspiration, not a near-term deliverable.</div>')

# 2
H.append('<h2>2 &middot; How the field moved in 2026</h2>')
H.append('<p>Five shifts, each corroborated by primary or institutional sources, define what a modern defense must now address:</p>')
H.append(table(
    ["Shift in 2026", "What it means", "Source"],
    [["Content &rarr; <b>agentic action</b>", "Guardrails built for LLMs-as-models miss attacks that unfold over tool-call action sequences; OWASP shipped a new Top 10 for Agentic Applications (ASI01-ASI10).", f"OWASP Agentic Top 10 2026 {MED}"],
     ["The <b>session</b>, not the prompt", "Multi-turn (Crescendo) attacks escalate from benign to harmful across turns at 65-99% success; single-message moderation does not catch them.", f"Crescendo, USENIX Sec 2025 {HI}"],
     ["<b>No certified defense</b> yet", "Adaptive attackers bypass 12 recent defenses at &gt;90% ASR by tuning general optimisers - robustness must be measured, not assumed.", f"“The Attacker Moves Second” {HI}"],
     ["<b>MCP</b> is the new attack surface", "Tool poisoning hides instructions in tool descriptions/metadata (not outputs); NSA, OWASP and multiple papers now treat it as a first-class threat.", f"MCP-38 taxonomy; NSA MCP guidance {HI}"],
     ["Guard-model reality check", "On a 14-model, 79,331-sample NIST-RMF benchmark: recall is the critical metric, model size does NOT predict safety performance, and ensembling non-overlapping guards is recommended.", f"Guard benchmark, arXiv 2605.28830 {HI}"]]))
H.append('<div class="callout"><b>Why this validates Vyuha.</b> The same benchmark found <b>Qwen Guard (4B) had the highest recall '
         '(83.97%)</b> while larger Llama Guard 12B / GPT-OSS-Safeguard 20B were conservative, missing up to 75% of unsafe content. '
         'Your choice of Qwen3Guard, your recall-at-fixed-FPR metric, and your cascade+ensemble design are all endorsed by 2026 '
         'evidence.</div>')

# 3
H.append('<h2>3 &middot; Prioritised roadmap</h2>')
H.append('<p>Ranked by decision-weight for <i>this</i> project (working, free-compute, black-box, single-author). Priority 1 items are '
         'green-barred; research stretches are amber-barred.</p>')
H.append(table(
    ["Direction", "What to add to Vyuha", "Effort", "Free compute?", "Evidence"],
    [(["<b>1. Agentic: MCP tool-poisoning + stateful action control</b>", "Scan MCP tool descriptions (not just outputs); action-sequence tool policy; instruction hierarchy system&gt;user&gt;tool", "Medium", "Yes", HI], "pri1"),
     (["<b>2. Multi-turn / session-level detection</b>", "Score the whole conversation graph; extend the L5 drift monitor to per-session escalation (catch Crescendo)", "Low-Med", "Yes", HI], "pri1"),
     (["<b>3. Adaptive-attack + benchmark evaluation</b>", "Run Vyuha vs adaptive attacks; report on the NIST-RMF guard benchmark + full AgentDojo", "Medium", "Mostly", HI], "pri1"),
     (["<b>4. Guard-ensemble upgrade</b>", "Add one non-overlapping guard (e.g. Granite Guardian for injection); ensemble + report", "Low", "Yes (GPU)", MED], "pri1"),
     (["5. Representation-level defense (circuit breakers / RepE)", "Reroute harmful internal representations - attack-agnostic, no guard model", "High", "No (white-box)", HI], "pri2"),
     (["6. Multimodal coverage", "Image/audio jailbreak + injection screening", "High", "Partly", MED], "pri2"),
     (["7. Provable / verifiable-policy guardrails", "Formal action-policy verification (ShieldAgent-style)", "Very high", "No", MED], "pri2")]))
H.append('<h3>The four Priority-1 moves, in detail</h3>')
H.append('<p><b>1. Go agentic (the top pick - scoped as P12 in Section 5).</b> Your L3 scans tool <i>outputs</i>; the 2026 frontier is '
         'attacks that never appear in outputs. <b>MCP tool poisoning</b> hides instructions in tool <i>descriptions/metadata</i> so the '
         'agent is compromised before a tool runs (MCP-38 taxonomy; Trust No Tool; NSA guidance). <b>CASCADE</b> (arXiv 2604.17125) is '
         'literally a cascaded hybrid defense for MCP prompt injection - your architecture, applied to MCP. Extending '
         '<span class="mono">InjectionScanner</span> to tool descriptions and moving <span class="mono">ToolPolicy</span> toward '
         'verifiable action-sequence policy (ShieldAgent / AGrail / CaMeL direction) is timely and paper-worthy. '
         '<i>Confidence: high.</i></p>')
H.append('<p><b>2. Defend the session, not the prompt.</b> Vyuha is single-turn; Crescendo defeats single-message moderation. Add a '
         'lightweight <b>per-conversation escalation detector</b> - you already own a drift monitor (PSI); extend it to score the '
         'conversation graph over turns. <i>Confidence: high.</i></p>')
H.append('<p><b>3. Measure robustness honestly.</b> Your own limitations section is validated by the field: no certified defense stops '
         'adaptive attacks. The decision-grade move is to <b>measure</b> - run Vyuha against the adaptive attacks of &ldquo;The Attacker '
         'Moves Second,&rdquo; report on the standardised NIST-RMF guard benchmark, and scale your P11 AgentDojo run past n=2. This '
         'turns an honest weakness into the paper&rsquo;s strongest, most credible contribution. <i>Confidence: high.</i></p>')
H.append('<p><b>4. Add one non-overlapping guard.</b> 2026 guidance: pair two guards with complementary strengths and ensemble - which '
         'your L1+L2 cascade already does. Granite Guardian (IBM) reportedly leads on prompt-injection; GuardReasoner-Omni adds '
         'reasoning/multimodal; X-Guard adds multilingual. Add one, report the ensemble on the benchmark. '
         '<i>Confidence: medium-high (the &ldquo;Granite leads on injection&rdquo; claim is from a secondary overview - verify against IBM&rsquo;s primary card).</i></p>')

# 4
H.append('<h2>4 &middot; Contested, unknown, and what would change the ranking</h2>')
H.append('<h4>Contested / unknown</h4>')
H.append('<ul>'
         '<li><b>Vendor effectiveness figures are unverified.</b> Numbers like PromptArmor &ldquo;&lt;1% FPR,&rdquo; AgentWatcher '
         '&ldquo;near-zero ASR,&rdquo; and a &ldquo;340% attack surge&rdquo; came from SEO/vendor blogs (low reliability) and are '
         '<b>not</b> cited as fact here.</li>'
         '<li><b>Black-box vs white-box is genuinely contested.</b> Representation methods report near-zero ASR but require model access; '
         'black-box layered defenses report higher residual ASR but deploy anywhere. Vyuha sits firmly and defensibly on the black-box '
         'side - a deliberate design choice, not an oversight.</li></ul>')
H.append('<h4>What would flip the ranking</h4>')
H.append('<ul>'
         '<li>If the project can use a <b>model you fine-tune/control</b>, representation-level defense (circuit breakers) jumps to #1 - '
         'it has the strongest measured robustness.</li>'
         '<li>If your professor steers toward <b>theory</b>, the provable/verifiable-policy line becomes the thesis, not a footnote.</li>'
         '<li>If a <b>new adaptive attack</b> specifically defeats cascaded/ensemble guards, the adaptive-evaluation move (3) becomes '
         'urgent rather than merely valuable.</li></ul>')

# 5 - P12
H.append('<h2>5 &middot; P12 build plan - MCP tool-poisoning + stateful-agent extension</h2>')
H.append('<p>The scoped top pick. It extends the agent layer (L3) and the ops layer (L5) to cover the two biggest 2026 gaps - MCP tool '
         'poisoning and multi-turn/action-sequence attacks - while staying inside Vyuha&rsquo;s free-compute, black-box, reproducible '
         'thesis. It maps directly onto the <b>OWASP Top 10 for Agentic Applications 2026</b> (ASI02 Tool Misuse, ASI06 Memory/Context '
         'Poisoning) and the <b>MCP-38</b> taxonomy.</p>')
H.append('<div class="step"><div class="h">Component A &mdash; MCP tool-description scanner (new)</div>'
         '<p class="small" style="margin-top:4px">Today L3 scans tool <i>outputs</i>. Tool poisoning lives in tool <i>descriptions/'
         'metadata</i>, read before any tool runs. Add <span class="mono">vyuha/agent/mcp_scanner.py</span>: normalise (L0) then apply '
         'the existing injection rules + a few MCP-specific ones (hidden-instruction, exfiltration, &ldquo;when the agent asks X do Y&rdquo; '
         'conditional-trigger, description/behaviour mismatch) to each MCP tool&rsquo;s <span class="mono">description</span> and '
         '<span class="mono">inputSchema</span> at registration time. Block or quarantine poisoned tools before they enter context.</p></div>')
H.append('<div class="step"><div class="h">Component B &mdash; Stateful action / capability policy (extend ToolPolicy)</div>'
         '<p class="small" style="margin-top:4px">Move <span class="mono">vyuha/agent/tool_policy.py</span> from single-step taint toward '
         'an <b>instruction hierarchy</b> (system &gt; user &gt; tool) and an <b>action-sequence</b> check: track the sequence of '
         '(read-untrusted &rarr; dangerous-action) across the turn, require confirm/block when an untrusted read is followed by an '
         'exfiltration/transfer/delete, and constrain the action space by default (least privilege). This is the free-compute, black-box '
         'approximation of ShieldAgent / CaMeL - stated honestly as weaker than their guarantees.</p></div>')
H.append('<div class="step"><div class="h">Component C &mdash; Session-level escalation detector (extend the L5 monitor)</div>'
         '<p class="small" style="margin-top:4px">Extend <span class="mono">vyuha/ops/monitor.py</span> to a per-conversation mode that '
         'scores the whole session graph (running max L1/L2 score, topic-drift, refusal-then-retry pattern) to catch Crescendo-style '
         'multi-turn escalation that any single message passes.</p></div>')
H.append('<h3>Evaluation (what makes it a result, not a claim)</h3>')
H.append(table(
    ["Axis", "Test set", "Metric"],
    [["Tool poisoning", "Curated poisoned MCP tool descriptions (public MCP-attack corpora + hand-built)", "detection rate; benign-tool pass-rate"],
     ["Agent injection", "AgentDojo (P11, scaled) with/without the new action policy", "injection ASR; task utility"],
     ["Multi-turn", "Crescendo-style escalation set", "session-level detection; per-message FPR"]]))
H.append('<h3>Deliverables &amp; effort</h3>')
H.append('<ul>'
         '<li><b>Code:</b> <span class="mono">vyuha/agent/mcp_scanner.py</span> (new), extended '
         '<span class="mono">tool_policy.py</span> and <span class="mono">ops/monitor.py</span>, '
         '<span class="mono">eval/mcp_eval.py</span> (new), and a <b>P12 Kaggle notebook</b>.</li>'
         '<li><b>Compute:</b> free - the scanners are rule/normalise-based (CPU); only the AgentDojo arm needs an LLM backend (free Groq, as in P11).</li>'
         '<li><b>Effort:</b> Components A and C are small (days); Component B is the substantive piece; the eval is the time cost.</li></ul>')
H.append('<div class="callout warn"><b>Honest positioning (carry into the paper).</b> This keeps Vyuha black-box and free-compute; it '
         'does <b>not</b> match CaMeL&rsquo;s capability guarantees or ShieldAgent&rsquo;s verifiable policies. The defensible '
         'contribution is <i>composition + reproducibility + being MCP-native and stateful on free compute</i> - and saying, at every '
         'layer, exactly where stronger (white-box, formally-verified, or paid-compute) work exists.</div>')

# 6
H.append('<h2>6 &middot; References &amp; method note</h2>')
H.append('<p class="small">Grading: <span class="grade g-hi">PRIMARY</span> peer-reviewed / official; '
         '<span class="grade g-med">SECONDARY</span> reputable overview; <span class="grade g-lo">BLOG</span> vendor/SEO, orientation only.</p>')
H.append('<ul>'
         '<li>' + HI + ' Benchmarking Open-Source Safety Guard Models &mdash; arXiv:2605.28830 (Apr 2026). <span class="small">https://arxiv.org/abs/2605.28830</span></li>'
         '<li>' + HI + ' The Attacker Moves Second (adaptive attacks bypass 12 defenses) &mdash; OpenReview 7B9mTg7z25.</li>'
         '<li>' + HI + ' Crescendo multi-turn jailbreak &mdash; USENIX Security 2025 / arXiv:2404.01833; &ldquo;Multi-Turn Jailbreaks Are Simpler Than They Seem&rdquo; arXiv:2508.07646.</li>'
         '<li>' + HI + ' MCP-38 threat taxonomy arXiv:2603.18063; Trust No Tool arXiv:2605.17453; CASCADE (MCP cascaded defense) arXiv:2604.17125; NSA MCP Security guidance.</li>'
         '<li>' + HI + ' Circuit Breakers (Representation Rerouting) &mdash; NeurIPS 2024 / arXiv:2406.04313; contrastive representation learning arXiv:2506.11938.</li>'
         '<li>' + HI + ' ShieldAgent (verifiable safety-policy reasoning) arXiv:2503.22738; Provably Secure Agent Guardrail arXiv:2605.29251.</li>'
         '<li>' + MED + ' OWASP Top 10 for Agentic Applications 2026 (genai.owasp.org); GuardReasoner-Omni arXiv:2602.03328; X-Guard arXiv:2504.08848.</li>'
         '<li>' + LO + ' Vendor/SEO overviews (getmaxim, futureagi, intelscroll, practical-devsecops) &mdash; used for orientation only; their specific statistics are not cited as fact.</li></ul>')
H.append('<p class="small"><b>Method.</b> Standard-tier deep-research protocol: question framed to the decision it serves, prior stated and '
         'tested against disconfirming searches, sources graded before use, claims traced to primary origin, confidence stated per '
         'finding, and the ranking&rsquo;s falsifiers named. As-of date: 5 August 2026.</p>')

html = "<html><head><meta charset='utf-8'><style>" + CSS + "</style></head><body>" + "".join(H) + "</body></html>"
open("/tmp/vyuha_futurework.html", "w", encoding="utf-8").write(html)
HTML(string=html).write_pdf("/tmp/Vyuha_Future_Work.pdf")
print("PDF built -> /tmp/Vyuha_Future_Work.pdf")
