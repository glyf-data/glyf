use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};
use regex::Regex;
use serde::Deserialize;
use serde_json::Value;
use std::collections::{BTreeMap, BTreeSet};
use std::sync::OnceLock;

#[derive(Debug, thiserror::Error)]
pub enum CoreError {
    #[error("{0}")]
    Parse(String),
    #[error("{0}")]
    Manifest(String),
}

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

#[derive(Debug, Deserialize)]
struct RawManifest {
    nodes: Value,
    #[serde(default)]
    sources: Value,
}

pub fn parse_ggsql_text(
    text: &str,
    name: &str,
    path: Option<&str>,
) -> Result<GgsqlChart, CoreError> {
    reject_unsupported_draws(text)?;
    let normalized = normalize_for_ggsql(text);
    let validated = ggsql::validate::validate(&normalized)
        .map_err(|err| CoreError::Parse(err.to_string()))?;
    if !validated.valid() {
        let errors = validated
            .errors()
            .iter()
            .map(|err| err.message.as_str())
            .collect::<Vec<_>>()
            .join("; ");
        return Err(CoreError::Parse(errors));
    }
    if !validated.has_visual() {
        return Err(CoreError::Parse("missing VISUALISE section".to_string()));
    }

    let (legacy_sql, visual_lines) = split_legacy_parts(text)
        .ok_or_else(|| CoreError::Parse("missing VISUALISE section".to_string()))?;

    let sql = if legacy_sql.trim().is_empty() {
        validated.sql().trim().to_string()
    } else {
        legacy_sql.trim().to_string()
    };
    if sql.is_empty() {
        return Err(CoreError::Parse("missing SQL query section".to_string()));
    }

    let visualise_line = visual_lines
        .first()
        .ok_or_else(|| CoreError::Parse("missing VISUALISE section".to_string()))?;
    let visualise = parse_visualise(visualise_line)?;
    validate_required_roles(&visualise)?;

    let mut draw_type = None;
    let mut labels = BTreeMap::new();
    let mut config = BTreeMap::new();
    let mut interactions = Vec::new();
    let mut seen_interactions = BTreeSet::new();

    for line in visual_lines.iter().skip(1) {
        if let Some(draw) = parse_draw(line) {
            if !is_supported_draw(&draw) {
                return Err(CoreError::Parse(format!("unsupported chart type '{draw}'")));
            }
            draw_type = Some(legacy_draw_type(&draw).to_string());
            continue;
        }
        if let Some((key, value)) = parse_key_value_directive(line, "LABEL") {
            labels.insert(key, unquote(value).trim().to_string());
            continue;
        }
        if let Some((key, value)) = parse_key_value_directive(line, "CONFIG") {
            if key != "width" && key != "height" {
                return Err(CoreError::Parse(format!("unsupported CONFIG key '{key}'")));
            }
            let parsed = value.trim().parse::<i64>().map_err(|_| {
                CoreError::Parse(format!("invalid CONFIG {key}: expected a positive integer"))
            })?;
            if parsed <= 0 {
                return Err(CoreError::Parse(format!(
                    "invalid CONFIG {key}: expected a positive integer"
                )));
            }
            config.insert(key, parsed);
            continue;
        }
        if let Some(raw) = strip_keyword(line, "INTERACT") {
            for item in raw.split(',') {
                let interaction = item.trim().to_lowercase().replace('-', "_");
                if interaction.is_empty() {
                    continue;
                }
                match interaction.as_str() {
                    "tooltip" | "zoom" | "legend_filter" => {}
                    _ => {
                        return Err(CoreError::Parse(format!(
                            "unsupported interaction '{interaction}'; supported interactions: legend_filter, tooltip, zoom"
                        )));
                    }
                }
                if seen_interactions.insert(interaction.clone()) {
                    interactions.push(interaction);
                }
            }
            if interactions.is_empty() {
                return Err(CoreError::Parse(
                    "INTERACT requires at least one interaction".to_string(),
                ));
            }
            continue;
        }

        return Err(CoreError::Parse(format!(
            "unrecognised ggsql directive: {line}"
        )));
    }

    let draw_type =
        draw_type.ok_or_else(|| CoreError::Parse("missing DRAW directive".to_string()))?;

    Ok(GgsqlChart {
        path: path.unwrap_or(name).to_string(),
        name: name.to_string(),
        sql,
        visualise,
        draw_type,
        labels,
        config,
        interactions,
    })
}

