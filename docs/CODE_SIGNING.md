# Code signing policy

## Current status

SignPath Foundation integration is being prepared. Admission, account setup and production signing are **pending**. Existing releases are unsigned. No claim of SignPath approval or sponsorship is made at this stage.

If the application is accepted and production signing is enabled, the attribution will be: **Free code signing provided by [SignPath.io](https://signpath.io), certificate by [SignPath Foundation](https://signpath.org).**

## Project and maintainer

Filter Curve Digitizer is an independent, MIT-licensed astrophotography utility developed and maintained by **Carlos Rincón**, GitHub account [crinconlab](https://github.com/crinconlab).

Carlos Rincón holds PixInsight CPD status. Evidence is available from the maintainer on request. This is background about the developer; it does not mean that PixInsight certifies, endorses or signs Filter Curve Digitizer.

- Authors/committers: Carlos Rincón (crinconlab).
- Reviewer for external contributions: Carlos Rincón (crinconlab).
- Signing approver: Carlos Rincón (crinconlab).
- Contributors must use multi-factor authentication for GitHub and SignPath where applicable. The maintainer has confirmed GitHub MFA is enabled; SignPath MFA must be enabled during account setup.

## Scope and approval

Only this project's Windows executable, built from its public source by the dedicated GitHub Actions workflow, may be submitted for signing. Third-party libraries must not be signed as if authored by this project.

The workflow is manually dispatched from main. Signing is disabled by default and additionally requires explicit configuration and credentials. Each signing request must require manual approval in SignPath. No signing request or GitHub artifact automatically publishes a Release or changes the website.

A signed candidate must pass signature verification and receive a separate review, including antivirus analysis, before a publication decision. A signature establishes origin and integrity; it is not a safety guarantee.

## Privacy and removal

See the [privacy policy](PRIVACY.md) and [removal instructions](UNINSTALL.md).

## References

- [SignPath Foundation conditions](https://signpath.org/terms)
- [GitHub integration](https://docs.signpath.io/trusted-build-systems/github)
- [Setup and validation checklist](SIGNPATH_SETUP.md)
