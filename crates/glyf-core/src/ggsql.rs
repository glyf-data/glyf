use regex::Regex;
use std::collections::{BTreeMap, BTreeSet};
use std::sync::OnceLock;

use crate::error::CoreError;
use crate::models::{GgsqlChart, VisualiseMapping};
use crate::resolver::{ref_regex, source_regex};

pub fn parse_ggsql_text(
    text: &str,
    name: &str,
    path: Option<&str>,
) -> Result<GgsqlChart, CoreError> {
    reject_unsupported_draws(text)?;
    let normalized = normalize_for_ggsql(text);
    let validated =
        ggsql::validate::validate(&normalized).map_err(|err| CoreError::Parse(err.to_string()))?;
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
        let parts = mapping_regex().captures(raw_mapping).ok_or_else(|| {
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

fn mapping_regex() -> &'static Regex {
    static REGEX: OnceLock<Regex> = OnceLock::new();
    REGEX.get_or_init(|| Regex::new(r"^\s*([A-Za-z_][\w.]*)\s+AS\s+([A-Za-z_][\w]*)\s*$").unwrap())
}

#[cfg(test)]
mod tests {
    use crate::ggsql::parse_ggsql_text;

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
}
