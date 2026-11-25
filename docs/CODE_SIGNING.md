# Code signing policy

## Current status

The free SignPath Foundation application was declined on **25 November 2026** because the project does not yet show the public visibility, community adoption and sustained track record required by the program. SignPath explicitly stated that this was not a judgment on the project's quality or potential.

This signing route is **closed for now**. No paid signing plan will be pursued. Existing releases remain unsigned; no signed candidate has been produced or published. The optional integration remains disabled and must not be enabled under the current decision. There is no SignPath approval, certificate or sponsorship.

The technical preparation is retained as inactive reference material, not as an active implementation plan. Any future reopening requires a new maintainer decision and a fresh eligibility review.

## Project and maintainer

Filter Curve Digitizer is an independent, MIT-licensed astrophotography utility developed and maintained by **Carlos Rincón**, GitHub account [crinconlab](https://github.com/crinconlab).

Carlos Rincón holds PixInsight CPD status. Evidence is available from the maintainer on request. This is background about the developer; it does not mean that PixInsight certifies, endorses or signs Filter Curve Digitizer.

- Authors/committers: Carlos Rincón (crinconlab).
- Reviewer for external contributions: Carlos Rincón (crinconlab).
- Maintainer responsible for any future signing decision: Carlos Rincón (crinconlab).
- Contributors must use multi-factor authentication for GitHub and SignPath where applicable. The maintainer has confirmed GitHub MFA is enabled; SignPath setup is not being pursued.

## Requirements if signing is reconsidered

If signing is reopened and approved in the future, only this project's Windows executable, built from its public source by the dedicated GitHub Actions workflow, may be submitted for signing. Third-party libraries must not be signed as if authored by this project.

The workflow is manually dispatched from main. Signing is disabled by default and additionally requires explicit configuration and credentials. Each signing request must require manual approval in SignPath. No signing request or GitHub artifact automatically publishes a Release or changes the website.

A signed candidate must pass signature verification and receive a separate review, including antivirus analysis, before a publication decision. A signature establishes origin and integrity; it is not a safety guarantee.

## Privacy and removal

See the [privacy policy](PRIVACY.md) and [removal instructions](UNINSTALL.md).

## References

- [SignPath Foundation conditions](https://signpath.org/terms)
- [GitHub integration](https://docs.signpath.io/trusted-build-systems/github)
- [Setup and validation checklist](SIGNPATH_SETUP.md)
