import sys
import time
import json
import asyncio
import importlib.util
import logging

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

from main.constants import *

# ============================================================================
# SYSTEM PREFLIGHT CHECK
# ============================================================================
def system_preflight_check() -> None:
    """
    Scans the runtime environment for critical dependencies.
    Auto-injects missing modules via pip and reboots the kernel.
    """
    required_packages = ['aiofiles', 'aiohttp', 'rich', 'mutagen', 'aiodns', 'pydantic', 'aiohttp_socks']
    missing = []

    for package in required_packages:
        if importlib.util.find_spec(package) is None:
            missing.append(package)

    if not missing:
        return

    # Fallback raw print for pre-rich environment
    print("\n\033[91m[FATAL] Missing Core Modules Detected.\033[0m")
    print(f"Missing dependencies: {', '.join(missing)}")
    print("Please install them manually by running:")
    print("    pip install " + " ".join(missing))
    print("Or install via requirements.txt if available.")
    sys.exit(1)

# Run preflight check before any imports
system_preflight_check()

from main.app import *

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================
def check_for_updates(config) -> None:
    """Checks the GitHub API for a new release tag."""
    import urllib.request
    
    last_checked = getattr(config, 'last_update_check', 0.0)
    if time.time() - last_checked < 86400:
        return
        
    try:
        url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
        req = urllib.request.Request(url, headers={'User-Agent': 'ASMR-Downloader'})
        with urllib.request.urlopen(req, timeout=3) as response:
            data = json.loads(response.read().decode())
            latest_version = data.get("tag_name", "")
            
            if latest_version:
                # Only save timestamp when we got a real response
                config.last_update_check = time.time()
                config.save()
                if latest_version != APP_VERSION:
                    console.print(f"\n[bold yellow]⚠ UPDATE AVAILABLE: {latest_version} (Current: {APP_VERSION})[/bold yellow]")
                    console.print(f"[cyan]Download at: https://github.com/{GITHUB_REPO}/releases/latest[/cyan]\n")
                    time.sleep(2)
    except Exception:
        pass

