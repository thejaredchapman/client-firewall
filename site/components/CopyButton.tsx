"use client";

import { useState } from "react";

export function CopyButton({ text, label = "Copy" }: { text: string; label?: string }) {
  const [status, setStatus] = useState<"idle" | "copied" | "failed">("idle");

  async function copy() {
    try {
      await navigator.clipboard.writeText(text);
      setStatus("copied");
    } catch {
      setStatus("failed");
    }
  }

  const text_ = status === "copied" ? "Copied" : status === "failed" ? "Select the text and copy it manually" : label;
  return (
    <button type="button" className="copy" onClick={copy}>
      {text_}
    </button>
  );
}
