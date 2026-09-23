use regex::Regex;
use sqlparser::ast::{
    visit_statements, Expr, Query, SelectItem, SetExpr, Statement, Visit, Visitor,
};
use sqlparser::dialect::{
    BigQueryDialect, Dialect, DuckDbDialect, GenericDialect, SnowflakeDialect,
};
use sqlparser::parser::Parser;
use std::collections::{BTreeMap, BTreeSet};
use std::ops::ControlFlow;
use std::sync::OnceLock;

use crate::error::CoreError;
use crate::models::{GgsqlChart, VisualiseMapping};
use crate::resolver::{ref_regex, source_regex};

/// glyf's chart language: what each draw type takes. This is the single
/// source of truth for validation; the renderer draws exactly these roles.
///
/// ggsql is the file format; pie, histogram, boxplot, table and kpi are glyf's
/// additions to it. glyf validates the chart block; sqlparser reads the SQL
/// (`read_sql`).
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

/// The role a table's columns carry. A table has no axes: `VISUALISE` lists
/// the columns to show, in order, and every one of them is a column.
pub const COLUMN_ROLE: &str = "column";
/// `VISUALISE *`: every column the query returns, in the order it returns
/// them. Stored as the field of a table's single mapping.
pub const EVERY_COLUMN: &str = "*";

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
        // A table is the rows themselves: columns without roles, and nothing
        // an interaction could bind to.
        "table" => DrawSpec {
            draw_type: "table",
            required: &[],
            allowed: &[COLUMN_ROLE],
            interactions: &[],
        },
        // A kpi is one number, with an optional one to compare it against.
        "kpi" => DrawSpec {
            draw_type: "kpi",
            required: &["value"],
            allowed: &["value", "compare"],
            interactions: &[],
        },
        _ => return None,
    })
}

/// The draw types glyf accepts, for error messages.
const SUPPORTED_DRAWS: &str =
    "area, bar, boxplot, heatmap, histogram, kpi, line, pie, scatter, table";

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
    let SqlReading {
        has_order_by,
        sql_warning,
        sql_columns,
        sql_selects_star,
    } = read_sql(&sql, dialect);

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
        sql_columns,
        sql_selects_star,
    })
}

/// What one pass over the parsed SQL yields.
struct SqlReading {
    has_order_by: bool,
    sql_warning: Option<String>,
    sql_columns: Vec<String>,
    sql_selects_star: bool,
}

/// Collects every column name the query mentions, and whether it selects `*`.
///
/// An identifier's last part is the column: `t.margin`, `f.margin` and
/// `margin` all count as `margin`. That is deliberately loose. A column
/// renamed in a CTE reaches the chart under another name, and a table alias
/// can hide which relation a column came from, so the list says "this query
/// mentions the name", which is the honest claim `glyf impact` can make.
#[derive(Default)]
struct ColumnCollector {
    columns: BTreeSet<String>,
    selects_star: bool,
}

impl Visitor for ColumnCollector {
    type Break = ();

    fn pre_visit_query(&mut self, query: &Query) -> ControlFlow<Self::Break> {
        if let SetExpr::Select(select) = query.body.as_ref() {
            if select.projection.iter().any(|item| {
                matches!(
                    item,
                    SelectItem::Wildcard(_) | SelectItem::QualifiedWildcard(_, _)
                )
            }) {
                self.selects_star = true;
            }
        }
        ControlFlow::Continue(())
    }

