# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# Working rules

- Plan in the main session, together with me. Hand grunt work (board searches, repetitive edits, boilerplate, log digging) to subagents on lesser models: Sonnet for searches, triage, and trivial mechanical work, and Opus for writing code. Keep decisions, architecture, and final review in the main session.
- Always look for the simplest solution first, and prefer it. The smallest change that solves the actual problem beats a bigger design. Extend existing patterns before inventing new ones. No new dependencies or moving parts without a real reason.
- Show me a checklist while you work (use the todo list tool), keep it current, so I can see what you are working on, what is done, and what is next.
- When you spawn a subagent, tell me at that moment: which model it runs on and what it is doing. Report what it came back with when it finishes.
- Never use Haiku.
- Comments: never multi-line. Omit the comment entirely when the code is obvious; otherwise one short line. Explain a fix in the commit message and the review/roadmap docs, not in the source. Docstrings are exempt (long explanatory docstrings are house style) but keep new ones tight.
- No over-explaining: deliver the exact output requested. Do not narrate internal steps or show reasoning chains. Do not use programming jargon.
- Strict scope control: stop when the requested task is complete. Do not expand, refactor unrequested areas, or suggest extra features.
- Commit only when I ask.

## What this repo is

`Atomize_NIOCH_Q` is the **Q-band** endstation variant of [Atomize](https://github.com/Anatoly1010/Atomize) — a modular instrument-control framework for spectrometers. Like the other endstation forks it adds an "EPR Endstation Control" tab to the main window (`atomize/main/main.py:382`) and a set of control-center subprocesses.

Python is the scripting language. Experimental scripts are ordinary Python files that import device-module classes and call `general` functions to push data to the LivePlot-based GUI.

### The hardware this fork actually drives

This is the single most important thing to keep straight, because the device_modules directory is inherited whole from upstream and lists far more hardware than exists here. The Q-band endstation is:

| Role | Module | Notes |
|---|---|---|
| Pulser | `PB_Micran` | Micran FMC board on `/dev/devfmc`, driven by raw `fcntl.ioctl` (`PB_Micran.py:2008`) — **not** libspinapi, despite the `to_spinapi` variable names |
| AWG | `Spectrum_M4I_6631_X8` | `/dev/spcm0`; needs the vendor `pyspcm`/`spcm_tools` on `sys.path` |
| Digitizer | `Keysight_3000_Xseries` | an oscilloscope, not a digitizer card — point/post-trigger based, no decimation control |
| MW bridge | `Micran_Q_band_MW_bridge` | |
| Field | `ITC_FC`, `BH_15` | |
| Temperature | `Lakeshore_335` | |

**`Insys_FPGA.py` is inherited and unused here.** Its `libs/exam_adc.ini` is not even shipped, so instantiating it fails. Every mention of "Insys" under `atomize/control_center/` is a *comment* explaining where a rule came from — the Insys-specific behaviour (decimation, `pulser_redefine_delta_start`, MW pulses following the pulser gates) does **not** apply on this fork. Do not port Insys code paths in.

### Device permissions (no sudo needed, with one exception)

Both PCI cards are opened by unprivileged udev rules, verified by actually opening them as `qband`:

- `/dev/spcm0` — mode 0666 via `/etc/udev/rules.d/99-spcm4.rules` (Spectrum AWG).
- `/dev/devfmc` — mode 0777 via `/etc/udev/rules.d/99-devfmc.rules` (the pulser board).

So the GUI never needs root. `libspinapi.so` would need `iopl()` (root), but only `PB_ESR_500_pro` and `Insys_FPGA` use it and neither runs on this fork.

The exception is the **serial instruments**: `/dev/ttyACM0` (`ITC_FC` field controller, `BH_15`, `ECC_15K`, `ER_031M`) and `/dev/ttyUSB0` (`Lakeshore_335`) are `root:dialout` mode 0660. The account must be in `dialout` (`sudo usermod -aG dialout <user>`, then log out and back in) — otherwise every field and temperature call fails with `PermissionError [Errno 13]` while the AWG and pulser work fine, which is a confusing way to find out.

The MW bridge (`tcp-ip`) and the Keysight scope (`ethernet`, config file `Keysight_3034t_config.ini`) are network devices and need no local permissions.

The `_insys` and other siblings under `atomize/control_center/other_versions/` target other endstations; the live files are the ones directly in `atomize/control_center/`.

## Two machines

Development happens on the maintainer's Linux box, against this checkout. Anything that touches the Spectrum card, the PulseBlaster or the Keysight scope can only run for real on the **spectrometer box**; everywhere else use test mode (below).

### The spectrometer box

`qband@192.168.2.1`, Ubuntu 22.04, Python 3.10.12, reachable by SSH key.

**The kernel is frozen at 6.5.0-14-generic** because the Spectrum `spcm4` kernel module is built against it. These packages are `apt-mark hold`ed: `linux-generic-hwe-22.04`, `linux-image-generic-hwe-22.04`, `linux-headers-generic-hwe-22.04`, `linux-image-6.5.0-14-generic`, `linux-headers-6.5.0-14-generic`, `linux-hwe-6.5-headers-6.5.0-14`. **Never run `apt upgrade` there** — install named packages only.

The install is an isolated venv that coexists with an older, unrelated Atomize checkout in `~/Atomize`:

- repo `~/Atomize_NIOCH_Q`, venv `~/Atomize_NIOCH_Q/.venv` (no system site-packages)
- launched by the alias `atomize-q`, i.e. `~/Atomize_NIOCH_Q/.venv/bin/atomize-nioch-q`
- configs in `~/.config/atomize-nioch-q/`

Isolation holds because a venv sets `ENABLE_USER_SITE = False`, hiding the old install's `~/.local` egg-link, and because the config app name `atomize-nioch-q` is one the old install never uses. Don't break either property.

## Common commands

Install (`pip install -e .`), the optional extras and the `atomize-nioch-q` entry point are defined in `pyproject.toml` — read it rather than trusting a copy here. The invocations that are NOT guessable from the manifest:

```bash
python3 -m atomize path/to/script.py    # launch the GUI and open a script in it
python3 path/to/script.py test          # smoke-test one script, no GUI (see "Test mode")
```

There is no unit-test suite; the project's pre-flight check is **test mode**.

**`atomize/tests/pulse_epr/` is stale — do not trust it as a reference.** Those scripts were inherited from an X-band endstation: they import `PB_ESR_500_pro`, `Spectrum_M4I_4450_X8`, `SR_PTC_10` and the pre-rename `Mikran_*` spelling of the MW-bridge modules (the modules are now `Micran_*`). Almost none of them pass test mode. The working reference for this fork is the control-center code and the presets under `atomize/control_center/experiments/`.

## Big-picture architecture

### Multi-process model

The GUI is **one Qt process that spawns many `QProcess` children**, not a monolithic event loop:

- `atomize/main/main.py:MainExtended` extends the upstream `MainWindow` with a third tab. Each control-center button (`start_rect_phasing`, `start_awg_phasing`, `start_sequence_calculator`, `start_excitation_profile`, `start_tune_preset`, `start_mw_control`, `start_treatment_control`, `start_treatment_2d_control`, `start_deer_analysis`, `start_spin_sim`, `start_field_control`, `start_cw_control`, `start_tr_control`, `start_temp_control`, `start_osc_control`) launches a script under `atomize/control_center/` via its own `QProcess`.
- `start_experiment` spawns the user's experimental script in `self.process_python`.
- Children communicate **upward** by writing `print "..."` to stdout; the parent's `handle_output*` parses lines prefixed with `print `, `before `, `closing ` or `ret = 0` and routes them to the in-app log.
- The parent communicates **downward** by writing to the child's stdin when the child prints `create_file_dialog` / `open_file_dialog` — this is how scripts trigger native file pickers.

Every `general.message(...)` call becomes a `print` over a pipe — don't replace it with a normal `print` or the routing logic will eat it.

### LivePlot data path

Plotting is a second IPC layer parallel to stdout:

- The main window starts a `QLocalServer` named `LivePlot` (`atomize/main/main_window.py`).
- Each child script imports `atomize.general_modules.general_functions`, which instantiates a `LivePlotClient` (`atomize/main/client.py`). The client connects to the local socket, allocates a `QSharedMemory` block, and sends NumPy payloads via shared memory plus a JSON metadata header over the socket.
- The main window's `accept` / `read_from` callbacks attach to the same shared memory and forward to the pyqtgraph DockArea.

This is why `general.plot_1d(...)` only works from a script launched **through** the main window — otherwise `LivePlotClient` raises `EnvironmentError("Couldn't find LivePlotter instance")`.

`client.py` and `main_window.py` are two halves of one protocol and must ship together.

### Device module convention

Every device gets a parallel pair:

- `atomize/device_modules/<Device>.py` — class named the same as the file (`import atomize.device_modules.Lakeshore_335 as ls; ls335 = ls.Lakeshore_335()`).
- `atomize/device_modules/config/<Device>_config.ini` — sectioned config (`DEFAULT`, `GPIB`, `SERIAL`, `MODBUS`, `ETHERNET`, `SPECIFIC`). `DEFAULT.type` (`gpib` / `rs232` / `ethernet` / `modbus`) picks the section used at connect time.

`config/config_utils.py` holds the shared `read_conf_util` / `read_specific_parameters` helpers. Transports: pyvisa, pyserial, minimalmodbus, raw sockets, and **ctypes** for vendor binaries (`libspinapi.so` in-repo, `libspcm_linux.so` from the system).

When adding a device, model it on an existing one of the same transport class and add its config file. The class name **must** match the module filename.

### Test mode (the pre-flight check)

Test mode is toggled by the first CLI argument. `general_functions.py` reads `test_flag = sys.argv[1]` at import; `is_test()` is `test_flag == 'test'`. Device modules do the same in `__init__`. The GUI's `Test Scripts` checkbox re-launches the script with `argv[1] == 'test'`.

It is **more than a syntax/import check**:

- **No real I/O.** Every device function guards hardware access with `if self.test_flag != 'test':` and returns canned values in the `elif self.test_flag == 'test':` branch, so a script runs end-to-end with no board attached.
- **Argument validation.** Those same branches range- and type-check their arguments and raise on bad input, surfacing illegal pulse lengths, out-of-range settings and sequence-overlap asserts before they reach hardware. This is why the phasing tools spin up a *throwaway* test-mode pulser to validate a live edit.
- **Message / plot twins.** `message_test`, `plot_1d_test`, `plot_2d_test` fire **only** in test mode; the plain versions only in a real run.

When adding hardware-touching code, always preserve the `argv[1] == 'test'` branch.

### Config-file lifecycle (important gotcha)

`atomize/main/local_config.py:copy_config` runs on every startup under the app name **`atomize-nioch-q`** and copies:
- `atomize/config.ini` → `<user_config_dir>/atomize-nioch-q/main_config.ini`
- `atomize/device_modules/config/*` → `<user_config_dir>/atomize-nioch-q/device_config/`

…but **only if** that directory is missing or empty. After first launch, device modules read the user-config copy (via `lconf.load_config_device()`), not the repo copy. Editing `atomize/device_modules/config/Foo_config.ini` in-repo will **not** affect a running install; edit the copy under `~/.config/atomize-nioch-q/device_config/`, or wipe the directory to force a re-copy.

**Two values must be re-patched after any re-copy**, because the repo ships another machine's paths:
- `Spectrum_M4I_*_config.ini` → `header_dir = /home/qband/Sources/AWG/Examples/python` (the vendor `pyspcm.py` / `spcm_tools.py`; `Spectrum_M4I_6631_X8.py` appends it to `sys.path` at import). The repo ships `/home/fel/sources/...`.
- `main_config.ini` → `script_dir` must point inside this repo, not the old `~/Atomize` checkout.

`atomize/main/main_window.py` also `os.chdir`'s into `libs/` early in startup, so relative paths after that resolve against `libs/`. The `libs/status` and `*.param` files are runtime IPC between control-center widgets and other processes — git-ignored and intentionally mutated at runtime.

### Pulse-EPR experiment presets

`atomize/control_center/experiments/*.phase` (RECT, 9 presets) and `*.phase_awg` (AWG, 13 presets) are saved phase-cycle/pulse-sequence presets consumed by `phasing.py`, `awg_phasing.py`, `sequence_calculator.py` and `tune_preset.py`.

**Live edit.** Both phasing tools can re-arm a *running* sequence without restarting. Editing a pulse parameter with "Live mode" on pushes the change to the acquisition worker after a debounced "Apply delay". Supporting pieces:

- A **Settings tab** holds the Live/Apply-delay controls and a "Link Parameter" combo; **Link mode** gives each pulse a No/0.5×/1×/2× coupling factor so one edit proportionally shifts the linked pulses together.
- Not every change can be applied in place: a change to the phase-cycle *structure* (number of steps, per-pulse phase text) forces an announced restart. The tool hashes the sequence structure to decide. Loading a preset or pressing Open while a preview is live stops that preview first.
- **Worker-side validation.** Before accepting a live edit the worker rebuilds the sequence under a throwaway **test-mode** pulser so the overlap/length asserts reject an illegal edit as `('LiveReject', reason)`; the GUI shows the reason and keeps the previous sequence running.

### General script-side API

Experimental scripts almost always start with:

```python
import atomize.general_modules.general_functions as general
import atomize.general_modules.csv_opener_saver as openfile
```

- `general.message(...)` / `general.message_test(...)` — print to the main-window log (non-test / test-only respectively).
- `general.wait('10 ms')` — string-with-unit time API used everywhere (`ks/s/ms/us/ns/ps`). Time arguments to device functions follow the same convention.
- `general.plot_1d`, `general.plot_2d` — push to LivePlot.
- `general.to_infinity()` — generator for `Stop`-button-aware infinite loops.
- `general.bot_message(...)` — Telegram (needs token + chat-id in `main_config.ini`).
- `atomize.general_modules.returned_thread.rThread` — `threading.Thread` subclass whose `join()` returns the target's return value; the project's standard concurrency primitive.
- `openfile.Saver_Opener()` — CSV/HDF5 I/O with header support and file dialogs.

## Fork family and sync rule

This repo is one of five Atomize variants sharing the same `atomize/` framework. Run the fork-sync checker **first** whenever porting anything: `~/atomize_sync/sync_check.py`.

Direction of truth:
- `device_modules/` and the math cores: plain `Atomize` is the **lead**, changes flow plain → fork.
- `control_center/`, GUI and scripts: developed in the forks, flow fork → plain.
- Shared EPR control-centre tools (`data_treatment*.py`, `deer_analysis.py`, `excitation_profile.py`, `spin_dynamics_sim.py`, `sequence_calculator.py`, …): **ITC is the lead**, mirrored fork → fork with `--sync-cc`.

Watch line endings when porting — some files in the family are CRLF, not LF.

## Documentation

The per-instrument function reference lives in `atomize/documentation/`. The rendered docs site is a separate repo (MkDocs Material) at `/home/anatoly/atomize_docs`, not in-tree. When changing a device module's public API, also touch the matching `*.md`.
