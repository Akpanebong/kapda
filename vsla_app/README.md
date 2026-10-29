# KAPDA VSLA module

This attached Django module provides KAPDA staff with VSLA group, member, meeting, savings, loan and social-fund workflows.

It is registered as `vsla_app.vsla` and exposed at `/vsla/`. It uses the shared KAPDA `accounts.User` model, staff-only access rules, KAPDA navigation, logo and branding styles.

The module is intentionally separate from the former BSLFSR VSLA models. The legacy BSLFSR VSLA tables and CRUD routes have been removed; this is now the single VSLA implementation in the project.
