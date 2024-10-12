# Changelog

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
