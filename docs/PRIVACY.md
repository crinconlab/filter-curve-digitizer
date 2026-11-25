# Privacy policy — Filter Curve Digitizer

Last updated: 25 November 2026.

Filter Curve Digitizer processes the chart images selected by the user locally. It does not upload chart images, extracted curves, passwords or exported CSV/JSON files to the developer.

## Network connections

The application optionally checks stable releases using GitHub's API. Automatic version checking is enabled by default, limited to approximately once per 24 hours, and can be disabled in the Help menu. A manual check can also be requested there.

Update downloads require user action. They contact GitHub and its download infrastructure using HTTPS, verify the downloaded package against GitHub's SHA-256 asset metadata, and do not automatically install or execute it. GitHub receives ordinary connection information, such as the source IP address and HTTP request information. See [GitHub's privacy statement](https://docs.github.com/en/site-policy/privacy-policies/github-general-privacy-statement).

No application usage analytics or tracking service is intentionally added by this project.

## Local files

The application saves preferences in `~/.filter-curve-digitizer/settings.json`, including onboarding and update-check preferences. User-requested image/CSV/JSON exports are saved at locations selected by the user. Requested update packages are saved in the Downloads directory.

Running from Python requires installing dependencies; the package index used by pip receives connection information during installation. This is separate from processing images in the application.

## Build and signing services

GitHub Actions compiles project sources. If approved and configured, SignPath receives build artifacts and build-origin metadata for signing. These are developer build operations, not network connections added to the running application. See [SignPath's privacy policy](https://signpath.io/privacy-policy).

## Contact and deletion

Contact Carlos Rincón at carlos@rinconcestero.com for questions. See [removal instructions](UNINSTALL.md) for deleting the application and its preferences.
