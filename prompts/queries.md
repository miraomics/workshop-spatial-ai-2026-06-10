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

## Links

* Extension Readme: https://github.com/honicky/anndata-duckdb-extension
* CellXGene datasets you can query: https://cellxgene.cziscience.com/datasets