def main() -> None:
    """Main entry point."""
    import argparse
    import re
    parser = argparse.ArgumentParser(prog="./asmr", description="ASMR.ONE Downloader")
    parser.add_argument("rj_codes", nargs="*", help="Directly download specific RJ codes (e.g. RJ123456)")
    parser.add_argument("-b", "--batch", help="Path to a text file containing RJ codes (one per line)")
    parser.add_argument("-a", "--all", action="store_true", help="Download all files automatically (bypass selection prompt)")
    parser.add_argument("--list", action="store_true", help="Fetch and print track list for an RJ code without downloading")
    parser.add_argument("--export", metavar="FILE", help="Export the library to a CSV or JSON file (e.g., ./asmr --export library.csv)")
    parser.add_argument("--test", action="store_true", help="Test all API mirrors and display detailed latency and error information")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be downloaded without actually downloading")
    parser.add_argument("--resume", action="store_true", help="Resume pending downloads from queue")
    parser.add_argument("--no-update-check", action="store_true", help="Skip GitHub update check")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose (DEBUG) logging")
    parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {APP_VERSION}", help="Show version information and exit")
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        app = Mainframe()
        app.auto_all = args.all
        app.dry_run = args.dry_run
        
        if args.list:
            if not args.rj_codes:
                console.print("[red]Please provide RJ codes to list (e.g., ./asmr --list RJ123456)[/red]")
                sys.exit(1)
            
            async def list_rj(rj):
                kernel = NetworkKernel(app.config)
                try:
                    meta_raw = await kernel.fetch(f"/api/workInfo/{rj}")
                    tracks_raw = await kernel.fetch(f"/api/tracks/{rj}?v=2")
                    if not meta_raw or not tracks_raw:
                        console.print(f"[red]Failed to fetch info for RJ{rj}[/red]")
                        return
                    
                    orc = Orchestrator(kernel, app.config, app.db)
                    
                    meta = WorkMetadata(
                        rj_id=meta_raw.get('id', rj),
                        title=meta_raw.get('title', 'Unknown'),
                        circle=meta_raw.get('circle', {}).get('name', 'Unknown'),
                        cv=[v['name'] for v in meta_raw.get('vas', [])],
                        tags=[t['name'] for t in meta_raw.get('tags', [])],
                        price=meta_raw.get('price', 0),
                        source_url=meta_raw.get('source_url', ''),
                        dl_count=meta_raw.get('dl_count', 0),
                        rating=meta_raw.get('rate_average_2dp', 0.0),
                        release_date=meta_raw.get('release_date', ''),
                        cover_url=meta_raw.get('mainCoverUrl', '')
                    )
                    root = orc.get_save_path(meta)
                    hierarchy = orc.parse_hierarchy(tracks_raw, root, root)
                    app.print_hierarchy(meta, hierarchy)
                finally:
                    await kernel.shutdown()
            
            for code in args.rj_codes:
                match = RJ_PATTERN.search(code)
                if match:
                    asyncio.run(list_rj(match.group("id")))
            sys.exit(0)
            
        if args.test:
            console.print("\n[yellow]Pinging all API mirrors...[/yellow]")
            from rich.table import Table
            results = asyncio.run(NetworkDiagnostics.get_all_latencies(app.config.proxy, getattr(app.config, 'dns', None)))
            table = Table(show_header=True, header_style="bold blue")
            table.add_column("Mirror")
            table.add_column("Latency", justify="right")
            table.add_column("Status")
            table.add_column("Global (UptimeRobot)", justify="center")
            
            for mirror, latency, err, global_status in results:
                if latency != float('inf'):
                    ms = f"{latency*1000:.0f} ms"
                    status = "[green]Online[/green]"
                else:
                    ms = "Error"
                    status = f"[red]{err}[/red]"
                
                g_status = "-"
                if global_status:
                    if "UP" in global_status:
                        g_status = f"[green]{global_status}[/green]"
                    elif "DOWN" in global_status:
                        g_status = f"[red]{global_status}[/red]"
                    else:
                        g_status = global_status

                table.add_row(mirror, ms, status, g_status)
            console.print(table)
            sys.exit(0)
            
        if args.export:
            export_path = Path(args.export)
            ext = export_path.suffix.lower()
            if ext not in ['.csv', '.json']:
                console.print("[red]Export file must end with .csv or .json[/red]")
                sys.exit(1)
            
            if app.db.export_library(export_path):
                console.print(f"[green]Successfully exported library to {export_path}[/green]")
                sys.exit(0)
            else:
                console.print(f"[red]Failed to export library to {export_path}[/red]")
                sys.exit(1)
            
        if not args.resume and not args.rj_codes and not args.batch and not args.no_update_check:
            check_for_updates(app.config)
        
        if not args.resume:
            fastest_mirror = asyncio.run(NetworkDiagnostics.test_mirrors(app.config.proxy, getattr(app.config, 'dns', None)))
            if not fastest_mirror:
                console.print("\n[bold red][FATAL] All API mirrors are unreachable.[/bold red]")
                console.print("[yellow]Please check your network connection or configure a proxy in config.json.[/yellow]")
                sys.exit(1)
            app.config.mirror = fastest_mirror
            app.config.save()
            time.sleep(1)

        if args.rj_codes or args.batch:
            codes = []
            if args.rj_codes:
                codes.extend(args.rj_codes)
            if args.batch:
                try:
                    with open(args.batch, 'r', encoding='utf-8') as f:
                        codes.extend([line.strip() for line in f if line.strip()])
                except Exception as e:
                    console.print(f"[red]Failed to read batch file: {e}[/red]")
                    sys.exit(1)
            
            added = 0
            for code in set(codes):
                match = RJ_PATTERN.search(code)
                if match:
                    rj = match.group("id")
                    if app.db.get_work(rj):
                        console.print(f"[yellow]Skipping RJ{rj}: Already in library.[/yellow]")
                        continue
                    app.db.queue_add(rj)
                    added += 1
            
            if added > 0 or app.db.queue_get_pending():
                app.process_queue()
            else:
                console.print("[yellow]No valid or new RJ codes found to download.[/yellow]")
                
        elif args.resume:
            app.process_queue()
        else:
            app.menu_loop()
        
    except KeyboardInterrupt:
        console.print("\n\n[yellow]Interrupt received. Shutting down gracefully...[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[red]Fatal error: {e}[/red]")
        logging.critical(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()