    fn pre_visit_expr(&mut self, expr: &Expr) -> ControlFlow<Self::Break> {
        match expr {
            Expr::Identifier(ident) => {
                self.columns.insert(ident.value.to_lowercase());
            }
            Expr::CompoundIdentifier(parts) => {
                if let Some(last) = parts.last() {
                    self.columns.insert(last.value.to_lowercase());
                }
            }
            _ => {}
        }
        ControlFlow::Continue(())
    }
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
fn read_sql(sql: &str, dialect: &str) -> SqlReading {
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
            let mut collector = ColumnCollector::default();
            let _ = visit_statements(&statements, |statement| {
                let _ = statement.visit(&mut collector);
                ControlFlow::<()>::Continue(())
            });
            SqlReading {
                has_order_by,
                sql_warning: None,
                sql_columns: collector.columns.into_iter().collect(),
                sql_selects_star: collector.selects_star,
            }
        }
        Err(err) => SqlReading {
            has_order_by: false,
            sql_warning: Some(format!(
                "SQL did not parse as {dialect}: {}. The warehouse will report the error if it is one; the rows are treated as unordered.",
                err.to_string().trim_start_matches("sql parser error: ")
            )),
            sql_columns: Vec::new(),
            sql_selects_star: false,
        },
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

/// The `VISUALISE` line, before the draw type is known.
///
/// Both shapes parse here: `month AS x, revenue AS y` for a chart with axes,
/// and `region, revenue` or `*` for a table. Which shape the draw type takes
/// is `validate_roles`'s question, once `DRAW` has been read.
fn parse_visualise(line: &str) -> Result<Vec<VisualiseMapping>, CoreError> {
    let raw = strip_keyword(line, "VISUALISE")
        .or_else(|| strip_keyword(line, "VISUALIZE"))
        .ok_or_else(|| CoreError::Parse("missing VISUALISE section".to_string()))?;
    let mut mappings = Vec::new();
    for raw_mapping in raw.split(',') {
        if let Some(parts) = mapping_regex().captures(raw_mapping) {
            mappings.push(VisualiseMapping {
                field: parts.get(1).unwrap().as_str().to_string(),
                role: parts.get(2).unwrap().as_str().to_string(),
            });
        } else if let Some(parts) = column_regex().captures(raw_mapping) {
            mappings.push(VisualiseMapping {
                field: parts.get(1).unwrap().as_str().to_string(),
                role: COLUMN_ROLE.to_string(),
            });
        } else {
            return Err(CoreError::Parse(format!(
                "invalid VISUALISE mapping: {}",
                raw_mapping.trim()
            )));
        }
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
    if draw == "table" {
        return validate_table_columns(visualise);
    }
    let takes = spec.allowed.join(", ");
    if let Some(bare) = visualise.iter().find(|mapping| mapping.role == COLUMN_ROLE) {
        // `VISUALISE month, revenue` reads as a column list, which only a
        // table takes; say what this chart wants instead of "invalid mapping".
        let first = spec.required.first().copied().unwrap_or("x");
        return Err(CoreError::Parse(format!(
            "{draw} maps each column to a role ({takes}); write '{} AS {first}', or DRAW table to list columns",
            bare.field
        )));
    }
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
            "kpi" => "kpi requires a value mapping".to_string(),
            _ => "VISUALISE requires x and y mappings".to_string(),
        };
        return Err(CoreError::Parse(message));
    }
    Ok(())
}

/// A table's `VISUALISE` is a list of columns, or `*` alone.
fn validate_table_columns(visualise: &[VisualiseMapping]) -> Result<(), CoreError> {
    if let Some(mapping) = visualise.iter().find(|mapping| mapping.role != COLUMN_ROLE) {
        return Err(CoreError::Parse(format!(
            "table lists its columns without roles; write 'VISUALISE {}, ...' or 'VISUALISE *', not '{} AS {}'",
            mapping.field, mapping.field, mapping.role
        )));
    }
    if visualise
        .iter()
        .any(|mapping| mapping.field == EVERY_COLUMN)
        && visualise.len() > 1
    {
        return Err(CoreError::Parse(
            "VISUALISE * already lists every column; write it alone".to_string(),
        ));
    }
    let mut seen = BTreeSet::new();
    for mapping in visualise {
        if !seen.insert(mapping.field.as_str()) {
            return Err(CoreError::Parse(format!(
                "table lists column '{}' twice",
                mapping.field
            )));
        }
    }
    Ok(())
}

