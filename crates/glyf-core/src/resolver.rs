use regex::Regex;
use std::collections::BTreeSet;
use std::sync::OnceLock;

use crate::models::{DbtManifest, RefResolution};

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

pub(crate) fn ref_regex() -> &'static Regex {
    static REGEX: OnceLock<Regex> = OnceLock::new();
    REGEX
        .get_or_init(|| Regex::new(r#"\{\{\s*ref\(\s*['"]([^'"]+)['"]\s*\)\s*\}\}"#).unwrap())
}

pub(crate) fn source_regex() -> &'static Regex {
    static REGEX: OnceLock<Regex> = OnceLock::new();
    REGEX.get_or_init(|| {
        Regex::new(r#"\{\{\s*source\(\s*['"]([^'"]+)['"]\s*,\s*['"]([^'"]+)['"]\s*\)\s*\}\}"#)
            .unwrap()
    })
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

#[cfg(test)]
mod tests {
    use crate::manifest::load_manifest_json_text;
    use crate::resolver::resolve_refs_text;

    #[test]
    fn resolves_refs_and_sources() {
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
        let manifest =
            load_manifest_json_text(r#"{"nodes": {}, "sources": {}}"#, "manifest.json").unwrap();
        let resolved = resolve_refs_text("select * from {{ ref('missing') }}", &manifest);
        assert_eq!(resolved.missing_refs, vec!["missing"]);
    }

    #[test]
    fn resolves_relation_parts_when_relation_name_is_absent() {
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

        let resolved = resolve_refs_text("select * from {{ ref('fct_orders') }}", &manifest);
        assert_eq!(resolved.sql, "select * from analytics.main.orders");
    }
}
