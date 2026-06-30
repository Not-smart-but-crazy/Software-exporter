import winreg
import platform
from odf.opendocument import OpenDocumentSpreadsheet
from odf.style import Style, TableColumnProperties, TableRowProperties, TextProperties
from odf.table import Table, TableColumn, TableRow, TableCell
from odf.text import P
import argparse
import sys
from datetime import datetime


def get_installed_software(debug_mode=False):
    """Collect all installed software from Windows Registry"""
    
    uninstall_keys = [
        r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
        r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"
    ]

    software_list = []
    total_scanned = 0
    success_count = 0

    for uninstall_key in uninstall_keys:
        try:
            reg_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, uninstall_key, 0, winreg.KEY_READ)
            
            if debug_mode:
                print(f"[DEBUG] Opening key: {uninstall_key}")
            
            num_subkeys = winreg.QueryInfoKey(reg_key)[0]
            
            if debug_mode:
                print(f"[DEBUG] Found {num_subkeys} subkeys in {uninstall_key}")
            
            for i in range(num_subkeys):
                total_scanned += 1
                
                try:
                    sub_key_name = winreg.EnumKey(reg_key, i)
                    
                    if debug_mode:
                        print(f"[DEBUG] Processing [{i+1}/{num_subkeys}]: {sub_key_name[:50]}...")
                    
                    sub_key = winreg.OpenKey(reg_key, sub_key_name, 0, winreg.KEY_READ)
                    
                    software = {}
                    name_found = False
                    
                    # REQUIRED: Try DisplayName first (this IS the software name)
                    try:
                        software["Name"] = winreg.QueryValueEx(sub_key, "DisplayName")[0]
                        name_found = True
                        
                        if debug_mode:
                            print(f"[DEBUG] FOUND NAME: {software['Name']}")
                            
                    except FileNotFoundError:
                        if debug_mode:
                            print(f"[DEBUG] No DisplayName for: {sub_key_name}")
                        continue
                    
                    # Optional fields - collect whatever exists
                    field_mappings = [
                        ("DisplayVersion", "Version"),
                        ("Publisher", "Publisher"),
                        ("Language", "Language"),
                        ("ProductID", "Product Code"),
                        ("InstallLocation", "Install Path"),
                        ("InstallDate", "Install Date"),
                        ("URLUpdateInfo", "Update URL"),
                        ("HelpLink", "Support Link"),
                        ("EstimatedSize", "Estimated Size KB"),
                        ("NoModify", "No Modify"),
                        ("NoRepair", "No Repair")
                    ]
                    
                    for reg_value, output_key in field_mappings:
                        try:
                            value = winreg.QueryValueEx(sub_key, reg_value)[0]
                            software[output_key] = value
                            if debug_mode:
                                print(f"[DEBUG]   + {output_key}: {str(value)[:60]}")
                        except FileNotFoundError:
                            software[output_key] = ""
                    
                    # Architecture detection
                    if "WOW6432Node" in uninstall_key:
                        software["Architecture"] = "32-bit"
                    elif platform.machine().endswith("64"):
                        software["Architecture"] = "64-bit"
                    else:
                        software["Architecture"] = "Unknown"
                    
                    software["Registry Key"] = uninstall_key.split("\\")[-1][:60]
                    
                    if name_found:
                        software_list.append(software)
                        success_count += 1
                        
                    winreg.CloseKey(sub_key)
                    
                except Exception as err:
                    if debug_mode:
                        print(f"[DEBUG] ERROR processing subkey[{i}]: {err}")
                    continue
            
            winreg.CloseKey(reg_key)
            
        except FileNotFoundError:
            print(f"Warning: Key not found: {uninstall_key}", file=sys.stderr)
            continue
        except PermissionError:
            print("[ERROR] Registry permission denied!", file=sys.stderr)
            print("Please run this script as Administrator!", file=sys.stderr)
            return []
        except Exception as err:
            print(f"[ERROR] Unexpected error accessing {uninstall_key}: {err}", file=sys.stderr)
            continue
    
    if debug_mode:
        print(f"\n[DEBUG SUMMARY]")
        print(f"  Total registry entries scanned: {total_scanned}")
        print(f"  Successful extractions: {success_count}")
        print(f"  Failed/duplicate entries skipped: {total_scanned - success_count}")
    
    return software_list


def add_system_metadata(software_list, author_name=""):
    """Add system information header"""
    
    metadata = {
        "__HEADER__": True,
        "SYSTEM_INFO": f"{platform.system()} {platform.release()}",
        "SCANNED_BY": author_name or "Anonymous",
        "SCAN_DATE": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "TOTAL_PACKAGES": str(len(software_list)),
        "MACHINE_NAME": platform.node(),
        "PROCESSOR": platform.processor(),
        "PYTHON_VERSION": platform.python_version()
    }
    
    return [metadata] + software_list