fn validate_interactions(spec: &DrawSpec, interactions: &[String]) -> Result<(), CoreError> {
    for interaction in interactions {
        if !spec.interactions.contains(&interaction.as_str()) {
            if spec.draw_type == "table" {
                return Err(CoreError::Parse(
                    "table takes no INTERACT clause: its rows are the picture, and every column is already readable"
                        .to_string(),
                ));
            }
            if spec.draw_type == "kpi" {
                return Err(CoreError::Parse(
                    "kpi takes no INTERACT clause: it is one number".to_string(),
                ));
            }
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

/// A bare column name, or `*`: what a table's `VISUALISE` lists.
fn column_regex() -> &'static Regex {
    static REGEX: OnceLock<Regex> = OnceLock::new();
    REGEX.get_or_init(|| Regex::new(r"^\s*([A-Za-z_][\w.]*|\*)\s*$").unwrap())
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
    fn parses_a_table_as_a_role_less_column_list() {
        let chart = parse_ggsql_text(
            "SELECT region, revenue, margin FROM {{ ref('fct_finance') }} ORDER BY revenue DESC LIMIT 25\n\nVISUALISE region, revenue, margin\nDRAW table\nLABEL revenue => \"Revenue (USD)\"\nCONFIG height => 400\n",
            "top_regions",
            None,
            "duckdb",
        )
        .unwrap();

        assert_eq!(chart.draw_type, "table");
        assert_eq!(
            chart
                .visualise
                .iter()
                .map(|mapping| (mapping.field.as_str(), mapping.role.as_str()))
                .collect::<Vec<_>>(),
            vec![
                ("region", "column"),
                ("revenue", "column"),
                ("margin", "column")
            ]
        );
        assert_eq!(chart.labels.get("revenue").unwrap(), "Revenue (USD)");
        assert_eq!(chart.config.get("height"), Some(&400));
        assert!(chart.has_order_by);
    }

    #[test]
    fn a_table_can_list_every_column_with_a_star() {
        let chart = parse_ggsql_text(
            "SELECT * FROM t\n\nVISUALISE *\nDRAW table\n",
            "everything",
            None,
            "duckdb",
        )
        .unwrap();

        assert_eq!(chart.visualise.len(), 1);
        assert_eq!(chart.visualise[0].field, "*");
        assert_eq!(chart.visualise[0].role, "column");

        let error = parse_ggsql_text(
            "SELECT * FROM t\n\nVISUALISE *, region\nDRAW table\n",
            "everything",
            None,
            "duckdb",
        )
        .unwrap_err();
        assert_eq!(
            error.to_string(),
            "VISUALISE * already lists every column; write it alone"
        );
    }

    #[test]
    fn a_table_rejects_roles_and_a_chart_rejects_a_column_list() {
        let table = parse_ggsql_text(
            "SELECT region, revenue FROM t\n\nVISUALISE region AS x, revenue AS y\nDRAW table\n",
            "c",
            None,
            "duckdb",
        )
        .unwrap_err();
        assert_eq!(
            table.to_string(),
            "table lists its columns without roles; write 'VISUALISE region, ...' or 'VISUALISE *', not 'region AS x'"
        );

        let bar = parse_ggsql_text(
            "SELECT region, revenue FROM t\n\nVISUALISE region, revenue\nDRAW bar\n",
            "c",
            None,
            "duckdb",
        )
        .unwrap_err();
        assert_eq!(
            bar.to_string(),
            "bar maps each column to a role (x, y, color); write 'region AS x', or DRAW table to list columns"
        );
    }

    #[test]
    fn a_table_rejects_a_repeated_column_and_any_interaction() {
        let twice = parse_ggsql_text(
            "SELECT region FROM t\n\nVISUALISE region, region\nDRAW table\n",
            "c",
            None,
            "duckdb",
        )
        .unwrap_err();
        assert_eq!(twice.to_string(), "table lists column 'region' twice");

        let interact = parse_ggsql_text(
            "SELECT region FROM t\n\nVISUALISE region\nDRAW table\nINTERACT tooltip\n",
            "c",
            None,
            "duckdb",
        )
        .unwrap_err();
        assert!(
            interact
                .to_string()
                .starts_with("table takes no INTERACT clause"),
            "{interact}"
        );
    }

    #[test]
    fn a_bare_word_that_is_not_a_column_is_still_an_invalid_mapping() {
        let error = parse_ggsql_text(
            "SELECT a FROM t\n\nVISUALISE a b\nDRAW table\n",
            "c",
            None,
            "duckdb",
        )
        .unwrap_err();
        assert_eq!(error.to_string(), "invalid VISUALISE mapping: a b");
    }

    #[test]
    fn parses_a_kpi_with_a_value_and_an_optional_comparison() {
        let chart = parse_ggsql_text(
            "SELECT sum(revenue) AS revenue, sum(previous) AS previous FROM t\n\nVISUALISE revenue AS value, previous AS compare\nDRAW kpi\nLABEL title => 'Revenue'\nLABEL compare => 'vs last month'\n",
            "revenue_kpi",
            None,
            "duckdb",
        )
        .unwrap();
        assert_eq!(chart.draw_type, "kpi");
        assert_eq!(chart.visualise.len(), 2);
        assert_eq!(chart.labels.get("compare").unwrap(), "vs last month");

        let alone = parse_ggsql_text(
            "SELECT 1 AS n\n\nVISUALISE n AS value\nDRAW kpi\n",
            "n",
            None,
            "duckdb",
        )
        .unwrap();
        assert_eq!(alone.visualise.len(), 1);
    }

    #[test]
    fn a_kpi_rejects_axes_a_column_list_and_interactions() {
        let axes = parse_ggsql_text(
            "SELECT a, b FROM t\n\nVISUALISE a AS x, b AS y\nDRAW kpi\n",
            "c",
            None,
            "duckdb",
        )
        .unwrap_err();
        assert_eq!(
            axes.to_string(),
            "kpi does not take a 'x' mapping; it takes value, compare"
        );

        let missing = parse_ggsql_text(
            "SELECT a FROM t\n\nVISUALISE a AS compare\nDRAW kpi\n",
            "c",
            None,
            "duckdb",
        )
        .unwrap_err();
        assert_eq!(missing.to_string(), "kpi requires a value mapping");

        let list = parse_ggsql_text(
            "SELECT a FROM t\n\nVISUALISE a\nDRAW kpi\n",
            "c",
            None,
            "duckdb",
        )
        .unwrap_err();
        assert_eq!(
            list.to_string(),
            "kpi maps each column to a role (value, compare); write 'a AS value', or DRAW table to list columns"
        );

        let interact = parse_ggsql_text(
            "SELECT a FROM t\n\nVISUALISE a AS value\nDRAW kpi\nINTERACT tooltip\n",
            "c",
            None,
            "duckdb",
        )
        .unwrap_err();
        assert!(interact
            .to_string()
            .starts_with("kpi takes no INTERACT clause"));
    }

    #[test]
    fn lists_the_columns_the_sql_mentions_and_whether_it_selects_star() {
        let chart = parse_ggsql_text(
            "WITH w AS (SELECT week, sum(active_users) AS active_users FROM t GROUP BY 1)\nSELECT w.week, Active_Users, lag(active_users) OVER (ORDER BY week) AS previous FROM w WHERE margin > 0 ORDER BY week DESC\n\nVISUALISE week AS x, active_users AS y\nDRAW line\n",
            "c",
            None,
            "duckdb",
        )
        .unwrap();
        assert_eq!(chart.sql_columns, vec!["active_users", "margin", "week"]);
        assert!(!chart.sql_selects_star);

        let star = parse_ggsql_text(
            "SELECT * FROM (SELECT f.* FROM t f) s\n\nVISUALISE a AS x, b AS y\nDRAW bar\n",
            "c",
            None,
            "duckdb",
        )
        .unwrap();
        assert!(star.sql_selects_star);

        let broken = parse_ggsql_text(
            "SELECT a b c FROM t\n\nVISUALISE a AS x, b AS y\nDRAW bar\n",
            "c",
            None,
            "duckdb",
        )
        .unwrap();
        assert!(broken.sql_columns.is_empty() && !broken.sql_selects_star);
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
            "unsupported chart type 'donut'; supported chart types: area, bar, boxplot, heatmap, histogram, kpi, line, pie, scatter, table"
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
