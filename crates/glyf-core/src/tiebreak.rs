//! Settle the ties a query's `ORDER BY` leaves.
//!
//! `ORDER BY department` promises nothing about two rows with the same
//! department, so the warehouse may return them either way round, and a chart
//! drawn from them changes from build to build: which point is on top, a
//! stack's segments, a table's rows, and under a `LIMIT` which rows make the
//! cut. glyf appends the query's other output columns to its outermost
//! `ORDER BY`. The keys the author wrote come first and are untouched, so the
//! order they asked for holds; the added ones only decide what theirs call
//! equal.
//!
//! The SQL is edited as text, not re-printed from the syntax tree, so the
//! query reads as written with the keys added at the end of its `ORDER BY`.
//! The result is parsed again and must be the same query with longer
//! `ORDER BY`; anything else leaves the SQL alone.

use sqlparser::ast::{Expr, OrderByKind, Query, SelectItem, SetExpr, Statement, Value};
use sqlparser::keywords::Keyword;
use sqlparser::parser::Parser;
use sqlparser::tokenizer::{Location, Token, TokenWithSpan, Tokenizer};

use crate::ggsql::sql_dialect;

/// What glyf can do about a query's ties.
#[derive(Debug, Clone, Default, PartialEq, Eq)]
pub struct Tiebreak {
    /// The query with the tiebreak keys appended, when glyf could add them.
    pub sql: Option<String>,
    /// The output columns added, by name (`column 3` for an unnamed one).
    pub added: Vec<String>,
    /// The author's keys as output column names, when every key is one: the
    /// columns a tie can be seen in once the rows are back. Empty otherwise.
    pub keys: Vec<String>,
    /// Why the SQL could not be given a tiebreak, when it has an `ORDER BY`.
    pub reason: Option<String>,
    /// Whether the query keeps only some rows (`LIMIT` or `FETCH`): then the
    /// ties decide which rows come back, not only their order.
    pub limited: bool,
}

/// The tiebreak for one compiled query. A query without an outer `ORDER BY`
/// gets an empty answer: glyf orders those rows itself.
pub fn order_tiebreak(sql: &str, dialect: &str) -> Tiebreak {
    let dialect_impl = sql_dialect(dialect);
    let Ok(statements) = Parser::parse_sql(dialect_impl.as_ref(), sql) else {
        return Tiebreak::default();
    };
    let [Statement::Query(query)] = statements.as_slice() else {
        return Tiebreak::default();
    };
    let Some(order_by) = &query.order_by else {
        return Tiebreak::default();
    };
    let OrderByKind::Expressions(order_exprs) = &order_by.kind else {
        // `ORDER BY ALL` orders by every column already.
        return Tiebreak::default();
    };
    let limited = query.limit_clause.is_some() || query.fetch.is_some();
    let SetExpr::Select(select) = query.body.as_ref() else {
        return Tiebreak {
            limited,
            reason: Some(
                "its ORDER BY orders a set operation, which glyf leaves as written".into(),
            ),
            ..Tiebreak::default()
        };
    };

    let outputs: Vec<Option<String>> = select.projection.iter().map(output_name).collect();
    let keys = key_columns(
        order_exprs.iter().map(|e| &e.expr),
        &select.projection,
        &outputs,
    );

    if select.projection.iter().any(|item| {
        matches!(
            item,
            SelectItem::Wildcard(_) | SelectItem::QualifiedWildcard(_, _)
        )
    }) {
        return Tiebreak {
            keys,
            limited,
            reason: Some(
                "it selects *, so glyf cannot name the columns to add before it runs".into(),
            ),
            ..Tiebreak::default()
        };
    }

    let used = used_positions(
        order_exprs.iter().map(|e| &e.expr),
        &select.projection,
        &outputs,
    );
    let mut appended = Vec::new();
    let mut added = Vec::new();
    for (index, item) in select.projection.iter().enumerate() {
        if used.contains(&index) {
            continue;
        }
        appended.push(order_key(item, index));
        added.push(
            outputs[index]
                .clone()
                .unwrap_or_else(|| format!("column {}", index + 1)),
        );
    }
    if appended.is_empty() {
        return Tiebreak {
            keys,
            limited,
            ..Tiebreak::default()
        };
    }

    let first = order_exprs
        .first()
        .map(|e| sqlparser::ast::Spanned::span(&e.expr).start);
    let rewritten = first
        .and_then(|start| insert_at_order_by_end(sql, dialect, start, &appended))
        .filter(|candidate| same_query_with_keys(dialect, query, candidate, &appended));
    match rewritten {
        Some(sql) => Tiebreak {
            sql: Some(sql),
            added,
            keys,
            reason: None,
            limited,
        },
        None => Tiebreak {
            keys,
            limited,
            reason: Some("glyf could not find where its ORDER BY ends".into()),
            ..Tiebreak::default()
        },
    }
}

