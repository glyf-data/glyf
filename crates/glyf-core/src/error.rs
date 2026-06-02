#[derive(Debug, thiserror::Error)]
pub enum CoreError {
    #[error("{0}")]
    Parse(String),
    #[error("{0}")]
    Manifest(String),
    #[error("{0}")]
    Dashboard(String),
}
