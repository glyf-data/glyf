use regex::Regex;
use serde_json::Value;
use std::sync::OnceLock;

use crate::error::CoreError;

const TOOLBAR_ACTIONS: &[&str] = &["share", "visibility"];
const TOOLBAR_VISIBILITIES: &[&str] = &["private", "public"];
const DASHBOARD_THEMES: &[&str] = &["light", "dark"];
const CHART_THEMES: &[&str] = &["auto", "light", "dark"];

pub fn validate_dashboard_json_text(text: &str, path: &str) -> Result<(), CoreError> {
    let raw: Value = serde_json::from_str(text)
        .map_err(|_| CoreError::Dashboard(format!("Invalid dashboard JSON: {path}")))?;
    let dashboard = raw
        .as_object()
        .ok_or_else(|| dashboard_error("expected a YAML mapping"))?;

    required_string(dashboard.get("name"), "name")?;
    validate_dashboard_name(dashboard.get("name").and_then(Value::as_str).unwrap())?;

    required_string(dashboard.get("title"), "title")?;
    optional_string(dashboard.get("description"), "description")?;
    validate_theme(dashboard.get("theme"))?;
    validate_chart_theme(dashboard.get("chart_theme"))?;
    validate_tags(dashboard.get("tags"))?;
    validate_charts(dashboard.get("charts"), "charts")?;
    validate_filters(dashboard.get("filters"))?;
    validate_toolbar(dashboard.get("toolbar"))?;
    validate_summary(dashboard.get("summary"))?;
    validate_layout(dashboard.get("layout"))?;

    let sections = dashboard
        .get("sections")
        .or_else(|| dashboard.get("groups"));
    validate_sections(sections)?;
    Ok(())
}

fn validate_dashboard_name(name: &str) -> Result<(), CoreError> {
    if dashboard_name_regex().is_match(name) {
        return Ok(());
    }
    Err(dashboard_error(
        "expected 'name' to be a valid filename stem using letters, numbers, '.', '_', or '-'",
    ))
}

fn validate_charts(value: Option<&Value>, label: &str) -> Result<(), CoreError> {
    let Some(value) = value else {
        return Ok(());
    };
    let charts = value.as_array().ok_or_else(|| {
        dashboard_error(format!("expected '{label}' to be a list of chart names"))
    })?;
    for (index, chart) in charts.iter().enumerate() {
        non_empty_string(
            Some(chart),
            &format!("{label}[{}]", index + 1),
            "chart name",
        )?;
    }
    Ok(())
}

fn validate_tags(value: Option<&Value>) -> Result<(), CoreError> {
    let Some(value) = value else {
        return Ok(());
    };
    if value.is_null() {
        return Ok(());
    }
    let tags = value
        .as_array()
        .ok_or_else(|| dashboard_error("expected 'tags' to be a list of non-empty strings"))?;
    for (index, tag) in tags.iter().enumerate() {
        non_empty_string(Some(tag), &format!("tags[{}]", index + 1), "string")?;
    }
    Ok(())
}

fn validate_theme(value: Option<&Value>) -> Result<(), CoreError> {
    let Some(value) = value else {
        return Ok(());
    };
    if value.is_null() {
        return Ok(());
    }
    let theme = value
        .as_str()
        .ok_or_else(|| dashboard_error("expected 'theme' to be one of: dark, light"))?;
    if DASHBOARD_THEMES.contains(&theme) {
        return Ok(());
    }
    Err(dashboard_error(
        "expected 'theme' to be one of: dark, light",
    ))
}

fn validate_chart_theme(value: Option<&Value>) -> Result<(), CoreError> {
    let Some(value) = value else {
        return Ok(());
    };
    if value.is_null() {
        return Ok(());
    }
    let chart_theme = value
        .as_str()
        .ok_or_else(|| dashboard_error("expected 'chart_theme' to be one of: auto, dark, light"))?;
    if CHART_THEMES.contains(&chart_theme) {
        return Ok(());
    }
    Err(dashboard_error(
        "expected 'chart_theme' to be one of: auto, dark, light",
    ))
}

