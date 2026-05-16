# fastVEP JSON API

A Python/FastAPI wrapper around `fastvep-web` that lets you annotate genomic variants
by posting plain JSON — no VCF formatting required.

## How it works

```
Your app  ──POST /annotate──▶  api (FastAPI :8000)  ──POST /api/annotate──▶  fastvep-web (Rust :8080)
           {"chr","pos","ref","alt"}                    VCF text in body
           ◀────────────────────  full annotation JSON  ◀─────────────────────────────────────────────
```

The wrapper converts your variant objects to VCF in memory, forwards the request
to `fastvep-web`, and returns the full annotation result including ACMG-AMP
classification (enabled by default).

---

## Setup

> **First time on a fresh server?** Run `setup.sh` from the repo root instead —
> it handles everything (Docker build + genome data download) in one step:
> ```bash
> bash setup.sh minimal    # ~10 GB, ~30 min — GRCh38 + ClinVar
> bash setup.sh clinical   # ~20 GB, ~1 hr  — + dbSNP + model organisms
> bash setup.sh full       # ~55 GB, ~6 hrs — + gnomAD v4 + GRCh37 (recommended)
> docker compose up -d
> ```

If genome data is already downloaded, start both services from the **repo root**:

```bash
cp .env.example .env      # set DATA_DIR to where your genome data lives
docker compose up -d
```

The `api` service waits for `fastvep-web` to finish loading the GFF3 (~1–2 min)
before it starts accepting requests.

### Dev / standalone (no Docker)

```bash
# From the repo root — fastvep-web must already be running on port 8080
cd api
pip install -r requirements.txt
FASTVEP_URL=http://localhost:8080 uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

---

## Endpoints

### `GET /health`

Checks that the API is up and `fastvep-web` is reachable.

```bash
curl http://localhost:8000/health
```

```json
{"status": "ok", "backend": "ok"}
```

Returns `503` if `fastvep-web` cannot be reached.

---

### `POST /annotate`

Annotate one or more variants.

#### Request fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `variants` | `Variant[]` | — | List of variants to annotate |
| `acmg` | `bool` | `true` | Include ACMG-AMP classification in the response |
| `pick` | `bool` | `false` | Return only the most severe consequence per variant |

Each `Variant`:

| Field | Type | Example |
|-------|------|---------|
| `chr` | `string` | `"chr17"` |
| `pos` | `int` | `43071077` |
| `ref` | `string` | `"A"` |
| `alt` | `string` | `"T"` |

#### Single variant (shorthand)

You can omit the `variants` wrapper and post one variant directly:

```bash
curl -X POST http://localhost:8000/annotate \
  -H "Content-Type: application/json" \
  -d '{"chr": "chr17", "pos": 43071077, "ref": "A", "alt": "T"}'
```

#### Batch (multiple variants)

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

#### Disable ACMG (faster, smaller response)

```bash
curl -X POST http://localhost:8000/annotate \
  -H "Content-Type: application/json" \
  -d '{"chr": "chr1", "pos": 69134, "ref": "A", "alt": "G", "acmg": false}'
```

#### Example response

A coding variant in BRCA1 with the **full** genome tier (gnomAD + ClinVar loaded):

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
          "clinvar": {
            "clinical_significance": "Pathogenic",
            "review_status": "criteria_provided,_multiple_submitters,_no_conflicts"
          },
          "acmg": {
            "classification": "LikelyPathogenic",
            "shorthand": "LP",
            "criteria": [
              {"code": "PM2_Supporting", "met": true,  "summary": "Absent in gnomAD v4"},
              {"code": "PP5",            "met": true,  "summary": "ClinVar Pathogenic (2★)"},
              {"code": "BA1",            "met": false, "summary": "AF not above 5% threshold"}
            ]
          }
        }
      ]
    }
  ]
}
```

> **Note:** `acmg.criteria` depth depends on which SA databases are loaded.
> With the **minimal** tier (ClinVar only), frequency-based criteria like
> `PM2`, `BA1`, `BS1` will show `evaluated: false` — they require gnomAD,
> which is included in the **full** tier.

#### Annotation fields reference

| Field | Present when | Description |
|-------|-------------|-------------|
| `gene_symbol`, `gene_id` | Always (coding) | Gene identifiers |
| `consequence_terms`, `impact` | Always | SO consequence terms + HIGH/MODERATE/LOW/MODIFIER |
| `hgvsc`, `hgvsp`, `hgvsg` | Coding variants | HGVS nomenclature |
| `amino_acids`, `codons` | Missense | Amino acid and codon change |
| `exon`, `intron` | Exonic/intronic | Position within transcript |
| `canonical`, `mane_select` | Where applicable | Transcript flags |
| `clinvar` | ClinVar loaded | Clinical significance + review status |
| `gnomad` | gnomAD loaded (full tier) | Population allele frequencies |
| `dbsnp` | dbSNP loaded (clinical/full) | rs ID |
| `acmg` | `acmg: true` (default) | Full ACMG-AMP classification block |

---

## Error codes

| Code | Meaning |
|------|---------|
| `422` | Invalid request body (missing or wrong-type fields) |
| `503` | `fastvep-web` is not reachable |
| `504` | `fastvep-web` did not respond within 120 seconds |
| `502` | `fastvep-web` returned an empty or non-JSON response |

---

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `FASTVEP_URL` | `http://localhost:8080` | URL of the `fastvep-web` backend |
| `CORS_ORIGINS` | `*` | Comma-separated allowed CORS origins |

When running via Docker Compose these are set automatically.
To restrict CORS in production, set `CORS_ORIGINS=https://myapp.com` in `.env`.

---

## Running the tests

```bash
cd api
pip install -r requirements-dev.txt
pytest tests/ -v
```