pub fn load_manifest_json_text(text: &str, path: &str) -> Result<DbtManifest, CoreError> {
    let raw: RawManifest = serde_json::from_str(text)
        .map_err(|_| CoreError::Manifest(format!("Invalid manifest JSON: {path}")))?;
    let nodes_obj = raw
        .nodes
        .as_object()
        .ok_or_else(|| CoreError::Manifest("Invalid manifest: expected top-level 'nodes' object".to_string()))?;

    let mut nodes = Vec::new();
    for (unique_id, node) in nodes_obj {
        if let Some(relation) = manifest_relation(unique_id, node) {
            if matches!(relation.resource_type.as_str(), "model" | "seed" | "snapshot") {
                nodes.push(relation);
            }
        }
    }
    nodes.sort_by(|left, right| left.unique_id.cmp(&right.unique_id));

    let mut sources = Vec::new();
    if !raw.sources.is_null() {
        let sources_obj = raw
            .sources
            .as_object()
            .ok_or_else(|| CoreError::Manifest("Invalid manifest: expected top-level 'sources' object".to_string()))?;
        for (unique_id, source) in sources_obj {
            if let Some(relation) = manifest_relation(unique_id, source) {
                if relation.resource_type == "source" {
                    sources.push(relation);
                }
            }
        }
    }
    sources.sort_by(|left, right| left.unique_id.cmp(&right.unique_id));

    Ok(DbtManifest {
        path: path.to_string(),
        nodes,
        sources,
    })
}

pub fn resolve_refs_text(sql: &str, manifest: &DbtManifest) -> RefResolution {
    let mut refs = Vec::new();
    let mut missing_refs = Vec::new();
    let mut sources = Vec::new();
    let mut missing_sources = Vec::new();

    let resolved_refs = ref_regex()
        .replace_all(sql, |captures: &regex::Captures<'_>| {
            let name = captures.get(1).map(|m| m.as_str()).unwrap_or_default();
            refs.push(name.to_string());
            match relation_for_ref(manifest, name) {
                Some(relation) => relation,
                None => {
                    missing_refs.push(name.to_string());
                    captures.get(0).unwrap().as_str().to_string()
                }
            }
        })
        .to_string();

    let resolved_sql = source_regex()
        .replace_all(&resolved_refs, |captures: &regex::Captures<'_>| {
            let source_name = captures.get(1).map(|m| m.as_str()).unwrap_or_default();
            let table_name = captures.get(2).map(|m| m.as_str()).unwrap_or_default();
            sources.push((source_name.to_string(), table_name.to_string()));
            match relation_for_source(manifest, source_name, table_name) {
                Some(relation) => relation,
                None => {
                    missing_sources.push((source_name.to_string(), table_name.to_string()));
                    captures.get(0).unwrap().as_str().to_string()
                }
            }
        })
        .to_string();

    RefResolution {
        sql: resolved_sql,
        refs,
        missing_refs: dedupe_strings(missing_refs),
        sources,
        missing_sources: dedupe_pairs(missing_sources),
    }
}

