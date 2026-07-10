use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};
use std::collections::BTreeMap;

use crate::dashboard::validate_dashboard_json_text;
use crate::error::CoreError;
use crate::ggsql::parse_ggsql_text;
use crate::manifest::load_manifest_json_text;
use crate::models::{DbtManifest, GgsqlChart, ManifestRelation, RefResolution};
use crate::resolver::resolve_refs_text;

pub(crate) fn register(module: &Bound<'_, PyModule>) -> PyResult<()> {
    module.add_function(wrap_pyfunction!(parse_ggsql, module)?)?;
    module.add_function(wrap_pyfunction!(load_manifest_json, module)?)?;
    module.add_function(wrap_pyfunction!(resolve_refs, module)?)?;
    module.add_function(wrap_pyfunction!(validate_dashboard_json, module)?)?;
    Ok(())
}

fn chart_to_python(py: Python<'_>, chart: GgsqlChart) -> PyResult<Py<PyAny>> {
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
    Ok(dict.into_any().unbind())
}

fn manifest_to_python(py: Python<'_>, manifest: DbtManifest) -> PyResult<Py<PyAny>> {
    let dict = PyDict::new(py);
    dict.set_item("path", manifest.path)?;
    dict.set_item("nodes", relations_to_python(py, manifest.nodes)?)?;
    dict.set_item("sources", relations_to_python(py, manifest.sources)?)?;
    Ok(dict.into_any().unbind())
}

fn relations_to_python(py: Python<'_>, relations: Vec<ManifestRelation>) -> PyResult<Py<PyAny>> {
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
    Ok(list.into_any().unbind())
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

fn resolution_to_python(py: Python<'_>, resolution: RefResolution) -> PyResult<Py<PyAny>> {
    let dict = PyDict::new(py);
    dict.set_item("sql", resolution.sql)?;
    dict.set_item("refs", resolution.refs)?;
    dict.set_item("missing_refs", resolution.missing_refs)?;
    dict.set_item("sources", resolution.sources)?;
    dict.set_item("missing_sources", resolution.missing_sources)?;
    Ok(dict.into_any().unbind())
}

fn py_err(err: CoreError) -> PyErr {
    PyValueError::new_err(err.to_string())
}

#[pyfunction]
#[pyo3(signature = (text, name, path=None))]
fn parse_ggsql(py: Python<'_>, text: &str, name: &str, path: Option<&str>) -> PyResult<Py<PyAny>> {
    chart_to_python(py, parse_ggsql_text(text, name, path).map_err(py_err)?)
}

#[pyfunction]
fn load_manifest_json(py: Python<'_>, text: &str, path: &str) -> PyResult<Py<PyAny>> {
    manifest_to_python(py, load_manifest_json_text(text, path).map_err(py_err)?)
}

#[pyfunction]
fn resolve_refs(py: Python<'_>, sql: &str, manifest: &Bound<'_, PyDict>) -> PyResult<Py<PyAny>> {
    let manifest = manifest_from_python(manifest)?;
    resolution_to_python(py, resolve_refs_text(sql, &manifest))
}

#[pyfunction]
fn validate_dashboard_json(text: &str, path: &str) -> PyResult<()> {
    validate_dashboard_json_text(text, path).map_err(py_err)
}