/// The name a projection item has in the result, when it has one.
fn output_name(item: &SelectItem) -> Option<String> {
    match item {
        SelectItem::ExprWithAlias { alias, .. } => Some(alias.value.clone()),
        SelectItem::UnnamedExpr(Expr::Identifier(ident)) => Some(ident.value.clone()),
        SelectItem::UnnamedExpr(Expr::CompoundIdentifier(parts)) => {
            parts.last().map(|ident| ident.value.clone())
        }
        _ => None,
    }
}

/// How the tiebreak refers to a projection item: by the name the author wrote
/// for it, or by its position when it has none. Every warehouse glyf runs on
/// takes both in an `ORDER BY`.
fn order_key(item: &SelectItem, index: usize) -> String {
    match item {
        SelectItem::ExprWithAlias { alias, .. } => alias.to_string(),
        SelectItem::UnnamedExpr(expr @ (Expr::Identifier(_) | Expr::CompoundIdentifier(_))) => {
            expr.to_string()
        }
        _ => (index + 1).to_string(),
    }
}

/// The projection positions the author's keys already order by.
fn used_positions<'a>(
    exprs: impl Iterator<Item = &'a Expr>,
    projection: &[SelectItem],
    outputs: &[Option<String>],
) -> Vec<usize> {
    exprs
        .filter_map(|expr| position_of(expr, projection, outputs))
        .collect()
}

fn position_of(
    expr: &Expr,
    projection: &[SelectItem],
    outputs: &[Option<String>],
) -> Option<usize> {
    if let Expr::Value(value) = expr {
        if let Value::Number(number, _) = &value.value {
            return number
                .parse::<usize>()
                .ok()
                .filter(|n| *n >= 1)
                .map(|n| n - 1);
        }
    }
    let written = expr.to_string();
    projection.iter().zip(outputs).position(|(item, name)| {
        let same_expr = match item {
            SelectItem::UnnamedExpr(e) | SelectItem::ExprWithAlias { expr: e, .. } => {
                e.to_string() == written
            }
            _ => false,
        };
        let same_name = match (expr, name) {
            (Expr::Identifier(ident), Some(name)) => ident.value.eq_ignore_ascii_case(name),
            _ => false,
        };
        same_expr || same_name
    })
}

/// The author's keys as output column names, or nothing if any key is not one.
fn key_columns<'a>(
    exprs: impl Iterator<Item = &'a Expr>,
    projection: &[SelectItem],
    outputs: &[Option<String>],
) -> Vec<String> {
    let mut keys = Vec::new();
    for expr in exprs {
        let wildcard = projection.iter().any(|item| {
            matches!(
                item,
                SelectItem::Wildcard(_) | SelectItem::QualifiedWildcard(_, _)
            )
        });
        let name = match position_of(expr, projection, outputs) {
            Some(index) => outputs.get(index).cloned().flatten(),
            // Under `SELECT *` a plain column key is a result column too.
            None if wildcard => match expr {
                Expr::Identifier(ident) => Some(ident.value.clone()),
                Expr::CompoundIdentifier(parts) => parts.last().map(|i| i.value.clone()),
                _ => None,
            },
            None => None,
        };
        match name {
            Some(name) => keys.push(name),
            None => return Vec::new(),
        }
    }
    keys
}

