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
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ManifestRelation {
    pub unique_id: String,
    pub name: String,
    pub relation_name: String,
    pub resource_type: String,
    pub package_name: Option<String>,
    pub source_name: Option<String>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DbtManifest {
    pub path: String,
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
