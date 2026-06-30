# SSP3000 Software Inventory Collector

<div align="center">

![License](https://img.shields.io/badge/License-MIT-blue.svg)
![Python Version](https://img.shields.io/badge/Python-3.7+-green.svg)
![Platform](https://img.shields.io/badge/Platform-Windows-orange.svg)
![Downloads](https://img.shields.io/badge/downloads-beta-yellow.svg)

**Automated Windows software inventory collection with multi-format export**

[Installation](#installation) · [Usage](#usage) · [Features](#features) · [Debugging](#debugging) · [Troubleshooting](#troubleshooting)

</div>

---

## 📋 Overview

SSP3000 is a lightweight Python utility designed to scan your Windows system's registry and compile a complete list of installed software packages. The tool extracts detailed information including version numbers, publishers, installation paths, architecture (32/64-bit), and more — exporting results to LibreOffice Calc (.ods), CSV, or JSON formats.

Built for IT administrators, auditors, and power users who need reliable software asset tracking without commercial overhead.

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| **Registry Scanning** | Reads both HKLM uninstall keys (32-bit & 64-bit applications) |
| **Multi-Format Export** | Outputs to `.ods` (LibreOffice), `.csv`, or `.json` |
| **Rich Metadata** | Captures 15+ fields per package (version, publisher, install path, update URL, etc.) |
| **System Information** | Includes host machine specs, RAM, processor, Python version in report header |
| **CLI Arguments** | Fully configurable via command-line flags |
| **Debug Mode** | Verbose logging for troubleshooting and validation |
| **Summary Statistics** | Publisher breakdowns, architecture distribution analysis |
| **Zero External APIs** | Pure local operation — no network requirements or data sent externally |

### Extracted Fields

Every detected software entry includes:
- `Name` — Display name from registry
- `Version` — Product version number
- `Publisher` — Software vendor/company
- `Architecture` — 32-bit or 64-bit classification
- `Install Path` — Installation directory location
- `Install Date` — Registration-based installation timestamp
- `Product Code` — Windows Installer GUID/product ID
- `Language` — Locale/language setting
- `Update URL` — Link to vendor updates
- `Support Link` — Help/contact documentation URL
- `Estimated Size` — Disk space footprint (KB)
- Plus optional metadata flags (`NoModify`, `NoRepair`)

---

## 🛠️ Requirements

- **Operating System:** Windows 7/8/10/11 (64-bit recommended)
- **Python Version:** 3.7 or higher
- **Permissions:** Administrator rights required for full registry access
- **Dependencies:** Single external library (`odfpy`)

### Install Dependencies

```bash
pip install odfpy