/// The SQL with `, <keys>` after the last key of the `ORDER BY` whose first
/// key starts at `start`.
///
/// Walks the tokens from that key at bracket depth zero until the clause
/// ends: a `LIMIT`, `OFFSET`, `FETCH` or `FOR`, a `;`, a closing bracket or
/// the end. The last token before that is where the clause ends, `ASC`,
/// `DESC` and `NULLS LAST` included, which the syntax tree's positions leave
/// out.
fn insert_at_order_by_end(
    sql: &str,
    dialect: &str,
    start: Location,
    appended: &[String],
) -> Option<String> {
    let dialect_impl = sql_dialect(dialect);
    let tokens: Vec<TokenWithSpan> = Tokenizer::new(dialect_impl.as_ref(), sql)
        .tokenize_with_location()
        .ok()?;
    let first = tokens.iter().position(|t| t.span.start == start)?;
    let mut depth = 0i32;
    let mut end: Option<Location> = None;
    for token in &tokens[first..] {
        match &token.token {
            Token::Whitespace(_) => continue,
            Token::LParen | Token::LBracket => depth += 1,
            Token::RParen | Token::RBracket if depth == 0 => break,
            Token::RParen | Token::RBracket => depth -= 1,
            Token::SemiColon | Token::EOF if depth == 0 => break,
            Token::Word(word)
                if depth == 0
                    && matches!(
                        word.keyword,
                        Keyword::LIMIT | Keyword::OFFSET | Keyword::FETCH | Keyword::FOR
                    ) =>
            {
                break
            }
            _ => {}
        }
        end = Some(token.span.end);
    }
    let offset = byte_offset(sql, end?)?;
    Some(format!(
        "{}, {}{}",
        &sql[..offset],
        appended.join(", "),
        &sql[offset..]
    ))
}

/// The byte offset of a tokenizer location: lines from 1, columns in
/// characters from 1.
fn byte_offset(sql: &str, location: Location) -> Option<usize> {
    let mut line = 1u64;
    let mut column = 1u64;
    for (offset, ch) in sql.char_indices() {
        if line == location.line && column == location.column {
            return Some(offset);
        }
        if ch == '\n' {
            line += 1;
            column = 1;
        } else {
            column += 1;
        }
    }
    (line == location.line && column == location.column).then_some(sql.len())
}

/// Whether `candidate` is `original` with exactly `appended` added to the end
/// of its `ORDER BY`, and nothing else changed.
fn same_query_with_keys(
    dialect: &str,
    original: &Query,
    candidate: &str,
    appended: &[String],
) -> bool {
    let dialect_impl = sql_dialect(dialect);
    let Ok(statements) = Parser::parse_sql(dialect_impl.as_ref(), candidate) else {
        return false;
    };
    let [Statement::Query(rewritten)] = statements.as_slice() else {
        return false;
    };
    let (Some(before), Some(after)) = (&original.order_by, &rewritten.order_by) else {
        return false;
    };
    let (OrderByKind::Expressions(before), OrderByKind::Expressions(after)) =
        (&before.kind, &after.kind)
    else {
        return false;
    };
    if after.len() != before.len() + appended.len() || after[..before.len()] != before[..] {
        return false;
    }
    let added_match = after[before.len()..]
        .iter()
        .zip(appended)
        .all(|(expr, key)| expr.options.sort.is_none() && expr.expr.to_string() == *key);
    let mut rest_before = original.clone();
    let mut rest_after = rewritten.as_ref().clone();
    rest_before.order_by = None;
    rest_after.order_by = None;
    added_match && rest_before == rest_after
}

#[cfg(test)]
mod tests {
    use super::*;

    fn tiebreak(sql: &str) -> Tiebreak {
        order_tiebreak(sql, "duckdb")
    }

    #[test]
    fn appends_the_other_columns_after_the_authors_keys() {
        let result = tiebreak("SELECT department, expenses, month FROM t ORDER BY department");
        assert_eq!(
            result.sql.as_deref(),
            Some("SELECT department, expenses, month FROM t ORDER BY department, expenses, month")
        );
        assert_eq!(result.added, ["expenses", "month"]);
        assert_eq!(result.keys, ["department"]);
    }

