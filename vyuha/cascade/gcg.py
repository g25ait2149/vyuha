"""White-box gradient attacks on the open-weight screens (pre-registration v4 §4, attacker A3).

Two screen kinds:
- causal-LM guards (S1 Qwen3Guard-0.6B, S5 Llama-Guard-3-1B): GCG minimises the unsafe-vs-safe verdict log-odds
  by optimising an appended suffix (letters + basic punctuation only, round-trip-stable, pre-mortem M8);
- the DeBERTa screen (S4): GCG minimises logit[harmful] - logit[safe] on the sequence classifier.

The probe screen (S3) has a frozen Qwen2.5-1.5B backbone with an LR head; we attack the backbone features with
the same suffix search against the probe's decision function (treated as a linear head on mean-pooled layer 18).

Final success is ALWAYS re-measured by scoring the final text through the real pipeline (L0 -> screen) outside
this module; the loss here is only the search signal.
"""
import numpy as np
import torch

# Suffix token vocabulary: ASCII letters, space and a little punctuation; filtered to tokens that survive a
# decode->encode round trip so the attacked string is exactly what the pipeline will re-score (M8).
def suffix_vocab(tok, limit=20000):
    ok = []
    for tid in range(min(tok.vocab_size, limit)):
        s = tok.decode([tid])
        if s and all(c.isascii() and (c.isalpha() or c in " ,.-") for c in s):
            if tok(s, add_special_tokens=False).input_ids == [tid]:
                ok.append(tid)
    return torch.tensor(ok)


def _embed(m):
    return m.get_input_embeddings()


def splice_user_suffix(tok, base_prompt_fn, user_text, kind, prefix, n_tokens):
    """Return (head_ids, tail_ids) so that head + <suffix of n_tokens> + tail equals the tokenisation of the REAL
    prompt (L0 view of user_text, with the suffix appended to the user message) + the forced verdict prefix.

    This guarantees the GCG search optimises the suffix at exactly the position it will occupy when the final
    text is re-scored through the pipeline. Uses a decode-stable filler and aligns by common prefix/suffix of the
    token ids, so BPE merges at the boundary are handled. Raises if alignment is not exact."""
    import torch
    filler = (' zz' * n_tokens).strip()                     # 'zz' is decode-stable and single-token in most BPEs
    with_f = base_prompt_fn(tok, user_text + ' ' + filler, kind) + prefix
    without = base_prompt_fn(tok, user_text, kind) + prefix
    a = tok(with_f, add_special_tokens=False).input_ids
    b = tok(without, add_special_tokens=False).input_ids
    # common prefix
    h = 0
    while h < len(a) and h < len(b) and a[h] == b[h]:
        h += 1
    # common suffix
    t = 0
    while t < len(a) - h and t < len(b) - h and a[-1 - t] == b[-1 - t]:
        t += 1
    head_ids = torch.tensor(a[:h])
    tail_ids = torch.tensor(a[len(a) - t:]) if t > 0 else torch.tensor([], dtype=torch.long)
    n_filler = len(a) - h - t
    return head_ids, tail_ids, n_filler


@torch.no_grad()
def _verdict_loss_batch(m, id_batch, u, s, chunk=32):
    """Unsafe-vs-safe verdict log-odds for a [B, L] batch of equal-length sequences, chunked for memory."""
    out = []
    for i in range(0, id_batch.shape[0], chunk):
        lg = m(input_ids=id_batch[i:i + chunk]).logits[:, -1, :].float()
        out.append(torch.logsumexp(lg[:, u], 1) - torch.logsumexp(lg[:, s], 1))
    return torch.cat(out)


def gcg_lm(tok, m, user_ids, prefix_ids, u_ids, s_ids, cand_vocab,
           n_tokens=20, steps=100, topk=256, batch=64, eval_chunk=32, early_tau=None, log=print):
    """Greedy-coordinate-gradient suffix search for a causal-LM guard. Returns (best_suffix_ids, best_loss).

    user_ids: the templated prompt token ids WITHOUT the verdict prefix; we insert the suffix right before the
    verdict prefix (prefix_ids). Loss = unsafe-vs-safe log-odds; the attacker minimises it."""
    device = m.device
    u = torch.tensor(sorted(u_ids), device=device); s = torch.tensor(sorted(s_ids), device=device)
    emb = _embed(m); W = emb.weight
    adv = cand_vocab[torch.randint(0, len(cand_vocab), (n_tokens,))].to(device)
    cand_vocab = cand_vocab.to(device)

    def build(adv_ids):
        return torch.cat([user_ids.to(device), adv_ids.to(device), prefix_ids.to(device)])

    best, best_loss = adv.clone(), float('inf')
    for step in range(steps):
        ids = build(adv)
        one = torch.zeros(len(adv), W.shape[0], device=device, requires_grad=True)
        one.data = torch.nn.functional.one_hot(adv, W.shape[0]).float()
        full = torch.cat([emb(user_ids.to(device)), one @ W, emb(prefix_ids.to(device))]).unsqueeze(0)
        logits = m(inputs_embeds=full).logits[0, -1, :].float()
        loss = torch.logsumexp(logits[u], 0) - torch.logsumexp(logits[s], 0)
        grad = torch.autograd.grad(loss, one)[0]                      # [n_tokens, vocab]
        topk_ids = (-grad[:, cand_vocab]).topk(topk, dim=1).indices    # positions in cand_vocab
        # sample batch candidate single-token swaps and keep the best by true loss
        with torch.no_grad():
            trials = adv.repeat(batch, 1)
            pos = torch.randint(0, n_tokens, (batch,), device=device)
            choice = torch.randint(0, topk, (batch,), device=device)
            trials[torch.arange(batch), pos] = cand_vocab[topk_ids[pos, choice]]
            # one padded batch forward pass (all trials share user/prefix and have equal length)
            uu, pp = user_ids.to(device), prefix_ids.to(device)
            id_batch = torch.stack([torch.cat([uu, t, pp]) for t in trials])
            losses = _verdict_loss_batch(m, id_batch, u, s, chunk=eval_chunk)
            j = int(losses.argmin())
            if float(losses[j]) < best_loss:
                best_loss, best, adv = float(losses[j]), trials[j].clone(), trials[j].clone()
        if log and step % 25 == 0:
            log(f'    gcg step {step}/{steps} loss {best_loss:.3f}')
        if early_tau is not None and best_loss < early_tau:
            if log:
                log(f'    gcg early stop at step {step}, loss {best_loss:.3f} < tau {early_tau:.3f}')
            break
    return best.cpu(), best_loss
