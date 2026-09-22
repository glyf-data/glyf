use regex::Regex;
use sqlparser::ast::Statement;
use sqlparser::dialect::{
    BigQueryDialect, Dialect, DuckDbDialect, GenericDialect, SnowflakeDialect,
};
use sqlparser::parser::Parser;
use std::collections::{BTreeMap, BTreeSet};
use std::sync::OnceLock;

use crate::error::CoreError;
use crate::models::{GgsqlChart, VisualiseMapping};
use crate::resolver::{ref_regex, source_regex};

/// glyf's chart language: what each draw type takes. This is the single
/// source of truth for validation; the renderer draws exactly these roles.
///
/// ggsql is the file format; pie, histogram and boxplot are glyf's additions
/// to it. glyf validates the chart block; sqlparser reads the SQL (`read_sql`).
struct DrawSpec {
    /// The name glyf reports and the renderer dispatches on.
    draw_type: &'static str,
    required: &'static [&'static str],
    allowed: &'static [&'static str],
    interactions: &'static [&'static str],
}

const XY: &[&str] = &["x", "y"];
const XY_COLOR: &[&str] = &["x", "y", "color"];
const ALL_INTERACTIONS: &[&str] = &["legend_filter", "tooltip", "zoom"];
const CONFIG_KEYS: &[&str] = &["width", "height"];

fn draw_spec(draw: &str) -> Option<DrawSpec> {
    let xy = |draw_type| DrawSpec {
        draw_type,
        required: XY,
        allowed: XY_COLOR,
        interactions: ALL_INTERACTIONS,
    };
    Some(match draw {
        "line" => xy("line"),
        "bar" => xy("bar"),
        "area" => xy("area"),
        "pie" => xy("pie"),
        // ggsql calls it `point`; glyf has always reported `scatter`.
        "scatter" | "point" => xy("scatter"),
        "histogram" => DrawSpec {
            draw_type: "histogram",
            required: &["x"],
            allowed: &["x", "color"],
            interactions: ALL_INTERACTIONS,
        },
        // A boxplot is a composite mark a legend selection cannot bind to, and
        // a heatmap's colour is a continuous scale with no legend entries.
        "boxplot" => DrawSpec {
            draw_type: "boxplot",
            required: XY,
            allowed: XY_COLOR,
            interactions: &["tooltip", "zoom"],
        },
        "heatmap" | "tile" => DrawSpec {
            draw_type: "heatmap",
            required: XY_COLOR,
            allowed: XY_COLOR,
            interactions: &["tooltip", "zoom"],
        },
        _ => return None,
    })
}

/// The draw types glyf accepts, for error messages.
const SUPPORTED_DRAWS: &str = "area, bar, boxplot, heatmap, histogram, line, pie, scatter";