fn normalize_for_ggsql(text: &str) -> String {
    let Some((sql, visual_lines)) = split_legacy_parts(text) else {
        return normalize_jinja_for_ggsql(text);
    };
    let Some(visualise_line) = visual_lines.first() else {
        return normalize_jinja_for_ggsql(text);
    };
    let mapping = strip_keyword(visualise_line, "VISUALISE")
        .or_else(|| strip_keyword(visualise_line, "VISUALIZE"))
        .unwrap_or("")
        .trim();
    let mut normalized_visual = vec!["VISUALISE".to_string()];

    for line in visual_lines.iter().skip(1) {
        if line.is_empty() {
            continue;
        }
        if let Some(draw) = parse_draw(line) {
            normalized_visual.push(normalize_draw_for_ggsql(line, &draw, mapping));
            continue;
        }
        if strip_keyword(line, "LABEL").is_some() {
            normalized_visual.push(line.to_string());
            continue;
        }
        if strip_keyword(line, "CONFIG").is_some() || strip_keyword(line, "INTERACT").is_some() {
            continue;
        }
        normalized_visual.push(line.to_string());
    }

    let normalized_sql = normalize_jinja_for_ggsql(sql.trim());
    if normalized_sql.is_empty() {
        normalized_visual.join("\n")
    } else {
        format!("{}\n{}", normalized_sql, normalized_visual.join("\n"))
    }
}

fn split_legacy_parts(text: &str) -> Option<(String, Vec<String>)> {
    let mut sql_lines = Vec::new();
    let mut visual_lines = Vec::new();
    let mut in_visual = false;

    for line in text.lines() {
        let trimmed = line.trim();
        if !in_visual
            && (strip_keyword(trimmed, "VISUALISE").is_some()
                || strip_keyword(trimmed, "VISUALIZE").is_some())
        {
            in_visual = true;
        }
        if in_visual {
            if !trimmed.is_empty() {
                visual_lines.push(trimmed.to_string());
            }
        } else {
            sql_lines.push(line);
        }
    }

    if visual_lines.is_empty() {
        None
    } else {
        Some((sql_lines.join("\n"), visual_lines))
    }
}

fn normalize_draw_for_ggsql(line: &str, draw: &str, mapping: &str) -> String {
    let raw = strip_keyword(line, "DRAW").unwrap_or_default();
    let tail = raw
        .trim_start()
        .get(draw.len()..)
        .map(str::trim_start)
        .unwrap_or_default();
    let ggsql_draw = match draw {
        "pie" => "bar",
        "scatter" => "point",
        other => other,
    };
    let mut normalized = format!("DRAW {ggsql_draw}");
    if !tail.is_empty() {
        normalized.push(' ');
        normalized.push_str(tail);
    }
    if !mapping.is_empty() && !contains_mapping_clause(&normalized) {
        normalized.push_str(" MAPPING ");
        normalized.push_str(mapping);
    }
    normalized
}

fn contains_mapping_clause(line: &str) -> bool {
    line.split_whitespace()
        .any(|part| part.eq_ignore_ascii_case("MAPPING"))
}

fn normalize_jinja_for_ggsql(text: &str) -> String {
    let replaced_refs = ref_regex()
        .replace_all(text, |captures: &regex::Captures<'_>| {
            captures
                .get(1)
                .map(|m| m.as_str())
                .unwrap_or("ref")
                .to_string()
        })
        .to_string();
    source_regex()
        .replace_all(&replaced_refs, |captures: &regex::Captures<'_>| {
            let source_name = captures.get(1).map(|m| m.as_str()).unwrap_or("source");
            let table_name = captures.get(2).map(|m| m.as_str()).unwrap_or("table");
            format!("{source_name}.{table_name}")
        })
        .to_string()
}

fn reject_unsupported_draws(text: &str) -> Result<(), CoreError> {
    for line in text.lines() {
        if let Some(draw) = parse_draw(line) {
            if !is_supported_draw(&draw) {
                return Err(CoreError::Parse(format!("unsupported chart type '{draw}'")));
            }
        }
    }
    Ok(())
}

