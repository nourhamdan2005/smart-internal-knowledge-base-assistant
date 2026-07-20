# Controlled query-latency optimization

## Runtime inspection

Commands used included the Ollama `/api/version`, `/api/show`, `/api/ps`, and
`/api/tags` endpoints, `nvidia-smi`, `powercfg /getactivescheme`, and Windows
process inspection.

- Ollama: 0.31.2
- Generation model: Llama 3.2, 3.2B parameters, GGUF `Q4_K_M`
- Embedding model: nomic-embed-text, 137M parameters, F16
- GPU: NVIDIA GeForce MX130, 2 GB VRAM, CUDA driver 581.95
- Windows power scheme: Balanced
- Llama VRAM residency reported by Ollama: 888,930,303 bytes
- Embedding-model VRAM residency: 323,150,151 bytes
- Both `llama-server.exe` processes were visible to `nvidia-smi`
- The Llama model is partially, not fully, GPU-resident

CPU and system-memory details could not be read through CIM because the local
account was denied access. No uninstalled alternative generation models were
downloaded during this phase. The only locally available generation model was
`llama3.2:latest`, so no defensible alternative-model quality comparison was
possible.

## Explicit generation configuration

The application now centralizes temperature 0.2, top-p 0.9, top-k 40,
repeat penalty 1.1, context 4096, keep-alive 5 minutes, and a 180-second request
safety timeout. Streaming is enabled independently. The model's existing stop
sequences remain model-defined; no seed is set.

Output budgets are deterministic: ordinary factual questions use up to 96
tokens, list/procedure/summary/explanation requests use 192, and explicitly
detailed requests may use up to 320. The prompt requests concise, complete,
grounded answers without repetitive framing.

## After benchmark

The fixed five-question run followed one excluded warm-up.

| Case | Retrieval ms | First token ms | Total ms | Tokens | tok/s | Chars | Chunks |
|---|---:|---:|---:|---:|---:|---:|---:|
| HR factual | 3,788 | 36,838 | 48,730 | 39 | 3.278 | 174 | 5 |
| IT/security | 835 | 45,698 | 76,175 | 96 | 3.150 | 487 | 5 |
| Multi-chunk | 783 | 45,231 | 90,453 | 138 | 3.052 | 830 | 5 |
| HR filter | 797 | 14,918 | 42,567 | 96 | 3.473 | 488 | 3 |
| Weak evidence | 799 | 46,028 | 49,498 | 12 | 3.462 | 60 | 5 |

- Mean first token: 37.74 seconds; median: 45.23 seconds
- Mean completion: 61.48 seconds; median: 49.50 seconds
- Baseline mean/median: 32.82/36.97 seconds
- Mean completion regressed 87.3%; median regressed 33.9%
- Mean measured generation speed: 3.283 tokens/second versus 3.96 baseline
- Answer characters fell from 2,764 to 2,039 (26.2%)

The warm-up took 107.19 seconds and retrieval took 5.46 seconds. Subsequent
retrieval returned below one second except the first measured HR request. A
later non-stream weak-evidence request completed in 6.49 seconds and returned
the same exact refusal text as streaming, demonstrating severe runtime-state
variance rather than HTTP buffering or a content-contract difference.

Streaming materially improves progressive presentation once Ollama emits its
first token, but cannot meet a sub-three-second first-token target on this
observed hardware/runtime state. Production deployment should use a stronger
accelerator or validate a smaller model on the fixed quality suite before a
model replacement is approved.
