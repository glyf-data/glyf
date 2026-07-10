use serde::Deserialize;
use serde_json::Value;

use crate::error::CoreError;
use crate::models::{DbtManifest, ManifestRelation};

#[derive(Debug, Deserialize)]
struct RawManifest {
    nodes: Value,
    #[serde(default)]
    sources: Value,
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
    }
}
