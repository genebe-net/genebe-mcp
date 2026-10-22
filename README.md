<div align="center">

# 🧬 GeneBe MCP

**Give your AI assistant real variant-interpretation data instead of guesses.**

Annotate and classify human genetic variants (ACMG, gnomAD, ClinVar, in-silico predictors) from Claude, Cursor,
VS Code and any other [MCP](https://modelcontextprotocol.io) client, powered by [GeneBe](https://genebe.net).

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
![Transport](https://img.shields.io/badge/MCP-Streamable%20HTTP-6f42c1)
![Read only](https://img.shields.io/badge/access-read--only-2da44e)
![No account](https://img.shields.io/badge/account-not%20required-2da44e)
![Research use only](https://img.shields.io/badge/use-research%20only-orange)

`https://mcp.genebe.net/v1/mcp`

</div>

---

## Why

Language models are bad at remembering the clinical status of a specific variant. They sound confident and are often
wrong. GeneBe MCP lets the assistant look the variant up and answer from data: a **transparent, points-based ACMG
classification** with every criterion explained, together with population frequencies, predictor scores, ClinVar and
transcript consequences.

> *"Is NM_005577.4:c.4195A>C benign?"*  
> *"What is chr6-160585140-T-G? Explain why it is classified that way."*  
> *"Convert rs41272110 to hg38 and list its consequences on each transcript."*

For example, `chr6-160585140-T-G` (rs41272110, *LPA*) comes back as **Benign, −9 points** with criteria **BA1** and
**BP4**, plus the data behind them and a link to the GeneBe page.

## What you get

- **Any notation in:** genomic coordinates, HGVS, rsID or SPDI; hg19, hg38 and T2T supported through liftover.
- **Verdict you can audit:** ACMG classification with points and the reasoning for each criterion, not a black-box label.
- **Evidence in one call:** gnomAD frequencies, in-silico predictors, ClinVar, per-transcript consequences (HGVS c./p.,
  impact), gene details with MANE Select and ClinGen gene–disease validity.
- **Compact answers:** large lists are capped, so one call costs roughly 1–3k tokens, and every result also carries
  structured data that follows the tool's output schema.
- **Links back to GeneBe**, so the human can check the source.

## Connect in a minute

No sign-up, no API key. The server is remote; you only add its URL.

<details open>
<summary><b>Claude Code</b></summary>

```bash
claude mcp add --transport http genebe https://mcp.genebe.net/v1/mcp
```

</details>

<details>
<summary><b>Claude (web and desktop)</b></summary>

Settings → Connectors → *Add custom connector*, then enter `https://mcp.genebe.net/v1/mcp`.

</details>

<details>
<summary><b>ChatGPT</b></summary>

Open [chatgpt.com/plugins](https://chatgpt.com/plugins), click **Add (+)** → **Add custom MCP**, and enter
`https://mcp.genebe.net/v1/mcp`.

</details>

<details>
<summary><b>Cursor</b></summary>

Add to `~/.cursor/mcp.json`:

```json
{ "mcpServers": { "genebe": { "url": "https://mcp.genebe.net/v1/mcp" } } }
```

</details>

<details>
<summary><b>VS Code</b></summary>

Add to `.vscode/mcp.json`:

```json
{ "servers": { "genebe": { "type": "http", "url": "https://mcp.genebe.net/v1/mcp" } } }
```

</details>

<details>
<summary><b>Any other client / try it with curl</b></summary>

Any client that supports remote MCP over Streamable HTTP works. Try it from a terminal:

```bash
curl -s -X POST https://mcp.genebe.net/v1/mcp \
  -H 'Content-Type: application/json' -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"annotate_variant","arguments":{"variant":"chr6-160585140-T-G"}}}'
```

More examples: [USAGE.md](USAGE.md).

</details>

## Tools

| Tool | What it does |
|---|---|
| `annotate_variant` | **Start here.** Any notation → ACMG verdict, points and criteria, frequencies, predictor scores, ClinVar, consequences, GeneBe links |
| `explain_acmg_decision_path` | Why each classification criterion applied, in plain text |
| `convert_variant` | HGVS / rsID / SPDI → hg38 coordinates |
| `get_variant_effects` | Per-transcript consequences (HGVS c./p., impact) |
| `get_gene` | Gene identifiers, location, MANE Select, ClinGen gene–disease validity, transcripts |
| `liftover_coordinate` | Positions, intervals or variants between hg19 / hg38 / t2t |

The default genome build is hg38.

## Trust and privacy

- **Read-only.** No tool changes anything, anywhere.
- **No account, no key** needed to use the hosted server.
- **Single variants only.** No patient data, no VCF files, no samples are sent or stored.
- **Nothing is stored and variant input is not logged** by the MCP server.
- **Transparent classification.** Results come from GeneBe's points-based ACMG implementation; the reasoning is
  returned with the verdict, so you and the assistant can check it.
- **Open source** under the [MIT license](LICENSE); you can read exactly what the server does, or
  [run your own copy](DEVELOPMENT.md).
- **Research use only.** This is not a medical device and not a diagnosis. Classifications must be reviewed by a
  qualified specialist before any clinical use.

## Roadmap

Today GeneBe MCP answers questions about single variants. We plan to grow it into a workspace your assistant can use
on your own data. None of the items below is available yet, and the order may change.

- [ ] **Sign-in**, so the assistant can act on your GeneBe account
- [ ] **Your own samples:** view and edit sample details and annotations
- [ ] **Search your cohort:** find a variant across your own set of samples
- [ ] **Upload samples** from the assistant
- [ ] **Supervise computations:** start analyses, follow their progress and read the results

Ideas or requests? Open an issue or write to us via [genebe.net](https://genebe.net).

## Data sources

Results combine data from GeneBe, gnomAD, ClinVar, UniProt, ClinGen and dbNSFP predictors. Please check each source's
license terms before redistributing the data.

## Contributing and self-hosting

Want to run your own instance or change the code? See [DEVELOPMENT.md](DEVELOPMENT.md). Issues and pull requests are
welcome.

---

<div align="center">

Made by the <a href="https://genebe.net">GeneBe</a> team · <a href="LICENSE">MIT</a> · Research use only

</div>
