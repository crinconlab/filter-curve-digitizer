# Filter Curve Digitizer v1.3b

**Windows x64 · macOS · Linux x86_64 testing**

Filter Curve Digitizer turns a colored spectral transmission curve in an image into sampled wavelength/transmission data, with exports for PixInsight FilterManager and Siril SPCC.

## What's included

- Standalone Windows 64-bit executable, built with Nuitka.
- English-language graphical interface and application icon.
- Seven-click calibration: two known X-axis wavelength references, two Y-axis transmission references, two visible plot boundaries, and one curve-color sample.
- Wavelength scale interpolation and extrapolation across the *visible* graph, independent of the reference tick positions.
- Adjustable color tolerance, curve extraction, and a continuous green verification overlay.
- CSV export for PixInsight FilterManager.
- JSON definition export intended for Siril SPCC.
- Full [README and illustrated walkthrough](https://github.com/crinconlab/filter-curve-digitizer#readme), using an original demonstration plot.

## Download and run

Download the Windows x64 ZIP attached to this release, extract it, and run `Filter_Curve_Digitizer.exe`. Python is not required for the compiled Windows application.

**Windows security notice:** The executable is not digitally signed. Windows SmartScreen may flag an unknown publisher; verify that you obtained the program from this repository before running it.

## Linux x86_64 — installation warning (validation in progress)

The Linux package contains a `Filter_Curve_Digitizer/` directory with **both** the `Filter_Curve_Digitizer` executable and an `_internal/` dependency directory. **Extract the entire archive and keep these together. Do not copy the executable to the desktop by itself.** Otherwise the program cannot locate bundled libraries such as `libpython3.11.so.1.0`.

Launch it from the parent directory with `./Filter_Curve_Digitizer/Filter_Curve_Digitizer`. If needed, use `./Filter_Curve_Digitizer/Filter_Curve_Digitizer --self-test` for an ImageTk rendering test.

A Linux x86_64 build has launched and displayed an image on Ubuntu 26.04 under Parallels. Linux curve extraction and exports have **not yet been fully verified**; do not describe Linux as fully tested until those checks succeed. Other Linux distributions have not been verified.

## Verification and limitations

- The Windows application has been tested with a transmission plot, and the extracted curve has been checked visually against the source image.
- Exported CSV and JSON data have been compared for internal consistency.
- **Siril import has not yet been validated in the application.** JSON export does not automatically install a filter definition.
- Results are estimates digitized from a graphic, not measured or certified spectral transmission data.
- Image resolution, color overlap, background grid lines, manual calibration, and cropped plot areas can affect accuracy.
- Separate macOS Intel and Apple Silicon builds are prepared. The Intel app has been launched on an Intel Mac; Apple Silicon has not been user-tested.

## Credits and license

Developed by **Carlos Rincón** ([crinconlab](https://github.com/crinconlab)).

Inspired by the original filter digitization workflow shared by **Sweetman Astrophotography**. This project is an independently developed implementation and does not claim endorsement or approval by Sweetman.

Released under the [MIT License](LICENSE).

For installation, the complete seven-click guide, troubleshooting and export details, see the [README](README.md).
