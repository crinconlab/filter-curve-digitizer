# Filter Curve Digitizer v1.4.0

Filter Curve Digitizer converts colour-coded spectral transmission curves from manufacturer charts into wavelength/transmission samples. It exports CSV files for PixInsight FilterManager and JSON definitions intended for Siril SPCC.

## What's new

- **Seven-click calibration guide.** An introductory guide explains the four stages of calibration. The first four clicks must correspond exactly to the values in the X/Y reference fields.
- **Clearer calibration prompts.** The current click and its corresponding wavelength or transmission value are shown prominently above the chart. Separate reminders explain the extraction boundaries and the green verification overlay.
- **Update notifications.** The app can check for stable releases on GitHub, including via **Help → Check for updates…**. Automatic checks can be disabled. Checks run in the background and are limited to approximately once a day.
- **Direct update downloads.** When a newer compatible release is available, the app can download the matching package into the user's Downloads folder without requiring navigation through GitHub. Transfers use HTTPS with certificate verification and require a matching SHA-256 digest from GitHub release asset metadata. Installation remains manual.
- **Consistent app icon** across all operating systems.
- **Native Apple Silicon** build alongside the macOS Intel build.
- **Linux AppImage** replaces the Linux directory-based package as the user-facing format.

## Release downloads

| Platform | File |
| --- | --- |
| Windows x64 | `Filter-Curve-Digitizer-v1.4-Windows-x64.exe` |
| macOS Intel | `Filter-Curve-Digitizer-v1.4-macOS-Intel.zip` |
| macOS Apple Silicon (M-series) | `Filter-Curve-Digitizer-v1.4-macOS-Apple-Silicon.zip` |
| Linux x86_64 | `Filter-Curve-Digitizer-v1.4-Linux-x86_64.AppImage` |

A separate Linux `.sha256` file is provided for manual verification.

## Important limitations

- Extracted spectra are approximations of published charts, not physical measurements of the filters. Always inspect the green overlay before exporting.
- The macOS apps and Windows executable are not currently signed or notarized.
- Linux AppImage has limited distribution testing and remains **beta**.
- Importing exported JSON definitions into Siril is not yet established as independently verified.
- Update downloads are **not automatic installations**. App users decide whether and when to open and install them.
- The download feature has passed simulated tests; a full end-to-end update between two published stable Releases has not yet been validated.
- Updates are offered only for stable GitHub Releases, not pre-releases.

Developer: Carlos Rincón. Source repository: https://github.com/crinconlab/filter-curve-digitizer

## Code signing policy

The v1.4.0 release remains unsigned. The free SignPath Foundation application was declined on 25 November 2026 for insufficient public visibility and project track record. This route is closed for now; no paid signing plan will be pursued and the optional integration remains disabled. See the current [Code signing policy](https://github.com/crinconlab/filter-curve-digitizer/blob/main/docs/CODE_SIGNING.md), [privacy policy](https://github.com/crinconlab/filter-curve-digitizer/blob/main/docs/PRIVACY.md) and [setup checklist](https://github.com/crinconlab/filter-curve-digitizer/blob/main/docs/SIGNPATH_SETUP.md). No signed candidate has been produced or published.