fn validate_toolbar(value: Option<&Value>) -> Result<(), CoreError> {
    let Some(value) = value else {
        return Ok(());
    };
    if value.is_boolean() {
        return Ok(());
    }
    let toolbar = value
        .as_object()
        .ok_or_else(|| dashboard_error("expected 'toolbar' to be a boolean or mapping"))?;

    if let Some(enabled) = toolbar.get("enabled") {
        if !enabled.is_boolean() {
            return Err(dashboard_error(
                "expected 'toolbar.enabled' to be true or false",
            ));
        }
    }

    if let Some(visibility) = toolbar.get("visibility") {
        let visibility = visibility.as_str().ok_or_else(|| {
            dashboard_error("expected 'toolbar.visibility' to be one of: private, public")
        })?;
        if !TOOLBAR_VISIBILITIES.contains(&visibility) {
            return Err(dashboard_error(
                "expected 'toolbar.visibility' to be one of: private, public",
            ));
        }
    }

    if let Some(actions) = toolbar.get("actions") {
        let actions = actions
            .as_array()
            .ok_or_else(|| dashboard_error("expected 'toolbar.actions' to be a list"))?;
        for (index, action) in actions.iter().enumerate() {
            let action = action.as_str().ok_or_else(|| {
                dashboard_error(format!(
                    "expected 'toolbar.actions[{}]' to be one of: share, visibility",
                    index + 1
                ))
            })?;
            if !TOOLBAR_ACTIONS.contains(&action) {
                return Err(dashboard_error(format!(
                    "expected 'toolbar.actions[{}]' to be one of: share, visibility",
                    index + 1
                )));
            }
        }
    }
    Ok(())
}

fn validate_filters(value: Option<&Value>) -> Result<(), CoreError> {
    let Some(value) = value else {
        return Ok(());
    };
    if value.is_null() {
        return Ok(());
    }
    let filters = value
        .as_array()
        .ok_or_else(|| dashboard_error("expected 'filters' to be a list"))?;
    for (index, filter) in filters.iter().enumerate() {
        validate_filter(filter, index + 1)?;
    }
    Ok(())
}

fn validate_filter(filter: &Value, index: usize) -> Result<(), CoreError> {
    let label = format!("filters[{index}]");
    let filter = filter
        .as_object()
        .ok_or_else(|| dashboard_error(format!("expected {label} to be a mapping")))?;
    non_empty_string(filter.get("field"), &format!("{label}.field"), "string")?;

    let Some(values) = filter.get("values") else {
        return Err(dashboard_error(format!(
            "expected '{label}.values' to be provided"
        )));
    };
    if let Some(values) = values.as_array() {
        for (value_index, value) in values.iter().enumerate() {
            non_empty_string(
                Some(value),
                &format!("{label}.values[{}]", value_index + 1),
                "string",
            )?;
        }
        return Ok(());
    }

    let Some(source) = values.as_str() else {
        return Err(dashboard_error(format!(
            "expected '{label}.values' to be a list or source(chart, field)"
        )));
    };
    if filter_source_regex().is_match(source.trim()) {
        return Ok(());
    }
    Err(dashboard_error(format!(
        "expected '{label}.values' to be a list or source(chart, field)"
    )))
}

fn validate_summary(value: Option<&Value>) -> Result<(), CoreError> {
    let Some(value) = value else {
        return Ok(());
    };
    if value.is_null() {
        return Ok(());
    }
    let summary = value
        .as_array()
        .ok_or_else(|| dashboard_error("expected 'summary' to be a list"))?;
    for (index, item) in summary.iter().enumerate() {
        validate_macro_expression(item, &format!("summary[{}]", index + 1))?;
    }
    Ok(())
}

fn validate_layout(value: Option<&Value>) -> Result<(), CoreError> {
    let Some(value) = value else {
        return Ok(());
    };
    if let Some(kind) = value.as_str() {
        if kind.is_empty() {
            return Err(dashboard_error(
                "expected 'layout' to be a non-empty string",
            ));
        }
        return Ok(());
    }

    let layout = value
        .as_object()
        .ok_or_else(|| dashboard_error("expected 'layout' to be a string or mapping"))?;
    if let Some(kind) = layout.get("type").or_else(|| layout.get("kind")) {
        non_empty_string(Some(kind), "layout.type", "string")?;
    }
    validate_columns(layout.get("columns"), "layout.columns")
}

fn validate_sections(value: Option<&Value>) -> Result<(), CoreError> {
    let Some(value) = value else {
        return Ok(());
    };
    if value.is_null() {
        return Ok(());
    }
    let sections = value
        .as_array()
        .ok_or_else(|| dashboard_error("expected 'sections' to be a list"))?;
    for (index, section) in sections.iter().enumerate() {
        validate_section(section, index + 1)?;
    }
    Ok(())
}

