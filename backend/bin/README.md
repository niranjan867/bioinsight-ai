# AutoDock Vina Binaries

BioInsight AI uses the official Scripps AutoDock Vina v1.2.5 engine for high-performance in silico molecular docking.

## Architecture & Paths
The docking engine (`app.bioinformatics.docking.engine`) searches for the Vina executable in the following order:
1. `backend/bin/vina.exe` (Windows)
2. `backend/bin/vina` (Linux / macOS)
3. System `PATH` (`vina` or `vina.exe`)

## Platform Setup (Native, No Docker Required)

### Windows
The official Scripps 64-bit Windows binary (`vina.exe`) is bundled here for turnkey native execution.
- Source: https://github.com/ccsb-scripps/AutoDock-Vina/releases/download/v1.2.5/vina_1.2.5_win.exe

### Linux (Ubuntu / Debian / RHEL)
Download the standalone Scripps Linux binary and set executable permissions:
```bash
curl -L -o backend/bin/vina https://github.com/ccsb-scripps/AutoDock-Vina/releases/download/v1.2.5/vina_1.2.5_linux_x86_64
chmod +x backend/bin/vina
```

### macOS
Install via Homebrew or download from Scripps:
```bash
brew install vina
```
Or place the macOS binary in `backend/bin/vina` and run `chmod +x backend/bin/vina`.