    #[test]
    fn keeps_directions_and_nulls_and_goes_before_limit() {
        let result = tiebreak(
            "SELECT account_id, plan, sessions FROM t\nORDER BY sessions DESC NULLS LAST\nLIMIT 10",
        );
        assert_eq!(
            result.sql.as_deref(),
            Some("SELECT account_id, plan, sessions FROM t\nORDER BY sessions DESC NULLS LAST, account_id, plan\nLIMIT 10")
        );
    }

    #[test]
    fn a_function_key_keeps_its_closing_bracket() {
        let result = tiebreak("SELECT name, n FROM t ORDER BY lower(name)");
        assert_eq!(
            result.sql.as_deref(),
            Some("SELECT name, n FROM t ORDER BY lower(name), name, n")
        );
        assert!(result.keys.is_empty(), "lower(name) is not a result column");
    }

    #[test]
    fn aliases_and_ordinals_count_as_already_ordered() {
        let result = tiebreak(
            "SELECT month, sum(revenue) AS revenue, count(*) FROM t GROUP BY 1 ORDER BY 1, revenue",
        );
        assert_eq!(
            result.sql.as_deref(),
            Some("SELECT month, sum(revenue) AS revenue, count(*) FROM t GROUP BY 1 ORDER BY 1, revenue, 3")
        );
        assert_eq!(result.added, ["column 3"]);
        assert_eq!(result.keys, ["month", "revenue"]);
    }

    #[test]
    fn a_fully_ordered_query_is_left_alone() {
        let result = tiebreak("SELECT a, b FROM t ORDER BY a, b");
        assert_eq!(result.sql, None);
        assert_eq!(result.reason, None);
    }

    #[test]
    fn nested_order_bys_are_not_the_outer_one() {
        let sql = "WITH w AS (SELECT a, b FROM t ORDER BY a) SELECT a, b FROM w";
        assert_eq!(tiebreak(sql), Tiebreak::default());
        let outer = tiebreak("SELECT a, b, row_number() OVER (ORDER BY a) AS r FROM t ORDER BY a");
        assert_eq!(
            outer.sql.as_deref(),
            Some("SELECT a, b, row_number() OVER (ORDER BY a) AS r FROM t ORDER BY a, b, r")
        );
    }

    #[test]
    fn select_star_names_its_keys_but_cannot_be_rewritten() {
        let result = tiebreak("SELECT * FROM t ORDER BY plan LIMIT 5");
        assert_eq!(result.sql, None);
        assert_eq!(result.keys, ["plan"]);
        assert!(result.reason.unwrap().contains("selects *"));
        assert!(result.limited);
    }

    #[test]
    fn a_trailing_semicolon_and_comment_stay_where_they_were() {
        let result = tiebreak("SELECT a, b FROM t ORDER BY a -- by a\n;");
        assert_eq!(
            result.sql.as_deref(),
            Some("SELECT a, b FROM t ORDER BY a, b -- by a\n;")
        );
    }

    #[test]
    fn text_before_the_order_by_can_be_any_width() {
        let result =
            tiebreak("SELECT 'café ☕' AS label,\n  t.month, n\nFROM t\nORDER BY label\nOFFSET 2");
        assert_eq!(
            result.sql.as_deref(),
            Some("SELECT 'café ☕' AS label,\n  t.month, n\nFROM t\nORDER BY label, t.month, n\nOFFSET 2")
        );
        assert_eq!(result.added, ["month", "n"]);
    }

    #[test]
    fn a_quoted_alias_is_referred_to_as_written() {
        let result = order_tiebreak(
            "SELECT plan AS `Plan`, sessions FROM `p.d.t` ORDER BY sessions DESC LIMIT 3",
            "bigquery",
        );
        assert_eq!(
            result.sql.as_deref(),
            Some("SELECT plan AS `Plan`, sessions FROM `p.d.t` ORDER BY sessions DESC, `Plan` LIMIT 3")
        );
    }

    #[test]
    fn no_order_by_gets_nothing() {
        assert_eq!(tiebreak("SELECT a, b FROM t"), Tiebreak::default());
    }
}