fn validate_section(section: &Value, index: usize) -> Result<(), CoreError> {
    let label = format!("sections[{index}]");
    let section = section
        .as_object()
        .ok_or_else(|| dashboard_error(format!("expected section {index} to be a mapping")))?;

    optional_string(section.get("title"), &format!("{label}.title"))?;
    optional_string(section.get("description"), &format!("{label}.description"))?;
    validate_columns(section.get("columns"), &format!("{label}.columns"))?;

    let mut has_content = false;
    if let Some(items) = section.get("items") {
        has_content = true;
        let items = items
            .as_array()
            .ok_or_else(|| dashboard_error(format!("expected {label}.items to be a list")))?;
        for (item_index, item) in items.iter().enumerate() {
            validate_item(item, &format!("{label}.items[{}]", item_index + 1))?;
        }
    }
    if let Some(charts) = section.get("charts") {
        has_content = true;
        validate_charts(Some(charts), &format!("{label}.charts"))?;
    }
    if !has_content {
        return Err(dashboard_error(format!(
            "expected section {index} to contain items or charts"
        )));
    }
    Ok(())
}

fn validate_item(item: &Value, label: &str) -> Result<(), CoreError> {
    if item.is_string() {
        return non_empty_string(Some(item), label, "chart name");
    }

    let item = item.as_object().ok_or_else(|| {
        dashboard_error(format!("expected {label} to be a chart name or mapping"))
    })?;
    let kinds = ["chart", "component", "markdown", "metric"]
        .into_iter()
        .filter(|kind| item.contains_key(*kind))
        .collect::<Vec<_>>();
    if kinds.len() != 1 {
        return Err(dashboard_error(format!(
            "expected {label} to define exactly one of chart, component, markdown, or metric"
        )));
    }

    match kinds[0] {
        "chart" => validate_chart_item(item.get("chart").unwrap(), item, label),
        "component" => validate_component_item(item, label),
        "markdown" => validate_markdown_item(item, label),
        "metric" => validate_metric_item(item, label),
        _ => unreachable!(),
    }
}

fn validate_chart_item(
    chart: &Value,
    item: &serde_json::Map<String, Value>,
    label: &str,
) -> Result<(), CoreError> {
    if let Some(chart_name) = chart.as_str() {
        if chart_name.is_empty() {
            return Err(dashboard_error(format!(
                "expected {label}.chart to be a non-empty chart name"
            )));
        }
        optional_string(item.get("title"), &format!("{label}.title"))?;
        optional_positive_int(item.get("width"), &format!("{label}.width"))?;
        return Ok(());
    }

    let chart = chart.as_object().ok_or_else(|| {
        dashboard_error(format!(
            "expected {label}.chart to be a chart name or mapping"
        ))
    })?;
    non_empty_string(
        chart.get("name"),
        &format!("{label}.chart.name"),
        "chart name",
    )?;
    optional_string(chart.get("title"), &format!("{label}.chart.title"))?;
    optional_positive_int(chart.get("width"), &format!("{label}.chart.width"))
}

fn validate_component_item(
    item: &serde_json::Map<String, Value>,
    label: &str,
) -> Result<(), CoreError> {
    validate_macro_expression(
        item.get("component").unwrap(),
        &format!("{label}.component"),
    )?;
    optional_positive_int(item.get("width"), &format!("{label}.width"))
}

fn validate_markdown_item(
    item: &serde_json::Map<String, Value>,
    label: &str,
) -> Result<(), CoreError> {
    let markdown = item.get("markdown").unwrap();
    if markdown.is_string() {
        optional_string(item.get("title"), &format!("{label}.title"))?;
        return non_empty_string(Some(markdown), &format!("{label}.markdown"), "string");
    }

    let markdown = markdown.as_object().ok_or_else(|| {
        dashboard_error(format!(
            "expected {label}.markdown to be a string or mapping"
        ))
    })?;
    optional_string(markdown.get("title"), &format!("{label}.markdown.title"))?;
    non_empty_string(
        markdown.get("text"),
        &format!("{label}.markdown.text"),
        "string",
    )
}

fn validate_metric_item(
    item: &serde_json::Map<String, Value>,
    label: &str,
) -> Result<(), CoreError> {
    let metric = item
        .get("metric")
        .and_then(Value::as_object)
        .ok_or_else(|| dashboard_error(format!("expected {label}.metric to be a mapping")))?;
    non_empty_string(
        metric.get("label"),
        &format!("{label}.metric.label"),
        "string",
    )?;
    non_empty_string(
        metric.get("value"),
        &format!("{label}.metric.value"),
        "string",
    )?;
    optional_string(metric.get("note"), &format!("{label}.metric.note"))?;
    optional_positive_int(metric.get("width"), &format!("{label}.metric.width"))
}