def export_to_ods(data, filename="software-list.ods", name="", debug_mode=False):
    """Export to LibreOffice Calc format"""
    
    doc = OpenDocumentSpreadsheet()
    table = Table(name="Software Inventory")
    
    # Column style
    col_style = Style(name="colwidth", family="table-column")
    col_style.addElement(TableColumnProperties(columnwidth="3cm"))
    doc.styles.addElement(col_style)
    
    # FIXED: Collect ALL columns properly - include "Name"!
    all_columns = set()
    for item in data:
        if not item.get("__HEADER__"):
            for key in item.keys():
                if not key.startswith("_"):
                    all_columns.add(key)
    
    # Create consistent column order (important columns first)
    priority_columns = ["Name", "Version", "Publisher", "Architecture", "Install Path", 
                       "Install Date", "Product Code", "Language", "Update URL"]
    
    columns = []
    for pc in priority_columns:
        if pc in all_columns:
            columns.append(pc)
            all_columns.discard(pc)
    
    # Add remaining columns alphabetically
    columns.extend(sorted(all_columns))
    
    if debug_mode:
        print(f"\n[DEBUG EXPORT] Using {len(columns)} columns:")
        for col in columns:
            print(f"  - {col}")
    
    # Add column definitions
    for _ in columns:
        table.addElement(TableColumn(stylename=col_style))
    
    # Title row
    title_row = TableRow()
    title_cell = TableCell(numbercolumnsrepeated=len(columns))
    title_text = f"Software Inventory Report - {datetime.now().date()}"
    if name:
        title_text += f" | Author: {name}"
    title_cell.addElement(P(text=title_text))
    title_row.addElement(title_cell)
    table.addElement(title_row)
    
    # Header row
    header_row = TableRow()
    for col in columns:
        cell = TableCell()
        formatted_name = col.replace("_", " ").title()
        cell.addElement(P(text=formatted_name[:80]))
        header_row.addElement(cell)
    table.addElement(header_row)
    
    # Data rows
    software_count = 0
    for item in data:
        if item.get("__HEADER__"):
            # Put header info in special row format
            continue
        
        software_count += 1
        data_row = TableRow()
        
        for col in columns:
            cell = TableCell()
            value = str(item.get(col, ""))
            
            if len(value) > 400:
                value = value[:397] + "..."
            
            cell.addElement(P(text=value))
            data_row.addElement(cell)
        
        table.addElement(data_row)
    
    doc.spreadsheet.addElement(table)
    doc.save(filename)
    
    print(f"\n[SUCCESS] Export complete!")
    print(f"  Software packages written: {software_count}")
    print(f"  Output file: {filename}")
    
    if debug_mode:
        print(f"\n[DEBUG COLUMN CHECK]")
        print(f"  First 3 sample Names from exported data:")
        count = 0
        for item in data[:3]:
            if not item.get("__HEADER__"):
                nm = item.get("Name", "MISSING!")
                print(f"    {count+1}. {nm}")
                count += 1


def main():
    """Main entry point with CLI arguments"""
    
    parser = argparse.ArgumentParser(
        description="SSP3000 Software Scanner - Collect Windows installed software",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python SSP3000-libreoffice.py                      Basic scan
  python SSP3000-libreoffice.py --author "Your Name" Include your name
  python SSP3000-libreoffice.py -v                   Verbose debug mode
  python SSP3000-libreoffice.py -o report.ods        Custom output file
        """
    )
    
    parser.add_argument("--author", "-a", type=str, default="",
                       help="Your name to include in report")
    parser.add_argument("--output", "-o", default=None,
                       help="Custom output filename")
    parser.add_argument("--debug", "-v", action="store_true",
                       help="Enable verbose/debug output")
    parser.add_argument("--summary", "-s", action="store_true",
                       help="Show summary only, no export")
    parser.add_argument("--list-names", action="store_true",
                       help="Just list software names (no export)")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("  SSP3000 Software Inventory Collector v2.2")
    print("=" * 60)
    
    # Get software list
    programs = get_installed_software(debug_mode=args.debug)
    
    if not programs:
        print("\n[CRITICAL ERROR] No software found!")
        print("Possible causes:")
        print("  1. Not running as Administrator? Right-click Command Prompt > 'Run as Admin'")
        print("  2. Registry access blocked by group policy?")
        print("  3. Clean Windows installation with very few packages?")
        sys.exit(1)
    
    # Quick summary regardless of debug mode
    print(f"\n[FINDINGS] Discovered {len(programs)} software packages\n")
    
    if args.list_names:
        print("-" * 60)
        print("SOFTWARE NAMES ONLY:")
        print("-" * 60)
        for prog in sorted(programs, key=lambda x: x.get("Name", "")):
            ver = prog.get("Version", "unknown")
            pub = prog.get("Publisher", "unknown")
            print(f"  {prog['Name']:<50} ({ver})")
        sys.exit(0)
    
    if args.summary:
        print("\nSUMMARY STATISTICS:")
        publishers = {}
        architectures = {"32-bit": 0, "64-bit": 0, "Unknown": 0}
        
        for p in programs:
            pub = p.get("Publisher", "Unknown") or "Unknown"
            publishers[pub] = publishers.get(pub, 0) + 1
            arch = p.get("Architecture", "Unknown") or "Unknown"
            architectures[arch] = architectures.get(arch, 0) + 1
        
        print(f"  Unique publishers: {len(publishers)}")
        print(f"  Top 5 publishers:")
        top_pubs = sorted(publishers.items(), key=lambda x: x[1], reverse=True)[:5]
        for pub, count in top_pubs:
            pct = (count / len(programs)) * 100
            print(f"    • {pub}: {count} ({pct:.1f}%)")
        
        print(f"  Architecture breakdown:")
        for arch, count in architectures.items():
            if count > 0:
                print(f"    • {arch}: {count}")
        
        if args.output:
            full_data = add_system_metadata(programs, args.author)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = args.output or f"software_summary_{timestamp}.ods"
            export_to_ods(full_data, filename, args.author, debug_mode=args.debug)
        sys.exit(0)
    
    # Full export
    full_data = add_system_metadata(programs, args.author)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = args.output or f"software_inventory_{timestamp}.ods"
    
    export_to_ods(full_data, filename, args.author, debug_mode=args.debug)
    
    # Final summary
    print("\n" + "=" * 60)
    print("  SCAN COMPLETE")
    print("=" * 60)
    print(f"  Total packages: {len(programs)}")
    print(f"  Output saved to: {filename}")
    if args.author:
        print(f"  Recorded author: {args.author}")
    print("")


if __name__ == "__main__":
    main()
