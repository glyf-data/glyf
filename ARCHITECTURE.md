
### `ARCHITECTURE.md`

```md
# Architecture

```text
dbt project
   ↓
dbt manifest.json
   ↓
ggsql file parser
   ↓
ref/source resolver
   ↓
query executor
   ↓
chart renderer
   ↓
artifact store
   ↓
dashboard generator