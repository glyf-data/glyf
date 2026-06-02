mod dashboard;
mod error;
mod ggsql;
mod manifest;
mod models;
mod python;
mod resolver;

pub use error::CoreError;
pub use dashboard::validate_dashboard_json_text;
pub use ggsql::parse_ggsql_text;
pub use manifest::load_manifest_json_text;
pub use models::{
    DbtManifest, GgsqlChart, ManifestRelation, RefResolution, VisualiseMapping,
};
pub use resolver::resolve_refs_text;

use pyo3::prelude::*;

#[pymodule]
fn _core(_py: Python<'_>, module: &Bound<'_, PyModule>) -> PyResult<()> {
    python::register(module)
}
