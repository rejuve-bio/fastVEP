# fastVEP JSON API

A thin Python/FastAPI wrapper around `fastvep-web` that accepts variants in plain JSON and returns
rich annotation results — no VCF formatting required from the caller.

## How it works

```
caller  ──POST /annotate──▶  api (FastAPI)  ──POST /api/annotate──▶  fastvep-web (Rust)
         JSON variants                         VCF text in JSON body
         ◀──────────────────  JSON results  ◀──────────────────────
```

The wrapper converts your JSON variant objects to VCF format in memory, forwards the request to
`fastvep-web`, and returns the result unchanged.

## Prerequisites

1. `fastvep-web` must be running and reachable (see [../DEPLOYMENT.md](../DEPLOYMENT.md))
2. Genome data must be present (run `scripts/deploy-full.sh` once to download it)

## Quick start

**Standalone (dev):**
```bash
cd api
pip install -r requirements.txt
FASTVEP_URL=http://localhost:8080 uvicorn main:app --host 0.0.0.0 --port 8000
```

**Docker:**
```bash
docker build -t fastvep-api ./api
docker run -p 8000:8000 -e FASTVEP_URL=http://your-fastvep-web:8080 fastvep-api
```

**Docker Compose (recommended — starts both services):**
```bash
cp .env.example .env          # edit DATA_DIR to point at your genome data
docker-compose up --build
```

## Endpoints

### `GET /health`

Returns 200 when the API and `fastvep-web` backend are both up.

```bash
curl http://localhost:8000/health
```
```json
{"status": "ok", "backend": "ok"}
```

Returns 503 if `fastvep-web` is unreachable.

---

### `POST /annotate`

Annotate one or more variants.

**Request body:**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `variants` | `Variant[]` | — | List of variants (required unless using shorthand) |
| `acmg` | `bool` | `true` | Run ACMG-AMP classification |
| `pick` | `bool` | `false` | Return only the most severe consequence per variant |

**`Variant` object:**

| Field | Type | Example |
|-------|------|---------|
| `chr` | `string` | `"chr17"` |
| `pos` | `int` | `43071077` |
| `ref` | `string` | `"A"` |
| `alt` | `string` | `"T"` |

**Single-variant shorthand** (omit the `variants` wrapper):
```json
{"chr": "chr17", "pos": 43071077, "ref": "A", "alt": "T"}
```

**Batch request:**
```bash
curl -X POST http://localhost:8000/annotate \
  -H "Content-Type: application/json" \
  -d '{
    "variants": [
      {"chr": "chr17", "pos": 43071077, "ref": "A", "alt": "T"},
      {"chr": "chr1",  "pos": 69134,    "ref": "A", "alt": "G"}
    ]
  }'
```

**Example response (coding variant with ACMG):**
```json
{
  "count": 1,
  "time_ms": 12,
  "results": [
    {
      "seq_region_name": "chr17",
      "start": 43071077,
      "end": 43071077,
      "allele_string": "A/T",
      "most_severe_consequence": "missense_variant",
      "variant_type": "Snv",
      "transcript_consequences": [
        {
          "gene_id": "ENSG00000012048",
          "gene_symbol": "BRCA1",
          "transcript_id": "ENST00000357654",
          "biotype": "protein_coding",
          "canonical": 1,
          "mane_select": "ENST00000357654.9",
          "consequence_terms": ["missense_variant"],
          "impact": "MODERATE",
          "hgvsc": "ENST00000357654.9:c.5096A>T",
          "hgvsp": "ENSP00000350283.3:p.Asn1699Ile",
          "amino_acids": "N/I",
          "codons": "aaT/aaA",
          "exon": "18/24",
          "protein_start": 1699,
          "protein_end": 1699,
          "acmg": {
            "classification": "LikelyPathogenic",
            "shorthand": "LP",
            "criteria": [
              {"code": "PM2_Supporting", "met": true, "summary": "Absent in gnomAD"},
              {"code": "PP3", "met": true, "summary": "REVEL score 0.92"}
            ]
          },
          "clinvar": {
            "clinical_significance": "Pathogenic",
            "review_status": "criteria_provided,_multiple_submitters,_no_conflicts"
          }
        }
      ]
    }
  ]
}
```

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `FASTVEP_URL` | `http://localhost:8080` | URL of the `fastvep-web` backend |
| `CORS_ORIGINS` | `*` | Comma-separated allowed origins (e.g. `https://myapp.com,https://api.myapp.com`) |
