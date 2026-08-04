"""
Vyuha L2 (P3) - LoRA / QLoRA fine-tune a small guard LLM as a binary safety
classifier (P(unsafe)). Designed for a single free **T4** (4-bit base + LoRA adapter).

Trains on the assembled Vyuha corpus (de-obfuscation-normalized). Saves a small LoRA
adapter + tokenizer to `out_dir` - published to HF and loaded by guard_model.TunedGuard.

    from vyuha.guard.train_guard import train_guard
    from eval import datasets as D
    tr, _ = D.assemble(verbose=False)
    train_guard(tr, base_model="Qwen/Qwen2.5-1.5B", out_dir="vyuha_guard")

Requires: transformers, peft, bitsandbytes, accelerate, datasets, torch (GPU).
Version-adaptive: handles transformers' tokenizer->processing_class and
evaluation_strategy->eval_strategy renames.
"""
import inspect
import pandas as pd


def train_guard(train_df, val_df=None, base_model="Qwen/Qwen2.5-1.5B",
                out_dir="vyuha_guard", epochs=1, lr=2e-4, bsz=8, grad_accum=2,
                max_len=256, use_4bit=True, balance=True, seed=42):
    import torch
    from datasets import Dataset
    from transformers import (AutoTokenizer, AutoModelForSequenceClassification,
                              TrainingArguments, Trainer, DataCollatorWithPadding,
                              BitsAndBytesConfig)
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training, TaskType
    from vyuha.normalize.normalize import normalize

    df = train_df.copy()
    if balance:                                  # downsample benign to ~3x the positives
        pos = df[df.label == 1]
        neg = df[df.label == 0].sample(min((df.label == 0).sum(), len(pos) * 3), random_state=seed)
        df = pd.concat([pos, neg]).sample(frac=1, random_state=seed).reset_index(drop=True)
    print(f"train rows: {len(df)} (pos={int((df.label==1).sum())}, neg={int((df.label==0).sum())})")

    tok = AutoTokenizer.from_pretrained(base_model)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token

    quant = (BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                                bnb_4bit_compute_dtype=torch.float16) if use_4bit else None)
    model = AutoModelForSequenceClassification.from_pretrained(
        base_model, num_labels=2, quantization_config=quant,
        device_map="auto", torch_dtype=torch.float16)
    model.config.pad_token_id = tok.pad_token_id
    if use_4bit:
        model = prepare_model_for_kbit_training(model)
    model = get_peft_model(model, LoraConfig(
        task_type=TaskType.SEQ_CLS, r=16, lora_alpha=32, lora_dropout=0.05,
        target_modules="all-linear", modules_to_save=["score"]))
    model.print_trainable_parameters()

    def prep(d):
        ds = Dataset.from_dict({"text": [normalize(t, full=True) for t in d.text.tolist()],
                                "labels": d.label.astype(int).tolist()})
        return ds.map(lambda b: tok(b["text"], truncation=True, max_length=max_len), batched=True)

    train_ds = prep(df)
    eval_ds = prep(val_df) if val_df is not None else None

    # ---- version-adaptive TrainingArguments ----
    ta = dict(output_dir=out_dir, num_train_epochs=epochs, learning_rate=lr,
              per_device_train_batch_size=bsz, per_device_eval_batch_size=bsz,
              gradient_accumulation_steps=grad_accum, fp16=True, logging_steps=25,
              save_strategy="no", report_to=[])
    ta_params = inspect.signature(TrainingArguments.__init__).parameters
    ev = "epoch" if eval_ds is not None else "no"
    if "eval_strategy" in ta_params:
        ta["eval_strategy"] = ev
    elif "evaluation_strategy" in ta_params:
        ta["evaluation_strategy"] = ev
    args = TrainingArguments(**ta)

    # ---- version-adaptive Trainer (tokenizer -> processing_class) ----
    tr_kwargs = dict(model=model, args=args, train_dataset=train_ds, eval_dataset=eval_ds,
                     data_collator=DataCollatorWithPadding(tok))
    tr_params = inspect.signature(Trainer.__init__).parameters
    if "processing_class" in tr_params:
        tr_kwargs["processing_class"] = tok
    elif "tokenizer" in tr_params:
        tr_kwargs["tokenizer"] = tok
    Trainer(**tr_kwargs).train()

    model.save_pretrained(out_dir)
    tok.save_pretrained(out_dir)
    print("Vyuha guard adapter saved ->", out_dir)
    return out_dir
