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
    parser.add_argument("rj_codes", nargs="*", help="Directly download specific work codes (e.g. RJ123456 or VJ123456)")
    parser.add_argument("-b", "--batch", help="Path to a text file containing work codes (one per line)")
    parser.add_argument("-s", "--search", metavar="KEYWORD", help="Search ASMR.ONE online for works matching keyword")
    parser.add_argument("-o", "--output", metavar="DIR", help="Override output directory for downloads")
    parser.add_argument("--proxy", metavar="URL", help="Specify HTTP or SOCKS5 proxy URL (e.g., http://127.0.0.1:1080)")
    parser.add_argument("-a", "--all", action="store_true", help="Download all files automatically (bypass selection prompt)")
    parser.add_argument("--list", action="store_true", help="Fetch and print track list for a work code without downloading")
    parser.add_argument("--no-playlist", action="store_true", help="Disable automatic .m3u playlist generation")
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
        
        if args.output:
            from pathlib import Path
            app.config.output_dir = Path(args.output)
            
        if args.proxy:
            app.config.proxy = args.proxy

        if args.no_playlist:
            app.config.create_playlist = False
            
        if getattr(app.config, 'dns', None) == "auto":
            fastest_dns = asyncio.run(NetworkDiagnostics.scan_best_dns(app.config.proxy))
            app.config.dns = fastest_dns or ""
            
        if args.search:
            app.search_online_works(args.search)
            sys.exit(0)
        
        if args.list:
            if not args.rj_codes:
                console.print("[red]Please provide work codes to list (e.g., ./asmr --list RJ123456 or VJ123456)[/red]")
                sys.exit(1)
            
            async def list_rj(work_code):
                kernel = NetworkKernel(app.config)
                try:
                    meta_raw = await kernel.fetch(f"/api/workInfo/{work_code}")
                    track_lookup_id = get_track_lookup_id(meta_raw, work_code) if meta_raw else work_code
                    tracks_raw = await kernel.fetch(f"/api/tracks/{track_lookup_id}?v=2")
                    if not meta_raw or not tracks_raw:
                        console.print(f"[red]Failed to fetch info for {work_code}[/red]")
                        return
                    
                    orc = Orchestrator(kernel, app.config, app.db)
                    source_code = get_source_code(meta_raw, work_code)
                    
                    meta = WorkMetadata(
                        rj_id=source_code,
                        title=meta_raw.get('title', 'Unknown'),
                        circle=get_circle_name(meta_raw),
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
                work_code = normalize_work_code(code)
                if work_code:
                    asyncio.run(list_rj(work_code))
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
                from rich.panel import Panel
                msg = (
                    "[bold yellow]ASMR.ONE is actively region-blocked outside of East Asia.[/bold yellow]\n\n"
                    "If you are outside Japan or China, you MUST use a VPN or proxy.\n"
                    "We highly recommend using [bold cyan]Cloudflare WARP[/bold cyan] to bypass this:\n\n"
                    "  1. Download WARP from [u cyan]https://one.one.one.one/[/u cyan]\n"
                    "  2. Open the app settings (gear icon)\n"
                    "  3. Select [bold white]Traffic and DNS (UDP)[/bold white] (not just DNS)\n"
                    "  4. Connect and run this downloader again.\n\n"
                    "[dim]Alternatively, configure a custom proxy in config.json.[/dim]"
                )
                console.print(Panel(msg, title="[bold red]Connection Blocked[/bold red]", border_style="red", expand=False))
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
                work_code = normalize_work_code(code)
                if not work_code:
                    continue
                if app.db.get_work(work_code):
                    console.print(f"[yellow]Skipping {work_code}: Already in library.[/yellow]")
                    continue
                app.db.queue_add(work_code)
                added += 1
            
            if added > 0 or app.db.queue_get_pending():
                app.process_queue()
            else:
                console.print("[yellow]No valid or new work codes found to download.[/yellow]")
                
        elif args.resume:
            app.process_queue()
        else:
            app.menu_loop()
        
    except KeyboardInterrupt:
        console.print("\n\n[yellow]Interrupt received. Shutting down gracefully...[/yellow]")
        sys.exit(0)
    except Exception as e:
        from rich.panel import Panel
        msg = f"[bold red]An unexpected crash occurred:[/bold red]\n{e}\n\n[dim]Please check singularity.log for the full traceback.[/dim]"
        console.print(Panel(msg, title="[bold red]Application Crash[/bold red]", border_style="red", expand=False))
        logging.critical(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
