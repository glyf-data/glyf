use serde::Deserialize;
use serde_json::Value;

use crate::error::CoreError;
use crate::models::{DbtManifest, ManifestRelation};

#[derive(Debug, Deserialize)]
struct RawManifest {
    nodes: Value,
    #[serde(default)]
    sources: Value,
    #[serde(default)]
    metadata: Value,
}

pub fn load_manifest_json_text(text: &str, path: &str) -> Result<DbtManifest, CoreError> {
    let raw: RawManifest = serde_json::from_str(text)
        .map_err(|_| CoreError::Manifest(format!("Invalid manifest JSON: {path}")))?;
    let nodes_obj = raw.nodes.as_object().ok_or_else(|| {
        CoreError::Manifest("Invalid manifest: expected top-level 'nodes' object".to_string())
    })?;

    let mut nodes = Vec::new();
    for (unique_id, node) in nodes_obj {
        if let Some(relation) = manifest_relation(unique_id, node) {
            if matches!(
                relation.resource_type.as_str(),
                "model" | "seed" | "snapshot"
            ) {
                nodes.push(relation);
            }
        }
    }
    nodes.sort_by(|left, right| left.unique_id.cmp(&right.unique_id));

    let mut sources = Vec::new();
    if !raw.sources.is_null() {
        let sources_obj = raw.sources.as_object().ok_or_else(|| {
            CoreError::Manifest("Invalid manifest: expected top-level 'sources' object".to_string())
        })?;
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
        generated_at: raw
            .metadata
            .get("generated_at")
            .and_then(Value::as_str)
            .filter(|value| !value.is_empty())
            .map(str::to_string),
        nodes,
        sources,
    })
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
        pii_columns: pii_columns(obj),
    })
}

/// The columns a node's `schema.yml` marks as PII, in manifest order.
///
/// Two spellings are honoured, because teams use both: `meta: {pii: true}`
/// and a `pii` tag. Anything else -- a string `"true"`, a differently named
/// meta key -- is not a classification; the caller has `glyf.yml` for that.
fn pii_columns(raw: &serde_json::Map<String, Value>) -> Vec<String> {
    let Some(columns) = raw.get("columns").and_then(Value::as_object) else {
        return Vec::new();
    };
    columns
        .iter()
        .filter(|(_, column)| column_is_pii(column))
        .map(|(name, column)| {
            column
                .get("name")
                .and_then(Value::as_str)
                .filter(|value| !value.is_empty())
                .unwrap_or(name)
                .to_string()
        })
        .collect()
}

fn column_is_pii(column: &Value) -> bool {
    let by_meta = column
        .get("meta")
        .and_then(|meta| meta.get("pii"))
        .and_then(Value::as_bool)
        .unwrap_or(false);
    let by_tag = column
        .get("tags")
        .and_then(Value::as_array)
        .map(|tags| {
            tags.iter()
                .filter_map(Value::as_str)
                .any(|tag| tag.eq_ignore_ascii_case("pii"))
        })
        .unwrap_or(false);
    by_meta || by_tag
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

#[cfg(test)]
mod tests {
    use crate::manifest::load_manifest_json_text;

    #[test]
    fn loads_manifest_nodes_and_sources() {
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

        assert_eq!(manifest.nodes[0].name, "fct_orders");
        assert_eq!(manifest.sources[0].relation_name, "main.raw_orders");
        assert!(manifest.nodes[0].pii_columns.is_empty());
        assert!(manifest.generated_at.is_none());
    }

    #[test]
    fn reads_the_manifest_build_time() {
        let manifest = load_manifest_json_text(
            r#"{
              "metadata": {"generated_at": "2026-09-02T10:00:00.000000Z"},
              "nodes": {
                "model.basic.fct_orders": {
                  "name": "fct_orders",
                  "relation_name": "main.fct_orders"
                }
              }
            }"#,
            "target/manifest.json",
        )
        .unwrap();

        assert_eq!(
            manifest.generated_at.as_deref(),
            Some("2026-09-02T10:00:00.000000Z")
        );
    }

    #[test]
    fn reads_pii_columns_from_meta_and_tags() {
        let manifest = load_manifest_json_text(
            r#"{
              "nodes": {
                "model.basic.dim_customers": {
                  "name": "dim_customers",
                  "relation_name": "main.dim_customers",
                  "columns": {
                    "customer_id": {"name": "customer_id"},
                    "email": {"name": "email", "meta": {"pii": true}},
                    "phone": {"name": "phone", "tags": ["PII", "contact"]},
                    "note": {"name": "note", "meta": {"pii": "true"}},
                    "opted_out": {"name": "opted_out", "meta": {"pii": false}}
                  }
                }
              }
            }"#,
            "target/manifest.json",
        )
        .unwrap();

        assert_eq!(manifest.nodes[0].pii_columns, vec!["email", "phone"]);
    }
}
