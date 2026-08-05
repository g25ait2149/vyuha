# Response to review comments — Vyuha Technical Document

Thank you for the careful read and the encouragement. Below are point-by-point answers to each
comment, mapped to the page you annotated. Every number cited is from the evaluation records in the
repository (model card / paper), not restated from memory. I have also made two concrete edits to the
document itself (noted at the end).

## 1. The QLoRA guard — "explain it more" and "is it not performing well?" (p7 underline, p13 chart)

The tuned QLoRA guard (Qwen2.5-1.5B + LoRA, 4-bit) is a **jailbreak detector**, and on that task it
performs well: cross-benchmark **ROC-AUC 0.72–0.92 on jailbreak sets it never trained on**
(out-of-distribution generalisation), at a false-refusal rate of 0.03–0.06. That is the "great
detection rate" the text refers to.

The page-13 chart plotted only two axes — harmful-topic (XSTest) and semantic (PAIR) — where the guard
scores 0.00 and 0.03. That is **inert by design**, not failure: detecting harmful topics and fluent
persuasion is a different task, owned by the L2 content guard (Qwen3Guard), not by a jailbreak
classifier. The chart made the guard look like a failure because it omitted the guard's own strong
axis. **I have fixed the chart** — it now shows a second panel with the guard's OOD jailbreak
ROC-AUC (0.72–0.92), clearly labelled as a different metric.

Honest caveat I want to state plainly: the QLoRA guard is the **most marginal component** in the
stack. Its only justification is better OOD generalisation to novel jailbreak phrasings than the linear
L1 detector gives. The paper already lists it under "components that did not clearly earn their place."

## 2. "Is it an existing technique?" (p13 circle)

Yes. QLoRA (Dettmers et al., 2023) is a standard fine-tuning method, and fine-tuning a guard classifier
this way is common practice (Llama Guard, ShieldGemma are fine-tuned guards). What is *ours* is the
specific trained adapter, the published artifact, and the measured finding that it behaves as a
jailbreak specialist rather than a content guard — **not** a new technique. I do not claim the method
is novel.

## 3. "Content guards are stronger on semantics" — is the whole stack weaker on semantics? (p14 underline)

No — the opposite. Inside Vyuha the surface L1 detector and the QLoRA guard are intentionally weak on
semantics (L1 flags only **6.8%** of real PAIR jailbreaks). But the L2 content guard **Qwen3Guard
carries semantics at 90.3% on PAIR and 79% on XSTest**, at 4.8% over-refusal. So the stack's semantic
coverage equals Qwen3Guard's, which is strong.

The sentence means: rather than train our *own* semantic model to compete with mature content guards,
we **compose the best existing one** and route to it through the selective cascade. The honest boundary
is narrower than "weaker": Vyuha does not *add* semantic capability beyond the composed guard — its
semantic ceiling is Qwen3Guard's. That is a composition boundary, not a coverage weakness.

## 4. Novelty — "highlight the novelty of this (L2)" and "are all operations borrowed or proposed?" (p7, p8, p2)

I will be direct, because overclaiming novelty is the fastest way to lose a reviewer. **No component of
Vyuha is a new algorithm.** The borrowed, cited pieces include Dual-LLM (Willison), CaMeL as the target
(DeepMind), Qwen3Guard, QLoRA, PSI drift monitoring, canary tokens, and the PAIR / AgentDojo / XSTest
benchmarks.

On **L2 specifically** (your "highlight novelty of this" note): this is the layer with the *least*
novelty. Both models are existing. L2's only defensible contributions are compositional — **selective
invocation** (the expensive guard runs only on the cascade's uncertain band, which is what makes it
affordable on free compute) and **measured complementarity** (we quantify that the content guard owns
semantics while the tuned guard owns OOD jailbreak generalisation). I would not manufacture a novelty
claim at L2; the numbers will not support one.

Where the closer-to-genuine contributions actually are (all measured, not asserted):

- **L0 adaptive multi-view de-spacing** — closed the character-spacing gap from ASR **0.83 → 0.00** and
  *generalised to a held-out wider-spacing variant it never trained on*. This generalisation is the
  strongest single novelty claim.
- **The augmentation-vs-normalisation ablation** — a measured finding that normalisation alone leaves
  an adaptive attacker at ~1.00 ASR, and it is the adversarial augmentation that closes it to 0.00 at
  zero benign false positives.
- **The selective-cascade division of labour, reproducible on a single free GPU** — the "which layer
  catches what" evidence.

So the honest framing is that **Vyuha is a systems, measurement, and reproducibility contribution, not
an algorithmic one.** On that basis I fully agree with your suggestion of the **EACL 2027 industry /
applied track** — those venues explicitly reward relevance, honest evaluation, and reproducibility over
a new equation, which is exactly this project's profile. I have also softened the executive-summary
line you underlined ("No single piece is novel") to name the real contributions rather than invite the
dismissal.

## Document edits made in response

1. **Page-13 chart** — added a second panel showing the tuned QLoRA guard on its own axis (OOD
   jailbreak ROC-AUC 0.72–0.92, a different metric from the detection rate), with a caption explaining
   the near-zero bars are by design.
2. **Executive summary (page 2)** — reworded to: "No single *component algorithm* is new… the
   contributions are the measured composition, the adaptive-robustness ablation, and reproducibility on
   free compute."
