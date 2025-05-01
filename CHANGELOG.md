# Changelog

## [v0.2.10](https://github.com/datalab-org/datalab-api/tree/v0.2.10) (2025-04-29)

[Full Changelog](https://github.com/datalab-org/datalab-api/compare/v0.2.9...v0.2.10)

**Merged pull requests:**

- Remove typehint on base class `__enter__` that confuses parsers [\#59](https://github.com/datalab-org/datalab-api/pull/59) ([ml-evs](https://github.com/ml-evs))
- Bump astral-sh/setup-uv from 5 to 6 in the github-actions group [\#58](https://github.com/datalab-org/datalab-api/pull/58) ([dependabot[bot]](https://github.com/apps/dependabot))
- Use streaming downloads when requesting file data [\#57](https://github.com/datalab-org/datalab-api/pull/57) ([ml-evs](https://github.com/ml-evs))

## [v0.2.9](https://github.com/datalab-org/datalab-api/tree/v0.2.9) (2025-03-16)

[Full Changelog](https://github.com/datalab-org/datalab-api/compare/v0.2.8...v0.2.9)

**Merged pull requests:**

- Add test for `get_items` [\#54](https://github.com/datalab-org/datalab-api/pull/54) ([ml-evs](https://github.com/ml-evs))
- Only install bokeh if not running via emscripten [\#53](https://github.com/datalab-org/datalab-api/pull/53) ([ml-evs](https://github.com/ml-evs))

## [v0.2.8](https://github.com/datalab-org/datalab-api/tree/v0.2.8) (2025-03-16)

[Full Changelog](https://github.com/datalab-org/datalab-api/compare/v0.2.7...v0.2.8)

**Implemented enhancements:**

- Add method for pulling block info from deployment and add it to examples [\#40](https://github.com/datalab-org/datalab-api/pull/40) ([ml-evs](https://github.com/ml-evs))

**Fixed bugs:**

- File download fails when server's files are not stored in default location [\#51](https://github.com/datalab-org/datalab-api/issues/51)

**Merged pull requests:**

- Fix file download link so that it works locally and across all datalab configs [\#52](https://github.com/datalab-org/datalab-api/pull/52) ([ml-evs](https://github.com/ml-evs))
- add sublime files to .gitignore [\#49](https://github.com/datalab-org/datalab-api/pull/49) ([jdbocarsly](https://github.com/jdbocarsly))
- Replace RTD links with real domain [\#48](https://github.com/datalab-org/datalab-api/pull/48) ([ml-evs](https://github.com/ml-evs))
- Bump astral-sh/setup-uv from 4 to 5 in the github-actions group [\#45](https://github.com/datalab-org/datalab-api/pull/45) ([dependabot[bot]](https://github.com/apps/dependabot))
- Bump the github-actions group across 1 directory with 2 updates [\#44](https://github.com/datalab-org/datalab-api/pull/44) ([dependabot[bot]](https://github.com/apps/dependabot))
- Bump the github-actions group with 2 updates [\#37](https://github.com/datalab-org/datalab-api/pull/37) ([dependabot[bot]](https://github.com/apps/dependabot))
- Switch CI to uv and add dependabot + uv.lock [\#36](https://github.com/datalab-org/datalab-api/pull/36) ([ml-evs](https://github.com/ml-evs))

## [v0.2.7](https://github.com/datalab-org/datalab-api/tree/v0.2.7) (2024-10-12)

[Full Changelog](https://github.com/datalab-org/datalab-api/compare/v0.2.6...v0.2.7)

**Merged pull requests:**

- Guard against immutable ID not being returned from create collection [\#35](https://github.com/datalab-org/datalab-api/pull/35) ([ml-evs](https://github.com/ml-evs))
- Expose `update_data_block`: public interface for selective block updates [\#34](https://github.com/datalab-org/datalab-api/pull/34) ([ml-evs](https://github.com/ml-evs))
- Allow httpx session timeout to be configured [\#33](https://github.com/datalab-org/datalab-api/pull/33) ([ml-evs](https://github.com/ml-evs))

## [v0.2.6](https://github.com/datalab-org/datalab-api/tree/v0.2.6) (2024-10-08)

[Full Changelog](https://github.com/datalab-org/datalab-api/compare/v0.2.5...v0.2.6)

**Fixed bugs:**

- Remove `item_id` before sending request to automatically generate item ID [\#32](https://github.com/datalab-org/datalab-api/pull/32) ([ml-evs](https://github.com/ml-evs))

## [v0.2.5](https://github.com/datalab-org/datalab-api/tree/v0.2.5) (2024-10-08)

[Full Changelog](https://github.com/datalab-org/datalab-api/compare/v0.2.4...v0.2.5)

**Implemented enhancements:**

- Request randomly generated ID when creating item with no set ID [\#31](https://github.com/datalab-org/datalab-api/pull/31) ([ml-evs](https://github.com/ml-evs))

**Merged pull requests:**

- Make cheminventory helper more robust to missing barcodes [\#30](https://github.com/datalab-org/datalab-api/pull/30) ([ml-evs](https://github.com/ml-evs))
- Update demo deployment URLs to new domain [\#29](https://github.com/datalab-org/datalab-api/pull/29) ([ml-evs](https://github.com/ml-evs))

## [v0.2.4](https://github.com/datalab-org/datalab-api/tree/v0.2.4) (2024-07-03)

[Full Changelog](https://github.com/datalab-org/datalab-api/compare/v0.2.3...v0.2.4)

**Merged pull requests:**

- Migrate cheminventory import script to API helper [\#28](https://github.com/datalab-org/datalab-api/pull/28) ([ml-evs](https://github.com/ml-evs))
- Enable more ruff rules and refactor [\#27](https://github.com/datalab-org/datalab-api/pull/27) ([ml-evs](https://github.com/ml-evs))
- Dealing with collections [\#26](https://github.com/datalab-org/datalab-api/pull/26) ([ml-evs](https://github.com/ml-evs))
- Add `DuplicateItemError` exception type to allow scripts to be re-entrant [\#25](https://github.com/datalab-org/datalab-api/pull/25) ([ml-evs](https://github.com/ml-evs))

## [v0.2.3](https://github.com/datalab-org/datalab-api/tree/v0.2.3) (2024-06-05)

[Full Changelog](https://github.com/datalab-org/datalab-api/compare/v0.2.2...v0.2.3)

## [v0.2.2](https://github.com/datalab-org/datalab-api/tree/v0.2.2) (2024-05-28)

[Full Changelog](https://github.com/datalab-org/datalab-api/compare/v0.2.1...v0.2.2)

**Implemented enhancements:**

- Neatly redirect to correct API URL when provided with UI URL [\#21](https://github.com/datalab-org/datalab-api/issues/21)
- Add tests [\#2](https://github.com/datalab-org/datalab-api/issues/2)

**Closed issues:**

- Incorporate examples from hackathon into example notebook [\#20](https://github.com/datalab-org/datalab-api/issues/20)
- Confusion around instance\_url and api\_key when not passed at start, help strings are messed up and the app context does not store user info properly [\#4](https://github.com/datalab-org/datalab-api/issues/4)

**Merged pull requests:**

- Testing and CI setup [\#23](https://github.com/datalab-org/datalab-api/pull/23) ([ml-evs](https://github.com/ml-evs))
- Incorporate examples from hackathon into example notebook [\#22](https://github.com/datalab-org/datalab-api/pull/22) ([BenjaminCharmes](https://github.com/BenjaminCharmes))
- Updates from hackathon [\#19](https://github.com/datalab-org/datalab-api/pull/19) ([ml-evs](https://github.com/ml-evs))
- Add package description for PyPI [\#18](https://github.com/datalab-org/datalab-api/pull/18) ([ml-evs](https://github.com/ml-evs))

## [v0.2.1](https://github.com/datalab-org/datalab-api/tree/v0.2.1) (2024-04-15)

[Full Changelog](https://github.com/datalab-org/datalab-api/compare/v0.2.0...v0.2.1)

**Implemented enhancements:**

- Strip quotes from API keys to avoid confusing errors [\#14](https://github.com/datalab-org/datalab-api/issues/14)

**Closed issues:**

- Fix PyPI publisher auth [\#12](https://github.com/datalab-org/datalab-api/issues/12)

**Merged pull requests:**

- Strip quotes from API keys when present [\#15](https://github.com/datalab-org/datalab-api/pull/15) ([ml-evs](https://github.com/ml-evs))

## [v0.2.0](https://github.com/datalab-org/datalab-api/tree/v0.2.0) (2024-04-14)

[Full Changelog](https://github.com/datalab-org/datalab-api/compare/v0.1.0...v0.2.0)

**Implemented enhancements:**

- Generate docs page [\#1](https://github.com/datalab-org/datalab-api/issues/1)

**Closed issues:**

- Rewrite git history to exclude big example notebook [\#11](https://github.com/datalab-org/datalab-api/issues/11)
- Add example notebooks and build documentation site [\#10](https://github.com/datalab-org/datalab-api/issues/10)
- Cannot do anything with block response [\#5](https://github.com/datalab-org/datalab-api/issues/5)

## [v0.1.0](https://github.com/datalab-org/datalab-api/tree/v0.1.0) (2024-03-12)

[Full Changelog](https://github.com/datalab-org/datalab-api/compare/af6a29a434dc8d2648b10ac28154299822b86dff...v0.1.0)

**Closed issues:**

- Make client usable via context manager [\#7](https://github.com/datalab-org/datalab-api/issues/7)



\* *This Changelog was automatically generated by [github_changelog_generator](https://github.com/github-changelog-generator/github-changelog-generator)*