fn parse_visualise(line: &str) -> Result<Vec<VisualiseMapping>, CoreError> {
    let raw = strip_keyword(line, "VISUALISE")
        .or_else(|| strip_keyword(line, "VISUALIZE"))
        .ok_or_else(|| CoreError::Parse("missing VISUALISE section".to_string()))?;
    let mut mappings = Vec::new();
    for raw_mapping in raw.split(',') {
        let parts = mapping_regex()
            .captures(raw_mapping)
            .ok_or_else(|| {
                CoreError::Parse(format!("invalid VISUALISE mapping: {}", raw_mapping.trim()))
            })?;
        mappings.push(VisualiseMapping {
            field: parts.get(1).unwrap().as_str().to_string(),
            role: parts.get(2).unwrap().as_str().to_string(),
        });
    }
    if mappings.is_empty() {
        return Err(CoreError::Parse(
            "VISUALISE requires at least one mapping".to_string(),
        ));
    }
    Ok(mappings)
}

fn validate_required_roles(visualise: &[VisualiseMapping]) -> Result<(), CoreError> {
    let roles = visualise
        .iter()
        .map(|mapping| mapping.role.as_str())
        .collect::<BTreeSet<_>>();
    if !roles.contains("x") || !roles.contains("y") {
        return Err(CoreError::Parse(
            "VISUALISE requires x and y mappings".to_string(),
        ));
    }
    Ok(())
}

fn parse_draw(line: &str) -> Option<String> {
    let raw = strip_keyword(line, "DRAW")?;
    let draw = raw.split_whitespace().next()?;
    Some(draw.trim().to_lowercase())
}

fn legacy_draw_type(draw: &str) -> &str {
    match draw {
        "point" => "scatter",
        other => other,
    }
}

fn is_supported_draw(draw: &str) -> bool {
    matches!(draw, "area" | "bar" | "line" | "pie" | "point" | "scatter")
}

fn parse_key_value_directive(line: &str, keyword: &str) -> Option<(String, String)> {
    let raw = strip_keyword(line, keyword)?;
    let (key, value) = raw.split_once("=>")?;
    Some((key.trim().to_lowercase(), value.trim().to_string()))
}

fn strip_keyword<'a>(line: &'a str, keyword: &str) -> Option<&'a str> {
    let trimmed = line.trim_start();
    let prefix = trimmed.get(..keyword.len())?;
    if !prefix.eq_ignore_ascii_case(keyword) {
        return None;
    }
    let rest = trimmed.get(keyword.len()..)?.trim_start();
    if rest.is_empty() {
        Some("")
    } else {
        Some(rest)
    }
}

fn unquote(value: String) -> String {
    let trimmed = value.trim();
    if trimmed.len() >= 2 {
        let first = trimmed.as_bytes()[0];
        let last = trimmed.as_bytes()[trimmed.len() - 1];
        if (first == b'\'' && last == b'\'') || (first == b'"' && last == b'"') {
            return trimmed[1..trimmed.len() - 1].to_string();
        }
    }
    trimmed.to_string()
}

fn manifest_relation(unique_id: &str, raw: &Value) -> Option<ManifestRelation> {
    let obj = raw.as_object()?;
    let name = obj.get("name")?.as_str()?.to_string();
    if name.is_empty() {
        return None;
    }
    let resource_type = obj
        .get("resource_type")
        .and_then(Value::as_str)
        .map(str::to_string)
        .unwrap_or_else(|| resource_type_from_unique_id(unique_id));
    if resource_type.is_empty() {
        return None;
    }
    let relation_name = obj
        .get("relation_name")
        .and_then(Value::as_str)
        .map(str::to_string)
        .or_else(|| relation_from_parts(obj))?;
    Some(ManifestRelation {
        unique_id: unique_id.to_string(),
        name,
        relation_name,
        resource_type,
        package_name: obj
            .get("package_name")
            .and_then(Value::as_str)
            .map(str::to_string),
        source_name: obj
            .get("source_name")
            .and_then(Value::as_str)
            .map(str::to_string),
    })
}