fn validate_columns(value: Option<&Value>, label: &str) -> Result<(), CoreError> {
    let Some(value) = value else {
        return Ok(());
    };
    if let Some(count) = value.as_i64() {
        if count > 0 {
            return Ok(());
        }
        return Err(dashboard_error(format!(
            "expected '{label}' to be a positive integer"
        )));
    }
    if value.is_boolean() {
        return Err(dashboard_error(format!(
            "expected '{label}' to be a positive integer, string, or list"
        )));
    }
    if let Some(raw) = value.as_str() {
        let tracks = split_column_tracks(raw);
        if tracks.is_empty() {
            return Err(dashboard_error(format!(
                "expected '{label}' to define at least one column"
            )));
        }
        for (index, track) in tracks.iter().enumerate() {
            validate_column_track_str(track, &format!("{label}[{}]", index + 1))?;
        }
        return Ok(());
    }

    let tracks = if let Some(raw) = value.as_array() {
        raw
    } else {
        return Err(dashboard_error(format!(
            "expected '{label}' to be a positive integer, string, or list"
        )));
    };
    if tracks.is_empty() {
        return Err(dashboard_error(format!(
            "expected '{label}' to define at least one column"
        )));
    }
    for (index, track) in tracks.iter().enumerate() {
        validate_column_track(track, &format!("{label}[{}]", index + 1))?;
    }
    Ok(())
}

fn validate_column_track(value: &Value, label: &str) -> Result<(), CoreError> {
    if let Some(weight) = value.as_i64() {
        if weight > 0 {
            return Ok(());
        }
        return Err(dashboard_error(format!(
            "expected '{label}' to be a positive column weight"
        )));
    }
    if value.is_boolean() {
        return Err(dashboard_error(format!(
            "expected '{label}' to be a column width string"
        )));
    }
    let Some(track) = value.as_str() else {
        return Err(dashboard_error(format!(
            "expected '{label}' to be a column width string"
        )));
    };
    validate_column_track_str(track, label)
}

fn validate_column_track_str(value: &str, label: &str) -> Result<(), CoreError> {
    let track = value.trim();
    if track == "auto" {
        return Ok(());
    }
    let Some(captures) = column_track_regex().captures(track) else {
        return Err(dashboard_error(format!(
            "expected '{label}' to use %, fr, px, rem, em, ch, vw, vh, or auto"
        )));
    };
    let number = captures
        .get(1)
        .and_then(|value| value.as_str().parse::<f64>().ok())
        .unwrap_or(0.0);
    if number > 0.0 {
        return Ok(());
    }
    Err(dashboard_error(format!(
        "expected '{label}' to be greater than zero"
    )))
}

fn split_column_tracks(value: &str) -> Vec<&str> {
    if value.trim().is_empty() {
        return Vec::new();
    }
    let separator = if value.contains(',') { ',' } else { ' ' };
    value
        .split(separator)
        .map(str::trim)
        .filter(|track| !track.is_empty())
        .collect()
}

fn validate_macro_expression(value: &Value, label: &str) -> Result<(), CoreError> {
    let expression = value.as_str().ok_or_else(|| {
        dashboard_error(format!(
            "expected '{label}' to be a non-empty macro expression"
        ))
    })?;
    if expression.is_empty() {
        return Err(dashboard_error(format!(
            "expected '{label}' to be a non-empty macro expression"
        )));
    }
    if macro_expression_regex().is_match(expression) {
        return Ok(());
    }
    Err(dashboard_error(format!(
        "{label}: expected a Jinja expression like '{{{{ ui.label_value(...) }}}}'"
    )))
}

fn required_string(value: Option<&Value>, label: &str) -> Result<(), CoreError> {
    non_empty_string(value, label, "string")
}

fn non_empty_string(value: Option<&Value>, label: &str, expected: &str) -> Result<(), CoreError> {
    let Some(value) = value else {
        return Err(dashboard_error(format!("expected non-empty '{label}'")));
    };
    let Some(value) = value.as_str() else {
        return Err(dashboard_error(format!(
            "expected '{label}' to be a non-empty {expected}"
        )));
    };
    if value.is_empty() {
        return Err(dashboard_error(format!(
            "expected '{label}' to be a non-empty {expected}"
        )));
    }
    Ok(())
}

