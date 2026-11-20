# Filter Curve Digitizer v1.3b

**Windows x64 · macOS Intel · macOS Apple Silicon · Linux x86_64 BETA**

Filter Curve Digitizer turns a colored spectral transmission curve in an image into sampled wavelength/transmission data, with exports for PixInsight FilterManager and Siril SPCC.

## What's included

- Standalone Windows 64-bit executable, built with Nuitka.
- Standalone macOS applications for Intel (x86_64) and Apple Silicon (arm64), built with PyInstaller.
- Standalone Linux x86_64 **BETA**, built with PyInstaller as a complete application directory.
- English-language graphical interface and application icon.
- Seven-click calibration: two known X-axis wavelength references, two Y-axis transmission references, two visible plot boundaries, and one curve-color sample.
- Wavelength scale interpolation and extrapolation across the *visible* graph, independent of the reference tick positions.
- Adjustable color tolerance, curve extraction, and a continuous green verification overlay.
- CSV export for PixInsight FilterManager.
- JSON definition export intended for Siril SPCC.
- Full [README and illustrated walkthrough](https://github.com/crinconlab/filter-curve-digitizer#readme), using an original demonstration plot.

## Download and run

**This Release remains a draft.** These downloads are planned; do not circulate links until the release is published and the corresponding assets have been uploaded.

| Platform | Package / launch | Verification |
| --- | --- | --- |
| Windows x64 | Extract Windows ZIP and run `Filter_Curve_Digitizer.exe` | Image processing and exports tested |
| macOS Intel (x86_64) | Extract macOS Intel ZIP and open `Filter Curve Digitizer.app` | App opened on Intel Mac |
| macOS Apple Silicon (arm64) | Extract Apple Silicon ZIP and open `Filter Curve Digitizer.app` | Compiled; no physical Apple Silicon user test reported |
| Linux x86_64 **BETA** | Extract entire `.tar.gz`, preserving the executable and `_internal/` directory | Limited test on Ubuntu 26.04.1 LTS under Parallels |

The compiled packages do not require a separate Python installation. macOS and Windows builds are unsigned. The system may display a first-launch warning: only run files obtained from a trusted source; do not disable OS security protections globally.

## Linux x86_64 — BETA (limited testing)

The Linux package contains a `Filter_Curve_Digitizer/` directory with **both** the `Filter_Curve_Digitizer` executable and an `_internal/` dependency directory. **Extract the entire archive and keep these together. Do not copy the executable to the desktop by itself.** Otherwise the program cannot locate bundled libraries such as `libpython3.11.so.1.0`.

Launch it from the parent directory with `./Filter_Curve_Digitizer/Filter_Curve_Digitizer`. If needed, use `./Filter_Curve_Digitizer/Filter_Curve_Digitizer --self-test` for an ImageTk rendering test.

**Status: BETA (Linux x86_64).** This is an early platform build with limited testing. It is not yet verified on a native Linux installation or other distributions.

**Tests completed on 20 November 2026:** Ubuntu 26.04.1 LTS x86_64 running as a Parallels virtual machine on an Intel Mac:
- Packaged application launches, and its Pillow/Tk image-rendering self-test displays a red image.
- Opens and displays a local image; seven-point calibration and curve extraction run successfully.
- Visual inspection shows the green extracted overlay following the source curve.
- Produces a readable PixInsight FilterManager CSV and a structurally valid Siril JSON with numeric wavelength/transmission arrays. These two supplied exports have slightly different wavelength ranges/sample counts, so they have **not** been verified as identical datasets.
- Reads an image from a macOS shared folder using its full path.

**Not tested:** native Linux hardware; other Linux distributions and desktop environments; installation/launch outside the tested Ubuntu/Parallels environment; actual CSV import into PixInsight; actual JSON import into Siril; broad compatibility or regression testing. In Parallels, the Tk file dialog may not navigate shared macOS folders conveniently, although entering a full path works. This VM-specific behavior is not established as a defect on native Linux.



## Verification and limitations

- The Windows application has been tested with a transmission plot, and the extracted curve has been checked visually against the source image.
- Exported CSV and JSON data have been compared for internal consistency.
- **Siril import has not yet been validated in the application.** JSON export does not automatically install a filter definition.
- Results are estimates digitized from a graphic, not measured or certified spectral transmission data.
- Image resolution, color overlap, background grid lines, manual calibration, and cropped plot areas can affect accuracy.
- Separate macOS Intel and Apple Silicon builds have been prepared. The Intel app has been launched on an Intel Mac; Apple Silicon has not been user-tested.

## Credits and license

Developed by **Carlos Rincón** ([crinconlab](https://github.com/crinconlab)).

Inspired by the original filter digitization workflow shared by **Sweetman Astrophotography**. This project is an independently developed implementation and does not claim endorsement or approval by Sweetman.

Released under the [MIT License](LICENSE).

For installation, the complete seven-click guide, troubleshooting and export details, see the [README](README.md).
