# Handy DuckDB / anndata queries

Run in `duckdb` after `INSTALL anndata FROM community; LOAD anndata;`.

## Exploring a remote CellxGene h5ad

```sql
-- attach a remote .h5ad over HTTPS as an AnnData database
attach 'https://datasets.cellxgene.cziscience.com/74c3403a-451c-4a62-84e0-d8a8e45c7ea7.h5ad' as remote (type anndata);

-- describe the obs (cell metadata) columns
desc remote.obs;

-- peek at a single column
select author_cell_type from remote.obs limit 10;
select author_cell_type from remote.obs limit 40;

-- total cell count
select count(*) from remote.obs;

-- cell-type composition (author annotation), most common first
select author_cell_type, count(*) cell_type
from remote.obs
group by author_cell_type
order by cell_type desc;
```

## Exploring the local workshop crop

```sql
-- attach the local crop (anndata: prefix form; run from data/cervical_tls_workshop/)
attach 'anndata:cervical_tls_crop.h5ad' as ad;

-- shape / structure summary (n_obs, n_vars, X format, obsm keys, exposed tables)
select * from ad.info;

-- list the tables the extension exposes (obs, var, X, obsm_spatial, info)
show all tables;

-- describe the obs (cell metadata) columns
desc ad.obs;

-- distinct cell types at tissue-prior alpha 10 (the _alpha1000 column)
select distinct cell_type_cdiam_miratyper_v1_constrained_alpha1000 from ad.obs;
```

## Scanning a whole collection of h5ad files with a wildcard

`anndata_scan_obs(glob)` reads the **obs** metadata of every file matching a glob
in one pass — no `attach` per file, no loading expression matrices — and adds a
`_file_name` column so you can tell rows apart by source file. Run `duckdb` from the
directory holding the files (or put the path in the glob).

```sql
-- e.g. from a directory of CITE-seq h5ads:
--   cd /path/to/cdiam_citeseq_human
-- one row per (file, condition) with the patient count in each
select _file_name, patient_condition_cdiam, count(distinct patient_id_cdiam)
from anndata_scan_obs('scCITE-*.h5ad')
group by all;
```

`group by all` groups by every non-aggregated select column, so adding/removing a
breakdown column needs no edit to the `group by`. Swap the glob (`*.h5ad`,
`scCITE-*.h5ad`, `data/**/*.h5ad`) to widen or narrow the collection.

## Links

* Extension Readme: https://github.com/honicky/anndata-duckdb-extension
* CellXGene datasets you can query: https://cellxgene.cziscience.com/datasets