fn optional_string(value: Option<&Value>, label: &str) -> Result<(), CoreError> {
    let Some(value) = value else {
        return Ok(());
    };
    if value.is_string() {
        return Ok(());
    }
    Err(dashboard_error(format!(
        "expected '{label}' to be a string"
    )))
}

fn optional_positive_int(value: Option<&Value>, label: &str) -> Result<(), CoreError> {
    let Some(value) = value else {
        return Ok(());
    };
    let Some(value) = value.as_i64() else {
        return Err(dashboard_error(format!(
            "expected '{label}' to be a positive integer"
        )));
    };
    if value > 0 {
        return Ok(());
    }
    Err(dashboard_error(format!(
        "expected '{label}' to be a positive integer"
    )))
}

fn dashboard_error(message: impl Into<String>) -> CoreError {
    CoreError::Dashboard(message.into())
}

fn dashboard_name_regex() -> &'static Regex {
    static REGEX: OnceLock<Regex> = OnceLock::new();
    REGEX.get_or_init(|| Regex::new(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$").unwrap())
}

fn column_track_regex() -> &'static Regex {
    static REGEX: OnceLock<Regex> = OnceLock::new();
    REGEX.get_or_init(|| Regex::new(r"^(\d+(?:\.\d+)?)(%|fr|px|rem|em|ch|vw|vh)$").unwrap())
}

fn macro_expression_regex() -> &'static Regex {
    static REGEX: OnceLock<Regex> = OnceLock::new();
    REGEX.get_or_init(|| Regex::new(r"(?s)^\s*\{\{\s*.+?\s*\}\}\s*$").unwrap())
}

fn filter_source_regex() -> &'static Regex {
    static REGEX: OnceLock<Regex> = OnceLock::new();
    REGEX.get_or_init(|| {
        Regex::new(r#"^source\(\s*['"]?[A-Za-z0-9_.-]+['"]?\s*,\s*['"]?[A-Za-z0-9_.-]+['"]?\s*\)$"#)
            .unwrap()
    })
}

#[cfg(test)]
mod tests {
    use crate::dashboard::validate_dashboard_json_text;

    #[test]
    fn validates_basic_dashboard_spec() {
        validate_dashboard_json_text(
            r#"{
              "name": "executive",
              "title": "Executive Dashboard",
              "theme": "dark",
              "chart_theme": "auto",
              "tags": ["finance", "monthly"],
              "charts": ["revenue"],
              "layout": {"columns": "30% 70%"},
              "summary": ["{{ ui.label_value('Owner', 'Analytics') }}"]
            }"#,
            "dashboards/executive.yml",
        )
        .unwrap();
    }

    #[test]
    fn rejects_partial_macro_templates() {
        let error = validate_dashboard_json_text(
            r#"{
              "name": "executive",
              "title": "Executive Dashboard",
              "summary": ["Owner: {{ owner() }}"]
            }"#,
            "dashboards/executive.yml",
        )
        .unwrap_err();

        assert!(error.to_string().contains("expected a Jinja expression"));
    }

    #[test]
    fn rejects_empty_tags() {
        let error = validate_dashboard_json_text(
            r#"{
              "name": "executive",
              "title": "Executive Dashboard",
              "tags": ["finance", ""]
            }"#,
            "dashboards/executive.yml",
        )
        .unwrap_err();

        assert!(error.to_string().contains("tags[2]"));
    }

    #[test]
    fn validates_filters_with_source_expression() {
        validate_dashboard_json_text(
            r#"{
              "name": "executive",
              "title": "Executive Dashboard",
              "filters": [{"field": "plan", "values": "source(activation_by_plan, plan)"}]
            }"#,
            "dashboards/executive.yml",
        )
        .unwrap();
    }

    #[test]
    fn rejects_unknown_theme() {
        let error = validate_dashboard_json_text(
            r#"{
              "name": "executive",
              "title": "Executive Dashboard",
              "theme": "midnight"
            }"#,
            "dashboards/executive.yml",
        )
        .unwrap_err();

        assert!(error.to_string().contains("expected 'theme'"));
    }

    #[test]
    fn rejects_unknown_chart_theme() {
        let error = validate_dashboard_json_text(
            r#"{
              "name": "executive",
              "title": "Executive Dashboard",
              "chart_theme": "midnight"
            }"#,
            "dashboards/executive.yml",
        )
        .unwrap_err();

        assert!(error.to_string().contains("expected 'chart_theme'"));
    }
}