fn resource_type_from_unique_id(unique_id: &str) -> String {
    unique_id
        .split_once('.')
        .map(|(resource_type, _)| resource_type.to_string())
        .unwrap_or_default()
}

fn relation_from_parts(raw: &serde_json::Map<String, Value>) -> Option<String> {
    let identifier = raw
        .get("alias")
        .or_else(|| raw.get("identifier"))
        .or_else(|| raw.get("name"))
        .and_then(Value::as_str);
    let schema = raw.get("schema").and_then(Value::as_str);
    let database = raw.get("database").and_then(Value::as_str);
    let parts = [database, schema, identifier]
        .into_iter()
        .flatten()
        .filter(|part| !part.is_empty())
        .collect::<Vec<_>>();
    if parts.is_empty() {
        None
    } else {
        Some(parts.join("."))
    }
}

fn relation_for_ref(manifest: &DbtManifest, name: &str) -> Option<String> {
    manifest
        .nodes
        .iter()
        .find(|node| node.name == name)
        .map(|node| node.relation_name.clone())
}

fn relation_for_source(
    manifest: &DbtManifest,
    source_name: &str,
    table_name: &str,
) -> Option<String> {
    manifest
        .sources
        .iter()
        .find(|source| {
            source.source_name.as_deref() == Some(source_name) && source.name == table_name
        })
        .map(|source| source.relation_name.clone())
}

fn dedupe_strings(values: Vec<String>) -> Vec<String> {
    let mut seen = BTreeSet::new();
    let mut deduped = Vec::new();
    for value in values {
        if seen.insert(value.clone()) {
            deduped.push(value);
        }
    }
    deduped
}

fn dedupe_pairs(values: Vec<(String, String)>) -> Vec<(String, String)> {
    let mut seen = BTreeSet::new();
    let mut deduped = Vec::new();
    for value in values {
        if seen.insert(value.clone()) {
            deduped.push(value);
        }
    }
    deduped
}

fn mapping_regex() -> &'static Regex {
    static REGEX: OnceLock<Regex> = OnceLock::new();
    REGEX.get_or_init(|| {
        Regex::new(r"^\s*([A-Za-z_][\w.]*)\s+AS\s+([A-Za-z_][\w]*)\s*$").unwrap()
    })
}