/// Parse a `.ggsql` file: the SQL, then the chart block.
///
/// `dialect` names the warehouse the SQL is written for (`duckdb`,
/// `snowflake`, `bigquery`; anything else parses as generic SQL) and only
/// affects how the SQL is read for the `ORDER BY` question and the syntax
/// warning. The chart block is validated by glyf, whatever the dialect.
pub fn parse_ggsql_text(
    text: &str,
    name: &str,
    path: Option<&str>,
    dialect: &str,
) -> Result<GgsqlChart, CoreError> {
    let (legacy_sql, visual_lines) = split_legacy_parts(text)
        .ok_or_else(|| CoreError::Parse("missing VISUALISE section".to_string()))?;

    let sql = legacy_sql.trim().to_string();
    if sql.is_empty() {
        return Err(CoreError::Parse("missing SQL query section".to_string()));
    }
    let (has_order_by, sql_warning) = read_sql(&sql, dialect);

    let visualise_line = visual_lines
        .first()
        .ok_or_else(|| CoreError::Parse("missing VISUALISE section".to_string()))?;
    let visualise = parse_visualise(visualise_line)?;

    let mut draw_type = None;
    let mut labels = BTreeMap::new();
    let mut config = BTreeMap::new();
    let mut interactions = Vec::new();
    let mut seen_interactions = BTreeSet::new();

    for line in visual_lines.iter().skip(1) {
        if let Some(draw) = parse_draw(line) {
            let Some(spec) = draw_spec(&draw) else {
                return Err(CoreError::Parse(format!(
                    "unsupported chart type '{draw}'; supported chart types: {SUPPORTED_DRAWS}"
                )));
            };
            draw_type = Some(spec.draw_type.to_string());
            continue;
        }
        if let Some((key, value)) = parse_key_value_directive(line, "LABEL") {
            labels.insert(key, unquote(value).trim().to_string());
            continue;
        }
        if let Some((key, value)) = parse_key_value_directive(line, "CONFIG") {
            if !CONFIG_KEYS.contains(&key.as_str()) {
                return Err(CoreError::Parse(format!(
                    "unsupported CONFIG key '{key}'; supported keys: width, height"
                )));
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
                if !ALL_INTERACTIONS.contains(&interaction.as_str()) {
                    return Err(CoreError::Parse(format!(
                        "unsupported interaction '{interaction}'; supported interactions: legend_filter, tooltip, zoom"
                    )));
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
    let spec = draw_spec(&draw_type).expect("a stored draw type is in the table");
    validate_roles(&spec, &visualise)?;
    validate_interactions(&spec, &interactions)?;

    Ok(GgsqlChart {
        path: path.unwrap_or(name).to_string(),
        name: name.to_string(),
        sql,
        visualise,
        draw_type,
        labels,
        config,
        interactions,
        has_order_by,
        sql_warning,
    })
}

/// Whether the query orders its own rows, and a warning if it could not be
/// read.
///
/// The SQL is parsed with sqlparser after dbt calls are resolved to plain
/// names. Only the outer query's `ORDER BY` counts: one inside a CTE, a
/// subquery or a window function orders something other than the rows the
/// chart draws, and sqlparser keeps those apart. A parse failure is a
/// warning, never an error: the warehouse is the judge of the SQL, and a
/// parser can lag a dialect. The chart is then treated as unordered, so glyf
/// orders its rows itself, the safe side of the 0.8.0 rule.
fn read_sql(sql: &str, dialect: &str) -> (bool, Option<String>) {
    let plain = normalize_jinja_for_ggsql(sql);
    let dialect_impl: Box<dyn Dialect> = match dialect.to_ascii_lowercase().as_str() {
        "duckdb" => Box::new(DuckDbDialect {}),
        "snowflake" => Box::new(SnowflakeDialect {}),
        "bigquery" => Box::new(BigQueryDialect {}),
        _ => Box::new(GenericDialect {}),
    };
    match Parser::parse_sql(dialect_impl.as_ref(), &plain) {
        Ok(statements) => {
            let has_order_by = statements
                .iter()
                .any(|statement| matches!(statement, Statement::Query(query) if query.order_by.is_some()));
            (has_order_by, None)
        }
        Err(err) => (
            false,
            Some(format!(
                "SQL did not parse as {dialect}: {}. The warehouse will report the error if it is one; the rows are treated as unordered.",
                err.to_string().trim_start_matches("sql parser error: ")
            )),
        ),
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

fn validate_roles(spec: &DrawSpec, visualise: &[VisualiseMapping]) -> Result<(), CoreError> {
    let draw = spec.draw_type;
    let takes = spec.allowed.join(", ");
    // Say why, not just that: a histogram computes its own y.
    if draw == "histogram" && visualise.iter().any(|mapping| mapping.role == "y") {
        return Err(CoreError::Parse(
            "histogram counts the rows in each bin of x and takes no y mapping".to_string(),
        ));
    }
    for mapping in visualise {
        if !spec.allowed.contains(&mapping.role.as_str()) {
            return Err(CoreError::Parse(format!(
                "{draw} does not take a '{}' mapping; it takes {takes}",
                mapping.role
            )));
        }
    }
    let roles = visualise
        .iter()
        .map(|mapping| mapping.role.as_str())
        .collect::<BTreeSet<_>>();
    let missing = spec
        .required
        .iter()
        .filter(|role| !roles.contains(*role))
        .copied()
        .collect::<Vec<_>>();
    if !missing.is_empty() {
        let message = match draw {
            "histogram" => "histogram requires an x mapping".to_string(),
            "heatmap" => "heatmap requires x, y and color mappings".to_string(),
            _ => "VISUALISE requires x and y mappings".to_string(),
        };
        return Err(CoreError::Parse(message));
    }
    Ok(())
}

fn validate_interactions(spec: &DrawSpec, interactions: &[String]) -> Result<(), CoreError> {
    for interaction in interactions {
        if !spec.interactions.contains(&interaction.as_str()) {
            return Err(CoreError::Parse(format!(
                "{interaction} interaction is not supported for {} charts",
                spec.draw_type
            )));
        }
    }
    Ok(())
}

fn parse_draw(line: &str) -> Option<String> {
    let raw = strip_keyword(line, "DRAW")?;
    let draw = raw.split_whitespace().next()?;
    Some(draw.trim().to_lowercase())
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
        let chart = parse_ggsql_text("SELECT month, revenue, region FROM fct_orders\n\nVISUALISE month AS x, revenue AS y, region AS color\nDRAW scatter\nLABEL title => 'Revenue'\nCONFIG width => 900\nINTERACT tooltip, legend-filter\n", "revenue", Some("revenue.ggsql"), "duckdb")
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
        let chart = parse_ggsql_text("SELECT region, sum(revenue) AS revenue FROM {{ ref('fct_orders') }} GROUP BY 1\n\nVISUALISE region AS x, revenue AS y\nDRAW pie\n", "revenue_share", None, "duckdb")
        .unwrap();

        assert_eq!(chart.draw_type, "pie");
        assert_eq!(
            chart.sql,
            "SELECT region, sum(revenue) AS revenue FROM {{ ref('fct_orders') }} GROUP BY 1"
        );
    }

    #[test]
    fn accepts_double_quoted_labels() {
        let chart = parse_ggsql_text("SELECT month, revenue FROM fct_orders\n\nVISUALISE month AS x, revenue AS y\nDRAW line\nLABEL title => \"This month's revenue\"\nLABEL x_title => \"Month\"\n", "revenue", None, "duckdb")
        .unwrap();

        assert_eq!(chart.labels.get("title").unwrap(), "This month's revenue");
        assert_eq!(chart.labels.get("x_title").unwrap(), "Month");
    }

    #[test]
    fn parses_histogram_with_x_alone() {
        let chart = parse_ggsql_text("SELECT amount, region FROM fct_orders\n\nVISUALISE amount AS x, region AS color\nDRAW histogram\nINTERACT tooltip, legend_filter\n", "order_size", None, "duckdb")
        .unwrap();

        assert_eq!(chart.draw_type, "histogram");
        assert_eq!(chart.visualise.len(), 2);
    }

    #[test]
    fn rejects_histogram_with_y_mapping() {
        let error = parse_ggsql_text("SELECT amount, revenue FROM fct_orders\n\nVISUALISE amount AS x, revenue AS y\nDRAW histogram\n", "order_size", None, "duckdb")
        .unwrap_err();

        assert!(error.to_string().contains("takes no y mapping"));
    }

    #[test]
    fn rejects_an_unknown_role_naming_the_chart_the_user_wrote() {
        // Before DEC-008 this came back from ggsql as "Layer 'bar' does not
        // support the `banana` mapping": the stand-in, not the pie.
        let error = parse_ggsql_text("SELECT region, revenue FROM fct_orders\n\nVISUALISE region AS x, revenue AS banana\nDRAW pie\n", "share", None, "duckdb")
        .unwrap_err();

        assert_eq!(
            error.to_string(),
            "pie does not take a 'banana' mapping; it takes x, y, color"
        );
    }

    #[test]
    fn rejects_a_role_the_renderer_would_ignore() {
        // ggsql's grammar accepts `size`; glyf's renderer never drew it.
        let error = parse_ggsql_text(
            "SELECT a, b, c FROM t\n\nVISUALISE a AS x, b AS y, c AS size\nDRAW scatter\n",
            "s",
            None,
            "duckdb",
        )
        .unwrap_err();

        assert!(error
            .to_string()
            .starts_with("scatter does not take a 'size' mapping"));
    }

    #[test]
    fn every_draw_type_is_validated_by_glyf_not_a_stand_in() {
        for (draw, reported) in [
            ("line", "line"),
            ("bar", "bar"),
            ("area", "area"),
            ("scatter", "scatter"),
            ("point", "scatter"),
            ("pie", "pie"),
            ("boxplot", "boxplot"),
        ] {
            let chart = parse_ggsql_text(
                &format!("SELECT a, b FROM t\n\nVISUALISE a AS x, b AS y\nDRAW {draw}\n"),
                "c",
                None,
                "duckdb",
            )
            .unwrap();
            assert_eq!(chart.draw_type, reported, "{draw}");

            let error = parse_ggsql_text(
                &format!("SELECT a, b FROM t\n\nVISUALISE a AS x, b AS nope\nDRAW {draw}\n"),
                "c",
                None,
                "duckdb",
            )
            .unwrap_err()
            .to_string();
            assert!(
                error.starts_with(&format!("{reported} does not take a 'nope' mapping")),
                "{draw}: {error}"
            );
        }
    }

    #[test]
    fn names_the_supported_chart_types_on_an_unknown_draw() {
        let error = parse_ggsql_text(
            "SELECT a, b FROM t\n\nVISUALISE a AS x, b AS y\nDRAW donut\n",
            "c",
            None,
            "duckdb",
        )
        .unwrap_err();

        assert_eq!(
            error.to_string(),
            "unsupported chart type 'donut'; supported chart types: area, bar, boxplot, heatmap, histogram, line, pie, scatter"
        );
    }

    #[test]
    fn broken_sql_is_a_warning_with_a_position_not_an_error() {
        let chart = parse_ggsql_text(
            "SELECT region\nFROM t\nWHERE region = AND 1\n\nVISUALISE region AS x, region AS y\nDRAW bar\n",
            "c",
            None,
            "duckdb",
        )
        .unwrap();

        let warning = chart.sql_warning.expect("a warning");
        assert!(
            warning.starts_with("SQL did not parse as duckdb: "),
            "{warning}"
        );
        assert!(warning.contains("Line: 3, Column: "), "{warning}");
        assert!(warning.contains("treated as unordered"), "{warning}");
        assert!(!chart.has_order_by);
    }

    #[test]
    fn well_formed_sql_carries_no_warning() {
        let chart = parse_ggsql_text(
            "SELECT a, b FROM {{ ref('t') }} ORDER BY a\n\nVISUALISE a AS x, b AS y\nDRAW bar\n",
            "c",
            None,
            "snowflake",
        )
        .unwrap();
        assert_eq!(chart.sql_warning, None);
        assert!(chart.has_order_by);
    }

    #[test]
    fn the_dialect_is_passed_through_and_named() {
        // `SELECT * EXCLUDE (...)` is DuckDB and Snowflake syntax; the generic
        // parser is permissive enough to take it too, so only the name shows.
        let text = "SELECT * EXCLUDE (secret) FROM t\n\nVISUALISE a AS x, b AS y\nDRAW bar\n";
        assert_eq!(
            parse_ggsql_text(text, "c", None, "duckdb")
                .unwrap()
                .sql_warning,
            None
        );
        let broken = "SELECT a b c FROM t\n\nVISUALISE a AS x, b AS y\nDRAW bar\n";
        let warning = parse_ggsql_text(broken, "c", None, "bigquery")
            .unwrap()
            .sql_warning
            .unwrap();
        assert!(
            warning.starts_with("SQL did not parse as bigquery: "),
            "{warning}"
        );
    }

    #[test]
    fn parses_boxplot() {
        let chart = parse_ggsql_text("SELECT region, amount FROM fct_orders\n\nVISUALISE region AS x, amount AS y\nDRAW boxplot\nINTERACT tooltip\n", "order_spread", None, "duckdb")
        .unwrap();

        assert_eq!(chart.draw_type, "boxplot");
    }

    #[test]
    fn parses_heatmap_and_its_tile_alias() {
        for draw in ["heatmap", "tile"] {
            let chart = parse_ggsql_text(&format!(
                    "SELECT weekday, hour, orders FROM fct_orders\n\nVISUALISE hour AS x, weekday AS y, orders AS color\nDRAW {draw}\n"
                ), "order_heatmap", None, "duckdb")
            .unwrap();

            assert_eq!(chart.draw_type, "heatmap");
        }
    }

    #[test]
    fn rejects_heatmap_without_color_mapping() {
        let error = parse_ggsql_text("SELECT weekday, hour FROM fct_orders\n\nVISUALISE hour AS x, weekday AS y\nDRAW heatmap\n", "order_heatmap", None, "duckdb")
        .unwrap_err();

        assert!(error
            .to_string()
            .contains("heatmap requires x, y and color mappings"));
    }

    #[test]
    fn rejects_legend_filter_on_boxplot_and_heatmap() {
        let boxplot = parse_ggsql_text("SELECT region, amount FROM fct_orders\n\nVISUALISE region AS x, amount AS y, region AS color\nDRAW boxplot\nINTERACT legend_filter\n", "order_spread", None, "duckdb")
        .unwrap_err();
        assert!(boxplot
            .to_string()
            .contains("legend_filter interaction is not supported for boxplot charts"));

        let heatmap = parse_ggsql_text("SELECT weekday, hour, orders FROM fct_orders\n\nVISUALISE hour AS x, weekday AS y, orders AS color\nDRAW heatmap\nINTERACT legend_filter\n", "order_heatmap", None, "duckdb")
        .unwrap_err();
        assert!(heatmap
            .to_string()
            .contains("legend_filter interaction is not supported for heatmap charts"));
    }

    #[test]
    fn still_requires_x_and_y_for_other_chart_types() {
        let error = parse_ggsql_text(
            "SELECT month FROM fct_orders\n\nVISUALISE month AS x\nDRAW bar\n",
            "revenue",
            None,
            "duckdb",
        )
        .unwrap_err();

        assert!(error
            .to_string()
            .contains("VISUALISE requires x and y mappings"));
    }

    #[test]
    fn records_whether_the_query_orders_its_own_rows() {
        let ordered = parse_ggsql_text("SELECT month, revenue FROM fct_orders ORDER BY month\n\nVISUALISE month AS x, revenue AS y\nDRAW line\n", "revenue", None, "duckdb")
        .unwrap();
        assert!(ordered.has_order_by);

        let unordered = parse_ggsql_text("SELECT month, revenue FROM fct_orders\n\nVISUALISE month AS x, revenue AS y\nDRAW line\n", "revenue", None, "duckdb")
        .unwrap();
        assert!(!unordered.has_order_by);
    }

    #[test]
    fn a_nested_order_by_does_not_order_the_chart() {
        // Each of these orders something other than the rows the chart draws.
        for sql in [
            "SELECT month, revenue FROM (SELECT month, revenue FROM fct_orders ORDER BY month) t",
            "WITH ranked AS (SELECT month, revenue FROM fct_orders ORDER BY revenue) SELECT month, revenue FROM ranked",
            "SELECT month, row_number() OVER (ORDER BY month) AS revenue FROM fct_orders",
        ] {
            let chart = parse_ggsql_text(&format!("{sql}\n\nVISUALISE month AS x, revenue AS y\nDRAW line\n"), "revenue", None, "duckdb")
            .unwrap();
            assert!(!chart.has_order_by, "{sql}");
        }
    }

    #[test]
    fn an_outer_order_by_counts_even_with_a_nested_query() {
        let chart = parse_ggsql_text("WITH ranked AS (SELECT month, revenue FROM fct_orders) SELECT month, revenue FROM ranked ORDER BY month DESC\n\nVISUALISE month AS x, revenue AS y\nDRAW line\n", "revenue", None, "duckdb")
        .unwrap();

        assert!(chart.has_order_by);
    }
}
