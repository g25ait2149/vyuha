# -*- coding: utf-8 -*-
"""Builds a styled PDF of the professor-review response (Markdown -> HTML -> PDF via weasyprint).
Matches the Vyuha technical-document styling (fonts, navy accents), minus the per-section page breaks
since the response is short. Run: python docs/_profresponse_build.py"""
import re
import markdown
from weasyprint import HTML

ACCENT = "#1f3b63"     # deep navy
ACCENT2 = "#2f6f9f"    # steel blue

CSS = f"""
@page {{
  size: A4; margin: 1.9cm 2.0cm 2cm 2.0cm;
  @bottom-center {{ content: "Vyuha — Response to Review"; font-size: 8pt; color: #9aa6b2; }}
  @bottom-right  {{ content: counter(page) " / " counter(pages); font-size: 8pt; color: #9aa6b2; }}
}}
@page :first {{ @bottom-center {{ content: ""; }} @bottom-right {{ content: ""; }} }}
* {{ box-sizing: border-box; }}
body {{ font-family: "DejaVu Serif", Georgia, serif; font-size: 10.4pt; line-height: 1.5; color: #1c2430; }}
h1,h2,h3 {{ font-family: "DejaVu Sans","Segoe UI",Helvetica,Arial,sans-serif; color: {ACCENT}; line-height:1.25; page-break-after: avoid; }}
h2 + p, h3 + p, h2 + ul, h3 + ul {{ page-break-before: avoid; }}
h2 {{ font-size: 13.5pt; margin: 16px 0 7px; padding: 6px 0 6px 12px; border-left: 5px solid {ACCENT2};
      background: linear-gradient(90deg,#eef3f8,rgba(238,243,248,0)); }}
h3 {{ font-size: 11.5pt; margin: 12px 0 4px; color: {ACCENT2}; }}
p {{ margin: 6px 0; text-align: justify; }}
b, strong {{ color:#122236; }}
em {{ color:#2a3a4d; }}
code {{ font-family:"DejaVu Sans Mono",monospace; font-size: 8.8pt; background:#f0f3f7; padding:1px 4px; border-radius:3px; }}
ul {{ margin:6px 0 6px 0; padding-left: 18px; }} li {{ margin:4px 0; }}
.cover {{ border-top: 8px solid {ACCENT}; padding-top: 22px; margin-bottom: 6px; }}
.cover .kicker {{ font-family:"DejaVu Sans",sans-serif; letter-spacing:2px; text-transform:uppercase; color:{ACCENT2}; font-size:9pt; }}
.cover h1 {{ font-size: 22pt; margin: 8px 0 4px; color:{ACCENT}; line-height:1.18; }}
.cover .meta {{ margin-top: 10px; font-size:9.5pt; color:#3a4a5f; font-family:"DejaVu Sans",sans-serif; }}
.cover .note {{ margin-top: 14px; font-style: italic; font-size:9.2pt; color:#5a6675; border-top:1px solid #dbe3ec; padding-top:9px; }}
"""

raw = open("docs/Vyuha_Professor_Response.md", encoding="utf-8").read()

# Passages OMITTED from the shared PDF only (the source .md keeps them, for the repo record).
raw = re.sub(r"I will be direct, because overclaiming novelty is the fastest way to lose a reviewer\.\s*",
             "", raw, flags=re.S)
raw = re.sub(r"\s*On that basis I fully agree the.*?invite the dismissal\.", "", raw, flags=re.S)
# Split off the top-level "# title" -> render it as a styled cover; convert the rest as body.
m = re.match(r"#\s+(.+?)\n(.*)", raw, flags=re.S)
title = m.group(1).strip() if m else "Response to Review"
body_md = (m.group(2) if m else raw).strip()
# The first paragraph after the title is the intro salutation; keep it in the body.
body_html = markdown.markdown(body_md, extensions=["extra", "sane_lists"])

cover = (f'<div class="cover"><div class="kicker">Vyuha Project · CSL6010 · IIT Jodhpur</div>'
         f'<h1>{title}</h1>'
         f'<div class="meta"><b>U E Sai Pavan Vamshi Krishna</b> (G25AIT2149)</div>'
         f'<div class="note">Point-by-point reply to the annotated review, mapped to the pages marked. '
         f'Every figure is taken from the evaluation records in the repository, reported with confidence '
         f'intervals; new results added since the review are collected in §7.4 of the technical document.</div></div>')

html = f"<html><head><meta charset='utf-8'><style>{CSS}</style></head><body>{cover}{body_html}</body></html>"
HTML(string=html).write_pdf("/tmp/Vyuha_Professor_Response.pdf")
print("PDF built -> /tmp/Vyuha_Professor_Response.pdf")
