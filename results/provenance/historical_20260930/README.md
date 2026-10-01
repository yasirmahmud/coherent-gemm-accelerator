# Historical provenance audit

`inventory.csv` covers each main width at N=24 (published) and N=32
(recovered ece-lnx-10 cohort). `scripts/recover_provenance.py` inspects stage
logs/configurations and recovers ignored local trace files only when they
match a previously retained compressed-trace hash. N=32 traces were recovered
this way; logical hashes were recomputed from those retained bytes.

`candidate-*` files and candidate hashes preserve available local work files.
They are not proof of original per-stage source or binary identity. The
N=24 candidate files belong to the separate reproduction, not the published
cohort used for the three-width comparison. Historical simulator, guest,
source, CACTI, and exact command gaps remain explicit. No new rerun is needed
to report these comparisons as historical with those limits. Current source
or binaries cannot retrospectively recreate missing identities.

The manifest fingerprints recovery artifacts, not the missing historical
artifacts. Regenerate it after changing this README. Original archives and
manifests are preserved.

The historical source record's simulator hash has 62 hex digits and is invalid
SHA-256 metadata. `current-simulator.sha256` fingerprints the available local
binary (64 digits); it is a present-day observation, not a repair of the
historical record. The archived record is left intact.