fn ref_regex() -> &'static Regex {
    static REGEX: OnceLock<Regex> = OnceLock::new();
    REGEX
        .get_or_init(|| Regex::new(r#"\{\{\s*ref\(\s*['"]([^'"]+)['"]\s*\)\s*\}\}"#).unwrap())
}

fn source_regex() -> &'static Regex {
    static REGEX: OnceLock<Regex> = OnceLock::new();
    REGEX.get_or_init(|| {
        Regex::new(r#"\{\{\s*source\(\s*['"]([^'"]+)['"]\s*,\s*['"]([^'"]+)['"]\s*\)\s*\}\}"#)
            .unwrap()
    })
}

fn chart_to_python(py: Python<'_>, chart: GgsqlChart) -> PyResult<PyObject> {
    let dict = PyDict::new(py);
    dict.set_item("path", chart.path)?;
    dict.set_item("name", chart.name)?;
    dict.set_item("sql", chart.sql)?;
    let mappings = PyList::empty(py);
    for mapping in chart.visualise {
        let item = PyDict::new(py);
        item.set_item("field", mapping.field)?;
        item.set_item("role", mapping.role)?;
        mappings.append(item)?;
    }
    dict.set_item("visualise", mappings)?;
    dict.set_item("draw_type", chart.draw_type)?;
    dict.set_item("labels", chart.labels)?;
    dict.set_item("config", chart.config)?;
    dict.set_item("interactions", chart.interactions)?;
    Ok(dict.into())
}

fn manifest_to_python(py: Python<'_>, manifest: DbtManifest) -> PyResult<PyObject> {
    let dict = PyDict::new(py);
    dict.set_item("path", manifest.path)?;
    dict.set_item("nodes", relations_to_python(py, manifest.nodes)?)?;
    dict.set_item("sources", relations_to_python(py, manifest.sources)?)?;
    Ok(dict.into())
}

fn relations_to_python(py: Python<'_>, relations: Vec<ManifestRelation>) -> PyResult<PyObject> {
    let list = PyList::empty(py);
    for relation in relations {
        let item = PyDict::new(py);
        item.set_item("unique_id", relation.unique_id)?;
        item.set_item("name", relation.name)?;
        item.set_item("relation_name", relation.relation_name)?;
        item.set_item("resource_type", relation.resource_type)?;
        item.set_item("package_name", relation.package_name)?;
        item.set_item("source_name", relation.source_name)?;
        list.append(item)?;
    }
    Ok(list.into())
}

fn manifest_from_python(raw: &Bound<'_, PyDict>) -> PyResult<DbtManifest> {
    let path = raw
        .get_item("path")?
        .ok_or_else(|| PyValueError::new_err("manifest missing path"))?
        .extract::<String>()?;
    let nodes = raw
        .get_item("nodes")?
        .ok_or_else(|| PyValueError::new_err("manifest missing nodes"))?
        .extract::<Vec<BTreeMap<String, Option<String>>>>()?
        .into_iter()
        .map(relation_from_python_map)
        .collect::<PyResult<Vec<_>>>()?;
    let sources = raw
        .get_item("sources")?
        .ok_or_else(|| PyValueError::new_err("manifest missing sources"))?
        .extract::<Vec<BTreeMap<String, Option<String>>>>()?
        .into_iter()
        .map(relation_from_python_map)
        .collect::<PyResult<Vec<_>>>()?;
    Ok(DbtManifest {
        path,
        nodes,
        sources,
    })
}

fn relation_from_python_map(
    mut item: BTreeMap<String, Option<String>>,
) -> PyResult<ManifestRelation> {
    let required = |item: &mut BTreeMap<String, Option<String>>, key: &str| {
        item.remove(key)
            .flatten()
            .ok_or_else(|| PyValueError::new_err(format!("manifest relation missing {key}")))
    };
    Ok(ManifestRelation {
        unique_id: required(&mut item, "unique_id")?,
        name: required(&mut item, "name")?,
        relation_name: required(&mut item, "relation_name")?,
        resource_type: required(&mut item, "resource_type")?,
        package_name: item.remove("package_name").flatten(),
        source_name: item.remove("source_name").flatten(),
    })
}

fn resolution_to_python(py: Python<'_>, resolution: RefResolution) -> PyResult<PyObject> {
    let dict = PyDict::new(py);
    dict.set_item("sql", resolution.sql)?;
    dict.set_item("refs", resolution.refs)?;
    dict.set_item("missing_refs", resolution.missing_refs)?;
    dict.set_item("sources", resolution.sources)?;
    dict.set_item("missing_sources", resolution.missing_sources)?;
    Ok(dict.into())
}

fn py_err(err: CoreError) -> PyErr {
    PyValueError::new_err(err.to_string())
}

#[pyfunction]
#[pyo3(signature = (text, name, path=None))]
fn parse_ggsql(py: Python<'_>, text: &str, name: &str, path: Option<&str>) -> PyResult<PyObject> {
    chart_to_python(py, parse_ggsql_text(text, name, path).map_err(py_err)?)
}

#[pyfunction]
fn load_manifest_json(py: Python<'_>, text: &str, path: &str) -> PyResult<PyObject> {
    manifest_to_python(py, load_manifest_json_text(text, path).map_err(py_err)?)
}

#[pyfunction]
fn resolve_refs(py: Python<'_>, sql: &str, manifest: &Bound<'_, PyDict>) -> PyResult<PyObject> {
    let manifest = manifest_from_python(manifest)?;
    resolution_to_python(py, resolve_refs_text(sql, &manifest))
}

#[pymodule]
fn _core(_py: Python<'_>, module: &Bound<'_, PyModule>) -> PyResult<()> {
    module.add_function(wrap_pyfunction!(parse_ggsql, module)?)?;
    module.add_function(wrap_pyfunction!(load_manifest_json, module)?)?;
    module.add_function(wrap_pyfunction!(resolve_refs, module)?)?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parses_legacy_ggsql_with_ggsql_validation() {
        let chart = parse_ggsql_text(
            "SELECT month, revenue, region FROM fct_orders\n\nVISUALISE month AS x, revenue AS y, region AS color\nDRAW scatter\nLABEL title => 'Revenue'\nCONFIG width => 900\nINTERACT tooltip, legend-filter\n",
            "revenue",
            Some("revenue.ggsql"),
        )
        .unwrap();

        assert_eq!(chart.sql, "SELECT month, revenue, region FROM fct_orders");
        assert_eq!(chart.draw_type, "scatter");
        assert_eq!(chart.labels.get("title").unwrap(), "Revenue");
        assert_eq!(chart.config.get("width"), Some(&900));
        assert_eq!(chart.interactions, vec!["tooltip", "legend_filter"]);
        assert_eq!(chart.visualise[2].role, "color");
    }

    #[test]
    fn loads_manifest_and_resolves_refs() {
        let manifest = load_manifest_json_text(
            r#"{
              "nodes": {
                "model.basic.fct_orders": {
                  "name": "fct_orders",
                  "relation_name": "main.fct_orders"
                }
              },
              "sources": {
                "source.basic.raw.orders": {
                  "resource_type": "source",
                  "source_name": "raw",
                  "name": "orders",
                  "relation_name": "main.raw_orders"
                }
              }
            }"#,
            "target/manifest.json",
        )
        .unwrap();

        let resolved = resolve_refs_text(
            "select * from {{ ref('fct_orders') }} union all select * from {{ source('raw', 'orders') }}",
            &manifest,
        );
        assert_eq!(
            resolved.sql,
            "select * from main.fct_orders union all select * from main.raw_orders"
        );
        assert!(resolved.missing_refs.is_empty());
        assert!(resolved.missing_sources.is_empty());
    }

    #[test]
    fn reports_missing_refs() {
        let manifest = load_manifest_json_text(r#"{"nodes": {}, "sources": {}}"#, "manifest.json").unwrap();
        let resolved = resolve_refs_text("select * from {{ ref('missing') }}", &manifest);
        assert_eq!(resolved.missing_refs, vec!["missing"]);
    }

    #[test]
    fn preserves_legacy_pie_draw_type() {
        let chart = parse_ggsql_text(
            "SELECT region, sum(revenue) AS revenue FROM {{ ref('fct_orders') }} GROUP BY 1\n\nVISUALISE region AS x, revenue AS y\nDRAW pie\n",
            "revenue_share",
            None,
        )
        .unwrap();

        assert_eq!(chart.draw_type, "pie");
        assert_eq!(
            chart.sql,
            "SELECT region, sum(revenue) AS revenue FROM {{ ref('fct_orders') }} GROUP BY 1"
        );
    }

    #[test]
    fn uses_relation_parts_when_relation_name_is_absent() {
        let manifest = load_manifest_json_text(
            r#"{
              "nodes": {
                "model.basic.fct_orders": {
                  "name": "fct_orders",
                  "database": "analytics",
                  "schema": "main",
                  "alias": "orders"
                }
              }
            }"#,
            "manifest.json",
        )
        .unwrap();

        assert_eq!(
            relation_for_ref(&manifest, "fct_orders").as_deref(),
            Some("analytics.main.orders")
        );
    }
}
