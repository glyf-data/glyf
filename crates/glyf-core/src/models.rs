use std::collections::BTreeMap;

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct VisualiseMapping {
    pub field: String,
    pub role: String,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct GgsqlChart {
    pub path: String,
    pub name: String,
    pub sql: String,
    pub visualise: Vec<VisualiseMapping>,
    pub draw_type: String,
    pub labels: BTreeMap<String, String>,
    pub config: BTreeMap<String, i64>,
    pub interactions: Vec<String>,
    /// Whether the query orders its own rows. A chart whose query does not is
    /// rendered from whatever order the warehouse returned, which is not
    /// stable between builds.
    pub has_order_by: bool,
    /// Set when the SQL did not parse. Never an error: the warehouse is the
    /// judge of the SQL, and a parser can lag a dialect. Carries the parser's
    /// message with its line and column.
    pub sql_warning: Option<String>,
    /// Every column name the SQL mentions, lower-cased and de-duplicated: the
    /// last part of each identifier, wherever it appears. Empty when the SQL
    /// did not parse. `glyf impact` reads it to find the charts a column
    /// change touches.
    pub sql_columns: Vec<String>,
    /// Whether any SELECT in the query uses `*`, which reads columns the
    /// query never names.
    pub sql_selects_star: bool,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ManifestRelation {
    pub unique_id: String,
    pub name: String,
    pub relation_name: String,
    pub resource_type: String,
    pub package_name: Option<String>,
    pub source_name: Option<String>,
    /// Columns the dbt project classifies as PII: `meta: {pii: true}` or a
    /// `pii` tag on the column in `schema.yml`.
    pub pii_columns: Vec<String>,
    /// The nodes this one reads, as dbt records them in `depends_on.nodes`:
    /// unique ids of models, seeds, snapshots and sources. Lineage follows
    /// these back from a chart to the raw tables.
    pub parents: Vec<String>,
    /// The file dbt read the node from, `original_file_path`.
    pub path: Option<String>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DbtManifest {
    pub path: String,
    /// `metadata.generated_at` from the manifest: when dbt last built it.
    pub generated_at: Option<String>,
    pub nodes: Vec<ManifestRelation>,
    pub sources: Vec<ManifestRelation>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct RefResolution {
    pub sql: String,
    pub refs: Vec<String>,
    pub missing_refs: Vec<String>,
    pub sources: Vec<(String, String)>,
    pub missing_sources: Vec<(String, String)>,
}
