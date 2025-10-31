# Database

## Overview

- SQLite database: `database/quran_verses.db`
- Source: Tanzil Uthmani SQL dump (`database/Tanzil_quran-uthmani.sql`)
- Reference images: `database/reference_imgs/`

## Schema (key fields)

- `sura_number` (int)
- `aya_number` (int)
- `text_original` (Uthmani)
- `text_normalized` (optional)

## Initialization

- Provided DB is ready-to-use.
- To rebuild:

```bash
python database/scripts/init_db.py
```

## Reference Images

- Used for CV page-layout comparison
- One image per Medina page
- Place under `database/reference_imgs/`

## Access Layer

- `database/uthmani_db.py` provides read helpers for verses and page mapping.
