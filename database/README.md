# Database

The operational schema is normalized and indexed for customer/date access. Production deployments use PostgreSQL; local development defaults to SQLite. `schemas/001_initial_schema.sql` documents the PostgreSQL DDL and `queries/customer360_view.sql` provides a reusable analytical view.
