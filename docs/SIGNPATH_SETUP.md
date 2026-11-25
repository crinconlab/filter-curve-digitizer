# SignPath setup — pending admission

This preparation does not sign an existing release, submit an admission form, create a paid plan, or publish a new binary. There is no production signing credential configured by these files.

## Admission

Apply only for the free SignPath Foundation program. Project: Filter Curve Digitizer. Maintainer: Carlos Rincón (crinconlab), PixInsight CPD; the maintainer can provide the accreditation email privately if requested. CPD is not a certification of this application.

Use the repository and its published v1.4.0 release as evidence. Explain the project's recent public history honestly. Include the completed Microsoft (Not malware), Avira (Clean) and Symantec/Broadcom (Detection Removed, JLY50457046) reviews, while disclosing remaining vendor detections and the incomplete dynamic-analysis coverage. Do not promise acceptance or describe the application as already signed.

Public links:
- Repository/homepage: https://github.com/crinconlab/filter-curve-digitizer
- Download and signing policy: https://github.com/crinconlab/filter-curve-digitizer/blob/main/docs/CODE_SIGNING.md
- Privacy: https://github.com/crinconlab/filter-curve-digitizer/blob/main/docs/PRIVACY.md
- Releases: https://github.com/crinconlab/filter-curve-digitizer/releases/tag/v1.4.0

## After approval

1. Enable MFA in SignPath. Confirm the GitHub App permissions and scope it to this repository only.
2. Have SignPath configure verified GitHub build provenance for this repository and the `windows-signpath-candidate.yml` workflow.
3. Import `.signpath/artifact-configuration.xml` with slug `windows-candidate`. The ZIP root matches actions/upload-artifact. Only the outer application EXE is signed; do not sign third-party DLLs as this project.
4. Configure a signing policy with mandatory manual approval by Carlos Rincón. Disable automatic approval. Ask SignPath to review the project's small-team arrangement.
5. Create repository variables `SIGNPATH_ORGANIZATION_ID`, `SIGNPATH_PROJECT_SLUG`, `SIGNPATH_POLICY_SLUG`, and finally `SIGNPATH_ENABLED=true`. Store `SIGNPATH_API_TOKEN` as a GitHub Actions secret with submitter-only permission; never commit it.
6. Verify the approved Foundation certificate subject and timestamp service. If the actual subject differs from the workflow's Foundation check, confirm it with SignPath before changing the expected publisher.

## Candidate workflow

Manually run **Windows signing candidate (SignPath)** on main with request_signing **false** first. It runs regression tests, compiles, checks metadata and saves unsigned candidate plus evidence. Signing is a second manually dispatched run with request_signing **true** after account setup. It requires manual SignPath approval, verifies the returned signature, timestamp and publisher, then saves the signed EXE as a GitHub Actions artifact. There is no Release upload step and no contents:write permission.

Artifacts in a public repository must not be described as private: users with GitHub access may be able to download them. The signed artifact is a review candidate, not a supported public release. It expires after 14 days.

This build uses the existing requirements and records resolved versions. They are not pinned, so this is not a bit-for-bit reproducible build claim. Pinned action commits protect the workflow references; dependency locking remains a separate improvement.

## Antivirus comparison and publication

Keep both files from the **same build/signing run** and compare their SHA-256 and VirusTotal results. Do not compare only the new signed build to the old v1.4 EXE: metadata, compiler and resolved dependencies can differ.

The signature changes SHA-256. Preserve the original v1.4 EXE and existing review cases. Do not overwrite release assets or announce a signed release until signature and antivirus review are complete. Submit the signed candidate to VirusTotal manually; no API key, scheduled upload or automatic telemetry is introduced.

## Removal

See [UNINSTALL.md](UNINSTALL.md).

## Validation still required

- Admission and production account setup.
- SignPath schema/import validation of the XML configuration.
- A complete unsigned candidate run on GitHub Windows.
- A complete production signing and timestamp verification run.
- Antivirus comparison of same-build unsigned and signed candidates.
