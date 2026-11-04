# Sudina Division — Discovery and Matching

## Contribution

This folder owns the `discovery` application and its templates:

- Category, Skill, and UserSkill models with database constraints.
- Skill add/list/delete forms and views.
- Keyword search with AND semantics across project and owner fields.
- Category, project type, status, skill, and sort dropdown filters.
- Safe handling of invalid query parameters and pagination.
- People finder excluding the current user and opted-out profiles.
- Recommended projects and skill match percentages.
- Search-session recording for recent searches.

## Rubric coverage

- Search bar and predefined dropdown requirement.
- Forms, models, views, templates, and CRUD requirement.
- People finder and recommendation/member feature gates.
- Query hygiene using `select_related` and `prefetch_related`.
- Empty search, no-results, invalid parameter, guest best-match, and zero-skill cases.

## Copy to the main application

From the repository root:

```bash
cp -a Divisions/Sudina/discovery/. discovery/
cp -a Divisions/Sudina/templates/discovery/. templates/discovery/
.venv/bin/python manage.py test discovery.tests
```

The discovery app depends on the existing `projects`, `accounts`, and `activity` contracts, so integrate it after the Central baseline is available.

Run the full gate before committing and use a message such as `Add discovery search and skill matching`.
