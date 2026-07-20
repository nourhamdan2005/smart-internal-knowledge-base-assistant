# Query performance baseline

Recorded before the controlled query-latency optimization phase.

## Environment and results

- Model: `llama3.2:latest`
- Embedding model: `nomic-embed-text:latest`
- Mean completion time: 32.82 seconds
- Median completion time: 36.97 seconds
- Minimum completion time: 4.75 seconds
- Maximum completion time: 67.06 seconds
- LLM share of request duration: 97.98%
- Approximate output speed: 3.96 tokens/second
- Retrieval duration: approximately 0.6–0.75 seconds
- Context chunks: usually 3–5
- Request timeout: 120 seconds

## Fixed comparison questions

1. What is the company remote work policy?
2. What are the requirements for passwords and multi-factor authentication?
3. Summarize employee responsibilities for remote work, availability, and information security.
4. What leave and workplace policies apply to employees? (HR category filter)
5. What is the company policy for operating a submarine?

The retrieval parameters, chunking, embedding model, hybrid weights, semantic
thresholds, and Qdrant collection must remain unchanged during latency work.
