import os
import sys
import time
import asyncio
import logging
import random
import importlib.util
import platform
import subprocess
import json
from pathlib import Path
from datetime import datetime
from typing import List

from rich import box
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.tree import Tree
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.layout import Layout
from rich.live import Live
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, DownloadColumn, TransferSpeedColumn, TimeRemainingColumn

from main.constants import APP_NAME, APP_VERSION, GITHUB_REPO, RJ_PATTERN, CONFIG_FILE, DB_FILE, TKINTER_AVAILABLE, console, normalize_work_code, get_localized_tag_name
if TKINTER_AVAILABLE:
    import tkinter as tk
    from tkinter import filedialog

from main.models import WorkMetadata, TrackItem, SessionStats
from main.config import ConfigManager
from main.db import LibraryVault
from main.network import NetworkKernel, NetworkDiagnostics
from main.orchestrator import Orchestrator
from main.progress import RichProgressReporter

def get_source_code(meta_raw: dict, fallback: str) -> str:
    """Prefer the original DLsite code, e.g. RJ01304763 or VJ01002074."""
    return str(meta_raw.get('source_id') or fallback).upper()

def get_track_lookup_id(meta_raw: dict, fallback: str) -> str:
    """Tracks are keyed by ASMR.ONE's internal numeric work id."""
    return str(meta_raw.get('id') or fallback)

def get_circle_name(meta_raw: dict) -> str:
    circle = meta_raw.get('circle')
    if isinstance(circle, dict) and circle.get('name'):
        return circle['name']
    return meta_raw.get('name') or 'Unknown'

class Mainframe:
    """Main application controller."""
    def __init__(self):
        self.config = ConfigManager.load()
        self.db = LibraryVault()
        self.console = console
        self.dry_run = False
        self.auto_all = False  # set True by --all flag in main()
        
        if not self.config.output_dir.exists():
            console.print(f"[yellow]Warning: Output directory '{self.config.output_dir}' does not exist and will be created.[/yellow]")
        if 0 < self.config.bandwidth_limit_mbps < 0.1:
            console.print("[yellow]Warning: Bandwidth limit is set extremely low (< 100 KB/s). Downloads may timeout.[/yellow]")
        self.kernel = None
        self.orc = None
    
    def clear(self) -> None:
        """Clear the console."""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def draw_header(self) -> None:
        """Draw application header."""
        cnt, sz = self.db.get_summary()
        
        grid = Table.grid(expand=True)
        grid.add_column(justify="center", ratio=1)
        
        grid.add_row(Text("ASMR.ONE DOWNLOADER", style="bold white on blue", justify="center"))
        grid.add_row(Text("by Takoyune", style="italic cyan", justify="center"))
        grid.add_row(Text("https://github.com/takoyune", style="dim white", justify="center"))
        
        subtitle = f"[green]📚 Library: {cnt} works | 💾 {sz/1024**3:.2f} GB[/green]"
        
        console.print(Panel(
            grid,
            style="blue",
            box=box.HEAVY,
            subtitle=subtitle,
            subtitle_align="right"
        ))
    
    def get_clipboard(self) -> str:
        """Get text from clipboard."""
        if TKINTER_AVAILABLE:
            try:
                root = tk.Tk()
                root.withdraw()
                content = root.clipboard_get()
                root.destroy()
                return content
            except (tk.TclError, AttributeError):
                pass
        return ""
    
    def print_hierarchy(self, meta: WorkMetadata, items: List[TrackItem]) -> None:
        """Prints the file hierarchy tree for a work code to the console."""
        tree = Tree(f"📁 [bold]{meta.title}[/bold] ({meta.rj_id})")
        
        def add_nodes(node_list: List[TrackItem], parent_tree: Tree) -> None:
            for item in node_list:
                if item.type == 'folder':
                    branch = parent_tree.add(f"📁 [bold]{item.title}[/bold]")
                    add_nodes(item.children, branch)
                else:
                    icon = "🎵" if item.type == 'audio' else "📄"
                    parent_tree.add(f"{icon} {item.title} [dim]({item.size/1024/1024:.1f} MB)[/dim]")
                    
        add_nodes(items, tree)
        console.print(tree)

    def build_tree_selector(self, items: List[TrackItem]) -> List[TrackItem]:
        """Interactive tree builder for track selection."""
        tree = Tree("📂 [bold yellow]Root[/bold yellow]")
        selection_map = {}
        index_counter = [1]
        
        def add_nodes(node_list: List[TrackItem], parent_tree: Tree) -> None:
            for item in node_list:
                if item.type == 'folder':
                    branch = parent_tree.add(f"📁 [bold]{item.title}[/bold]")
                    add_nodes(item.children, branch)
                else:
                    idx = index_counter[0]
                    icon = "🎵" if item.type == 'audio' else "📄"
                    
                    status = ""
                    try:
                        try:
                            sz = item.save_path.stat().st_size
                        except FileNotFoundError:
                            sz = 0
                            
                        try:
                            tmp_sz = item.save_path.with_name(item.save_path.name + ".tmp").stat().st_size
                        except FileNotFoundError:
                            tmp_sz = 0
                            
                        if sz == item.size:
                            status = "[green]✅[/green] "
                        elif tmp_sz > 0:
                            status = "[yellow]⏳[/yellow] "
                    except Exception:
                        pass
                        
                    parent_tree.add(
                        f"[bold cyan]{idx}.[/bold cyan] {status}{icon} {item.title} "
                        f"[dim]({item.size/1024/1024:.1f} MB)[/dim]"
                    )
                    selection_map[idx] = item
                    index_counter[0] += 1
        
        add_nodes(items, tree)
        console.print(tree)
        
        console.print("\n[dim]Enter numbers to select (e.g., '1 3-5'). Leave empty for ALL.[/dim]")
        choice = Prompt.ask("Selection", default="").strip()
        
        if not choice:
            def get_all(nodes: List[TrackItem]) -> List[TrackItem]:
                result = []
                for n in nodes:
                    if n.type != 'folder':
                        result.append(n)
                    result.extend(get_all(n.children))
                return result
            return get_all(items)
        
        selected = []
        for part in choice.split():
            try:
                if '-' in part:
                    start_str, end_str = part.split('-', 1)
                    start = int(start_str.strip())
                    end = int(end_str.strip())
                    for i in range(start, end + 1):
                        if i in selection_map:
                            selected.append(selection_map[i])
                else:
                    idx = int(part.strip())
                    if idx in selection_map:
                        selected.append(selection_map[idx])
            except (ValueError, KeyError):
                console.print(f"[red]Invalid selection: {part}[/red]")
        
        return selected
    

    async def _run_job_safe(self, rj_id: str) -> int:
        """Helper to run a job and safely cleanup the event loop resources."""
        self.kernel = NetworkKernel(self.config)
        self.orc = Orchestrator(self.kernel, self.config, self.db)
        try:
            await self.execute_job(rj_id)
            return self.orc.stats.failed
        finally:
            if self.kernel:
                await self.kernel.shutdown()

    async def execute_job(self, rj_id: str) -> int:
        """Execute a download job for a specific work code."""
        work_code = normalize_work_code(rj_id) or rj_id
        self.orc.log_ui(f"Fetching metadata for {work_code}...")
        
        meta_raw = await self.kernel.fetch(f"/api/workInfo/{work_code}")
        if not meta_raw:
            self.orc.log_ui(f"[red]Failed to fetch metadata for {work_code}[/red]")
            return 1

        source_code = get_source_code(meta_raw, work_code)
        track_lookup_id = get_track_lookup_id(meta_raw, work_code)
        
        meta = WorkMetadata(
            rj_id=source_code,
            title=meta_raw.get('title', 'Unknown'),
            circle=get_circle_name(meta_raw),
            cv=[v['name'] for v in meta_raw.get('vas', [])],
            tags=[get_localized_tag_name(t, getattr(self.config, 'tag_language_priority', None)) for t in meta_raw.get('tags', [])],
            price=meta_raw.get('price', 0),
            source_url=meta_raw.get('source_url', ''),
            dl_count=meta_raw.get('dl_count', 0),
            rating=meta_raw.get('rate_average_2dp', 0.0),
            release_date=meta_raw.get('release_date', ''),
            cover_url=meta_raw.get('mainCoverUrl', '')
        )
        
        tracks_raw = await self.kernel.fetch(f"/api/tracks/{track_lookup_id}?v=2")
        if not tracks_raw:
            self.orc.log_ui(f"[red]Failed to fetch tracks for {source_code}[/red]")
            return 1
        
        root_path = self.orc.get_save_path(meta)
        hierarchy = self.orc.parse_hierarchy(tracks_raw, root_path, root_path)

        def flatten(nodes: List[TrackItem]) -> List[TrackItem]:
            """Flatten a hierarchy of TrackItems into a flat list of files."""
            result = []
            for n in nodes:
                if n.type != 'folder':
                    result.append(n)
                result.extend(flatten(n.children))
            return result
        
        selection_file = Path(".cache") / f"{source_code}.json"
        
        targets = None
        if selection_file.exists():
            try:
                with open(selection_file, 'r', encoding='utf-8') as f:
                    saved_paths = set(json.load(f))
                    
                all_tracks = flatten(hierarchy)
                saved_targets = [t for t in all_tracks if str(t.save_path.relative_to(root_path).as_posix()) in saved_paths]
                
                if saved_targets:
                    if len(self.db.queue_get_pending()) > 1 or getattr(self, 'auto_all', False):
                        targets = saved_targets
                    else:
                        self.clear()
                        self.draw_header()
                        console.print(f"[cyan]Found {len(saved_targets)} previously selected files for {source_code}.[/cyan]")
                        choice = Prompt.ask("Resume previous selection? (Press 'n' to change selection)", choices=["y", "n", "Y", "N"], default="y").lower()
                        if choice == 'y':
                            targets = saved_targets
            except Exception:
                pass

        if not targets:
            if len(self.db.queue_get_pending()) > 1 or self.auto_all:
                targets = flatten(hierarchy)
            else:
                self.clear()
                self.draw_header()
                
                info = Table.grid(expand=True)
                info.add_column()
                info.add_column(justify="right")
                info.add_row(f"[bold]{meta.title}[/bold]", f"⭐ {meta.rating}")
                info.add_row(f"{meta.circle}", f"📥 {meta.dl_count}")
                info.add_row(f"💰 {meta.price} JPY")
                info.add_row(f"📅 {meta.release_date}")
                info.add_row(f"🔗 {meta.source_url}", "")
                info.add_row(f"👥 CV: {', '.join(meta.cv) if meta.cv else 'N/A'}", "")
                info.add_row(f"🏷️ Tags: {', '.join(meta.tags) if meta.tags else 'N/A'}", "")
                
                console.print(Panel(info, title=source_code, border_style="green"))
                targets = self.build_tree_selector(hierarchy)
                
                if targets:
                    try:
                        selection_file.parent.mkdir(parents=True, exist_ok=True)
                        rel_paths = [str(t.save_path.relative_to(root_path).as_posix()) for t in targets]
                        with open(selection_file, 'w', encoding='utf-8') as f:
                            json.dump(rel_paths, f)
                    except Exception:
                        pass
        
        if not targets:
            self.orc.log_ui("[yellow]No tracks selected for download[/yellow]")
            return 0
            
        if self.dry_run:
            total_sz = sum(t.size for t in targets)
            console.print(f"\n[bold cyan][DRY RUN] Would download {len(targets)} files ({total_sz/1024/1024:.2f} MB) for {source_code}[/bold cyan]")
            return 0
            
        self.clear()
        self.draw_header()
        
        cover_path = root_path / "cover.jpg"
        if meta.cover_url:
            root_path.mkdir(parents=True, exist_ok=True)
            try:
                async with await self.kernel.stream(meta.cover_url) as resp:
                    if resp.status == 200:
                        data = await resp.read()
                        with open(cover_path, 'wb') as f:
                            f.write(data)
            except Exception:
                cover_path = None
        
        layout = Layout()
        layout.split_column(
            Layout(name="prog", size=10),
            Layout(name="logs", size=5)
        )
        
        prog = Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            "[progress.percentage]{task.percentage:>3.0f}%",
            DownloadColumn(),
            TransferSpeedColumn(),
            TimeRemainingColumn()
        )
        
        def get_curr_size(t: TrackItem) -> int:
            try:
                return t.save_path.stat().st_size
            except FileNotFoundError:
                pass
            try:
                return t.save_path.with_name(t.save_path.name + ".tmp").stat().st_size
            except FileNotFoundError:
                return 0

        total_bytes = sum(t.size for t in targets)
        curr_bytes = sum(get_curr_size(t) for t in targets)
        
        main_task = prog.add_task(
            f"Downloading {source_code}",
            total=total_bytes, 
            completed=curr_bytes
        )
        
        self.orc.stats = SessionStats()
        
        with Live(layout, refresh_per_second=10, console=console):
            layout["prog"].update(Panel(prog, border_style="blue"))
            
            async def updater():
                while not prog.finished:
                    log_text = "\n".join(self.orc.logs[-5:])
                    layout["logs"].update(Panel(log_text, title="Log", border_style="dim"))
                    await asyncio.sleep(0.5)
            
            update_task = asyncio.create_task(updater())
            
            reporter = RichProgressReporter(prog)
            coros = [
                self.orc.download_file(t, meta, reporter, main_task, cover_path) 
                for t in targets
            ]
            await asyncio.gather(*coros)
            
            await asyncio.sleep(1.0)
            update_task.cancel()
        
        def get_final_size(t: TrackItem) -> int:
            try:
                return t.save_path.stat().st_size
            except FileNotFoundError:
                return 0
                
        final_size = sum(get_final_size(t) for t in targets)
        self.db.register(meta, final_size, root_path)
        self.orc.generate_m3u_playlist(root_path, meta)
        
        self.clear()
        self.draw_header()
        
        sum_tab = Table(show_header=True, header_style="bold magenta")
        sum_tab.add_column("Result")
        sum_tab.add_column("Count")
        sum_tab.add_row("Success", str(self.orc.stats.success))
        
        elapsed_sec = time.time() - self.orc.stats.start_time
        speed = (self.orc.stats.bytes_downloaded / 1024**2) / elapsed_sec if elapsed_sec > 0 else 0
        summary_data = [
            ("Failed", self.orc.stats.failed, "red"),
            ("Skipped", self.orc.stats.skipped, "yellow"),
            ("Time Elapsed", f"{elapsed_sec:.1f}s", "cyan"),
            ("Avg Speed", f"{speed:.2f} MB/s", "cyan"),
            ("Total Data", f"{self.orc.stats.bytes_downloaded / 1024**2:.2f} MB", "cyan")
        ]
        
        for label, value, color in summary_data:
            sum_tab.add_row(f"[{color}]{label}[/{color}]", str(value))
        
        console.print(Panel(sum_tab, title="Session Report", border_style="green"))
        console.print(f"📂 Location: [link={root_path}]{root_path}[/link]")
        
        if self.orc.stats.failures:
            fail_tab = Table(show_header=True, header_style="bold red", title="Failed Files")
            fail_tab.add_column("#", style="dim", width=4)
            fail_tab.add_column("File", style="bold")
            fail_tab.add_column("Reason", style="red")
            for i, (filename, reason) in enumerate(self.orc.stats.failures, 1):
                fail_tab.add_row(str(i), filename[:60], reason[:80])
            console.print(fail_tab)
        
        Prompt.ask("[dim]Press Enter to continue...[/dim]", default="")

    def search_online_works(self, keyword: str) -> None:
        """Search ASMR.ONE online catalog for works by keyword/tag and prompt to queue them."""
        import urllib.parse
        async def do_search():
            kernel = self.kernel or NetworkKernel(self.config)
            encoded = urllib.parse.quote(keyword)
            url = f"/api/works?keyword={encoded}&page=1&subtitle=0"
            try:
                res = await kernel.fetch(url)
                if not res or 'works' not in res or not res['works']:
                    return []
                return res['works']
            finally:
                if not self.kernel:
                    await kernel.shutdown()
            
        works = asyncio.run(do_search())
        if not works:
            console.print(f"[yellow]No works found on ASMR.ONE for query: '{keyword}'[/yellow]")
            Prompt.ask("\n[dim]Press Enter to continue...[/dim]", default="")
            return

        table = Table(show_header=True, header_style="bold cyan", title=f"Search Results for '{keyword}'")
        table.add_column("#", justify="right")
        table.add_column("Work Code", style="yellow")
        table.add_column("Title")
        table.add_column("Circle", style="green")
        table.add_column("CV", style="magenta")
        table.add_column("Tags", style="blue")
        table.add_column("Rating", justify="right")

        work_map = {}
        for idx, item in enumerate(works[:15], 1):
            code = str(item.get('source_id') or item.get('id') or '').upper()
            if not code.startswith(('RJ', 'VJ', 'BJ')):
                code = f"RJ{code}"
            title = item.get('title', 'Unknown')[:30]
            circle = get_circle_name(item)[:15]
            cvs = ", ".join([v['name'] for v in item.get('vas', [])]) or "N/A"
            tags = ", ".join([get_localized_tag_name(t, getattr(self.config, 'tag_language_priority', None)) for t in item.get('tags', [])]) or "N/A"
            rating = f"★ {item.get('rate_average_2dp', 0.0):.2f}"
            table.add_row(str(idx), code, title, circle, cvs[:15], tags[:20], rating)
            work_map[str(idx)] = code
            work_map[code.lower()] = code

        console.print(table)
        inp = Prompt.ask("\nEnter numbers to download (e.g. 1 3, or 'all', or Enter to cancel)").strip().lower()
        if not inp:
            return

        selected_codes = []
        if inp == 'all':
            selected_codes = list(work_map.values())
        else:
            for token in inp.split():
                if token in work_map:
                    selected_codes.append(work_map[token])

        if selected_codes:
            for code in list(dict.fromkeys(selected_codes)):
                self.db.queue_add(code)
            console.print(f"[green]Added {len(selected_codes)} work(s) to the queue![/green]")
            time.sleep(1)
            if Confirm.ask("Process queue now?"):
                self.process_queue()
    
    def menu_loop(self) -> None:
        """Main menu loop."""
        while True:
            self.clear()
            self.draw_header()
            
            tips = [
                "💡 Tip: Use 'p' in download prompt to paste from clipboard",
                "💡 Tip: Work codes are usually RJ/VJ plus 6-8 digits",
                "💡 Tip: Try option [3] to search ASMR.ONE by tags ($tag:耳かき)!",
                "💡 Tip: You can batch download multiple work codes at once",
                "💡 Tip: Library search supports partial titles and circles",
            ]
            console.print(f"\n{random.choice(tips)}\n")
            
            console.print("[1] Download (Work Codes)")
            console.print("[2] Batch Download from File")
            console.print("[3] Search ASMR.ONE Online (Tags, CV, Circle)")
            console.print("[4] Library Browser")
            console.print("[5] Queue Manager")
            console.print("[6] Settings")
            console.print("[7] Statistics Dashboard")
            console.print("[8] System Utilities")
            console.print("[red][X] Exit[/red]")
            
            choice = Prompt.ask(
                "\nSelect", 
                choices=["1", "2", "3", "4", "5", "6", "7", "8", "s", "S", "x", "X"], 
                show_choices=False
            ).lower()
            
            if choice == "3" or choice == "s":
                self.clear()
                self.draw_header()
                console.print("[bold cyan]🔍 ASMR.ONE Online Search[/bold cyan]\n")
                console.print("[1] General Keyword / Title Search")
                console.print("[2] Tag Search (e.g., 耳かき, 睡眠, 膝枕)")
                console.print("[3] Voice Actor / CV Search (e.g., 本渡楓)")
                console.print("[4] Circle Search")
                console.print("[5] Custom Syntax Filter ($tag:, $rate:, $duration:)")
                console.print("[B] Back to Main Menu\n")
                
                sub_choice = Prompt.ask("Select search type", choices=["1", "2", "3", "4", "5", "b", "B"], show_choices=False).lower()
                if sub_choice == "1":
                    query = Prompt.ask("Enter keyword or title").strip()
                    if query: self.search_online_works(query)
                elif sub_choice == "2":
                    tag_inp = Prompt.ask("Enter tag(s) (space separated, e.g. Loli Incest 耳かき)").strip()
                    if tag_inp:
                        formatted_query = " ".join(t if t.startswith("$") else f"$tagw:{t}$" for t in tag_inp.split())
                        self.search_online_works(formatted_query)
                elif sub_choice == "3":
                    va_inp = Prompt.ask("Enter Voice Actor / CV name").strip()
                    if va_inp:
                        self.search_online_works(f"$va:{va_inp}")
                elif sub_choice == "4":
                    circle_inp = Prompt.ask("Enter Circle name").strip()
                    if circle_inp:
                        self.search_online_works(f"$circle:{circle_inp}")
                elif sub_choice == "5":
                    custom_inp = Prompt.ask("Enter search query with syntax ($tag:, $rate:, etc.)").strip()
                    if custom_inp:
                        self.search_online_works(custom_inp)
                continue
            elif choice == "1":
                inp = Prompt.ask("Enter Work Codes (space separated)").strip()
                if inp.lower() == 'p':
                    inp = self.get_clipboard()
                
                codes = list(dict.fromkeys(normalize_work_code(m.group("code")) for m in RJ_PATTERN.finditer(inp) if m.group("code")))
                
                if not codes:
                    console.print("[yellow]No valid work codes found[/yellow]")
                    time.sleep(1)
                    continue
                
                final_codes = []
                for code in set(codes):
                    work = self.db.get_work(code)
                    if work:
                        date_str = work['downloaded_at']
                        date = date_str[:10]
                        if not Confirm.ask(f"[yellow]{code} is already in your library (downloaded on {date}).[/yellow] Re-download anyway?"):
                            continue
                    final_codes.append(code)
                
                for code in final_codes:
                    self.db.queue_add(code)
                console.print(f"[green]Added {len(final_codes)} works to the download queue.[/green]")
                
                if Confirm.ask("Process queue now?"):
                    self.process_queue()            
            elif choice == "2":
                file_path = Prompt.ask("\nEnter path to text file containing work codes").strip()
                if not os.path.isfile(file_path):
                    console.print("[red]File not found.[/red]")
                    time.sleep(1)
                    continue
                
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        file_content = f.read()
                    
                    codes = list(dict.fromkeys(normalize_work_code(m.group("code")) for m in RJ_PATTERN.finditer(file_content) if m.group("code")))
                            
                    if not codes:
                        console.print("[yellow]No valid work codes found in the file.[/yellow]")
                        time.sleep(1)
                        continue
                        
                    final_codes = []
                    for code in set(codes):
                        work = self.db.get_work(code)
                        if work:
                            date_str = work['downloaded_at']
                            date = date_str[:10]
                            if not Confirm.ask(f"[yellow]{code} is already in your library (downloaded on {date}).[/yellow] Re-download anyway?"):
                                continue
                        final_codes.append(code)

                    for code in final_codes:
                        self.db.queue_add(code)
                    console.print(f"[green]Successfully loaded {len(final_codes)} work codes into the queue.[/green]")
                    time.sleep(1)
                    
                    if Confirm.ask("Process queue now?"):
                        self.process_queue()
                except Exception as e:
                    console.print(f"[red]Failed to read file: {e}[/red]")
                    time.sleep(1.5)
                    
            elif choice == "4":
                self.clear()
                self.draw_header()
                
                query = Prompt.ask("Search Library (Empty for all)").strip()
                results = self.db.search(query)
                
                if not results:
                    console.print("[yellow]No results found[/yellow]")
                    time.sleep(1)
                    continue
                
                table = Table(show_header=True)
                table.add_column("ID", style="cyan")
                table.add_column("Title", style="white")
                table.add_column("Size", justify="right")
                table.add_column("Date", justify="right")
                
                paths = {}
                for row in results:
                    rj_id = row['rj_id']
                    title = row['title'][:50] + "..." if len(row['title']) > 50 else row['title']
                    size = f"{row['size_bytes'] / 1024**3:.2f} GB" if row['size_bytes'] else "N/A"
                    date_str = row['downloaded_at']
                    date = date_str[:10]
                    
                    table.add_row(str(rj_id), title, size, date)
                    paths[rj_id] = row['local_path']
                
                console.print(table)
                
                selected = normalize_work_code(Prompt.ask("Enter work code to open folder (or Enter to continue)").strip())
                if selected and selected in paths:
                    try:
                        path = Path(paths[selected])
                        if path.exists():
                            if platform.system() == "Windows":
                                os.startfile(path)
                            elif platform.system() == "Darwin":
                                subprocess.run(["open", path])
                            else:
                                subprocess.run(["xdg-open", path])
                        else:
                            console.print(f"[yellow]Path not found: {path}[/yellow]")
                    except Exception as e:
                        console.print(f"[red]Failed to open folder: {e}[/red]")
                
                time.sleep(0.5)
            
            elif choice == "5":
                self.queue_manager_loop()
                
            elif choice == "6":
                audio_langs = ", ".join(getattr(self.config, 'audio_language_priority', ['ja-jp', 'en-us', 'zh-cn']))
                tag_langs = ", ".join(getattr(self.config, 'tag_language_priority', ['ja-jp', 'en-us', 'zh-cn']))
                settings_info = f"""
Directory: {self.config.output_dir}
Concurrent Downloads: {self.config.max_concurrent}
Bandwidth Limit: {self.config.bandwidth_limit_mbps if self.config.bandwidth_limit_mbps > 0 else 'Unlimited'} MB/s
Proxy: {self.config.proxy or 'None'}
Mirror: {self.config.mirror}
Audio Tagging: {'Enabled' if self.config.tag_audio else 'Disabled'}
Auto-Sort: {'Enabled' if self.config.sort_files else 'Disabled'}
Create .M3U Playlist: {'Enabled' if getattr(self.config, 'create_playlist', True) else 'Disabled'}
Audio Language Priority: {audio_langs}
Tag Language Priority: {tag_langs}
Timeout: {self.config.timeout}s
                """.strip()
                
                console.print(Panel(settings_info, title="Settings"))
                
                if Confirm.ask("Edit settings?"):
                    if Confirm.ask("Change download directory?"):
                        if TKINTER_AVAILABLE:
                            root = tk.Tk()
                            root.withdraw()
                            directory = filedialog.askdirectory()
                            root.destroy()
                            if directory:
                                self.config.output_dir = Path(directory)
                        else:
                            new_dir = Prompt.ask("Enter directory path")
                            if new_dir:
                                self.config.output_dir = Path(new_dir)
                    
                    if Confirm.ask("Set proxy?"):
                        proxy_url = Prompt.ask("Proxy URL (e.g., http://proxy:port)", default="")
                        self.config.proxy = proxy_url if proxy_url else None
                    
                    if Confirm.ask(f"Toggle auto-sort (currently: {self.config.sort_files})?"):
                        self.config.sort_files = not self.config.sort_files

                    if Confirm.ask(f"Toggle .M3U Playlist generation (currently: {getattr(self.config, 'create_playlist', True)})?"):
                        self.config.create_playlist = not getattr(self.config, 'create_playlist', True)

                    if Confirm.ask("Edit Audio Language Priority?"):
                        console.print(f"Current Priority: {audio_langs}")
                        new_audio_lang = Prompt.ask("Enter new order (comma separated, e.g. ja-jp, en-us, zh-cn)")
                        if new_audio_lang:
                            self.config.audio_language_priority = [x.strip().lower() for x in new_audio_lang.split(",") if x.strip()]

                    if Confirm.ask("Edit Tag Language Priority?"):
                        console.print(f"Current Priority: {tag_langs}")
                        console.print("Available languages: [bold cyan]ja-jp[/bold cyan] (Japanese), [bold cyan]en-us[/bold cyan] (English), [bold cyan]zh-cn[/bold cyan] (Chinese)")
                        new_lang = Prompt.ask("Enter new order (comma separated, e.g. en-us, ja-jp, zh-cn)")
                        if new_lang:
                            self.config.tag_language_priority = [x.strip().lower() for x in new_lang.split(",") if x.strip()]
                    
                    if Confirm.ask(f"Change concurrent downloads (currently: {self.config.max_concurrent})?"):
                        new_max = IntPrompt.ask("Number (1-10)", default=self.config.max_concurrent)
                        self.config.max_concurrent = max(1, min(10, new_max))
                        
                    if Confirm.ask(f"Change bandwidth limit (currently: {self.config.bandwidth_limit_mbps} MB/s)?"):
                        new_bw = Prompt.ask("Limit in MB/s (0 for unlimited)", default=str(self.config.bandwidth_limit_mbps))
                        try:
                            self.config.bandwidth_limit_mbps = max(0.0, float(new_bw))
                        except ValueError:
                            console.print("[red]Invalid value. Keeping old limit.[/red]")
                            
                    if Confirm.ask("Edit Format Priority list?"):
                        console.print(f"Current Priority: {', '.join(self.config.format_priority)}")
                        new_formats = Prompt.ask("Enter new list (comma separated, e.g. flac,wav,mp3)")
                        if new_formats:
                            self.config.format_priority = [x.strip().lower() for x in new_formats.split(",") if x.strip()]
                            
                    self.config.save()
                    console.print("[green]Settings saved![/green]")

            elif choice == "7":
                self.show_statistics_dashboard()
                
            elif choice == "8":
                self.system_utilities_loop()
            elif choice == "x":
                console.print("\n[bold cyan]Thanks for using ASMR.ONE Downloader![/bold cyan]")
                console.print("[dim]May your downloads be plentiful and your files organized![/dim]")
                time.sleep(1)
                break
    
    def show_statistics_dashboard(self) -> None:
        """Show statistics dashboard."""
        self.clear()
        cnt, sz = self.db.get_summary()
        
        console.print(Panel.fit(
            "[bold cyan]📊 STATISTICS DASHBOARD[/bold cyan]",
            border_style="cyan"
        ))
        
        stats = Table.grid(expand=True)
        stats.add_column()
        stats.add_column(justify="right")
        
        stats.add_row("[cyan]Total Works:[/cyan]", f"[green]{cnt}[/green]")
        stats.add_row("[cyan]Library Size:[/cyan]", f"[green]{sz/1024**3:.2f} GB[/green]")
        stats.add_row("[cyan]Queue Length:[/cyan]", f"[green]{len(self.db.queue_get_pending())}[/green]")
        if cnt > 0:
            avg_size = sz / cnt / 1024**2
            stats.add_row("[cyan]Average Work Size:[/cyan]", f"[green]{avg_size:.1f} MB[/green]")
        
        console.print(Panel(stats, border_style="green"))
        
        Prompt.ask("\n[dim]Press Enter to continue...[/dim]")
    


    def process_queue(self) -> None:
        """Process all pending items in the database queue."""
        self.clear()
        console.print("[bold cyan]▶ Processing Download Queue...[/bold cyan]")
        console.print("Press [yellow]Ctrl+C[/yellow] during a download to safely pause and return to menu.\n")
        
        failed_rjs = []
        
        while True:
            pending = self.db.queue_get_pending()
            if not pending:
                console.print("[green]Queue is empty or all downloads completed.[/green]")
                time.sleep(1.5)
                break
                
            rj = pending[0]['rj_id']
            try:
                self.db.queue_update_status(rj, 'active')
                failed = asyncio.run(self._run_job_safe(rj))
                self.db.queue_remove(rj)
                if failed and failed > 0:
                    failed_rjs.append(rj)
            except KeyboardInterrupt:
                console.print(f"\n[yellow]Download paused for {rj}. State saved to database.[/yellow]")
                self.db.queue_update_status(rj, 'pending')
                if Confirm.ask("\n[yellow]Do you want to clean up in-progress .tmp files for this download?[/yellow]", default=False):
                    cleaned = 0
                    for path in self.config.output_dir.rglob("*.tmp"):
                        if str(rj) in str(path) and path.is_file():
                            path.unlink()
                            cleaned += 1
                    console.print(f"[green]Cleaned up {cleaned} .tmp files.[/green]")
                time.sleep(1.5)
                break
            except Exception as e:
                console.print(f"\n[red]Error processing {rj}: {e}[/red]")
                logging.exception(f"Error processing {rj}: {e}")
                # Remove from queue so it doesn't block future runs as a permanent 'error' row
                self.db.queue_remove(rj)
                failed_rjs.append(rj)
                time.sleep(1.5)
                break
                
        if failed_rjs:
            if Confirm.ask(f"\n[yellow]{len(failed_rjs)} work codes had failed downloads. Retry them now?[/yellow]"):
                for rj in failed_rjs:
                    self.db.queue_add(rj)
                self.process_queue()
                return
                
        if sys.platform == 'win32':
            try:
                import winsound
                winsound.MessageBeep(winsound.MB_OK)
            except Exception:
                pass
                
    def queue_manager_loop(self) -> None:
        """Interactive queue manager."""
        while True:
            self.clear()
            console.print("[bold]📋 Queue Manager[/bold]\n")
            
            items = self.db.queue_get_all()
            if not items:
                console.print("[dim]Queue is empty.[/dim]\n")
            else:
                table = Table(show_header=True, header_style="bold blue")
                table.add_column("Work Code")
                table.add_column("Priority")
                table.add_column("Status")
                table.add_column("Added")
                
                for item in items:
                    status_color = "yellow" if item['status'] == 'pending' else "cyan" if item['status'] == 'active' else "red"
                    table.add_row(
                        str(item['rj_id']),
                        str(item['priority']),
                        f"[{status_color}]{item['status']}[/{status_color}]",
                        item['added_at'][:16]
                    )
                console.print(table)
                
            console.print("\n[1] Add to Queue")
            console.print("[2] Remove from Queue")
            console.print("[3] Change Priority")
            console.print("[4] Start Processing Queue")
            console.print("[5] Clear Queue")
            console.print("[red][B] Back[/red]")
            
            choice = Prompt.ask("\nSelect", choices=["1", "2", "3", "4", "5", "b", "B"], show_choices=False).lower()
            
            if choice == "1":
                inp = Prompt.ask("Enter Work Codes").strip()
                codes = {normalize_work_code(m.group("code")) for m in RJ_PATTERN.finditer(inp) if m.group("code")}
                final_codes = []
                for c in codes:
                    work = self.db.get_work(c)
                    if work:
                        date_str = work['downloaded_at']
                        date = date_str[:10]
                        if not Confirm.ask(f"[yellow]{c} is already in your library (downloaded on {date}).[/yellow] Re-download anyway?"):
                            continue
                    final_codes.append(c)
                for c in final_codes:
                    self.db.queue_add(c)
            elif choice == "2":
                rj = Prompt.ask("Enter Work Code to remove").strip()
                work_code = normalize_work_code(rj)
                if work_code:
                    self.db.queue_remove(work_code)
            elif choice == "3":
                rj = Prompt.ask("Enter Work Code").strip()
                work_code = normalize_work_code(rj)
                if work_code:
                    pri = IntPrompt.ask("Enter priority (higher is downloaded first)", default=1)
                    self.db.queue_update_priority(work_code, pri)
            elif choice == "4":
                self.process_queue()
            elif choice == "5":
                if Confirm.ask("[red]Clear all items from queue?[/red]"):
                    self.db.queue_clear()
            elif choice == "b":
                break
    
    def run_diagnostic(self) -> None:
        """Run system diagnostic."""
        console.print("[bold]🔧 Running System Diagnostic...[/bold]\n")
        
        checks = [
            ("Config File", lambda: CONFIG_FILE.exists()),
            ("Database", lambda: DB_FILE.exists()),
            ("Output Directory", lambda: self.config.output_dir.exists()),
            ("Audio Tagging", lambda: importlib.util.find_spec("mutagen") is not None),
            ("Network Module", lambda: importlib.util.find_spec("aiohttp") is not None),
        ]
        
        all_pass = True
        for check_name, check_func in checks:
            try:
                result = check_func()
                status = "✓" if result else "✗"
                color = "green" if result else "red"
                console.print(f"  [{color}]{status}[/{color}] {check_name}")
                if not result:
                    all_pass = False
                time.sleep(0.2)
            except Exception as e:
                console.print(f"  [red]✗[/red] {check_name} (Error: {e})")
                all_pass = False
        
        if all_pass:
            console.print("\n[green]✓ All systems operational![/green]")
        else:
            console.print("\n[yellow]⚠ Some issues detected. Check logs for details.[/yellow]")

    def system_utilities_loop(self) -> None:
        """Interactive System Utilities."""
        while True:
            self.clear()
            console.print("[bold cyan]🛠️ System Utilities[/bold cyan]\n")
            
            console.print("[1] Run Preflight Diagnostic")
            console.print("[2] Database Repair & Optimize")
            console.print("[3] Cache & Temp File Cleaner")
            console.print("[4] Network Mirror Test")
            console.print("[red][B] Back[/red]")
            
            choice = Prompt.ask("\nSelect", choices=["1", "2", "3", "4", "b", "B"], show_choices=False).lower()
            
            if choice == "1":
                self.run_diagnostic()
                Prompt.ask("\n[dim]Press Enter to continue...[/dim]")
            elif choice == "2":
                console.print("\n[yellow]Running PRAGMA integrity_check and VACUUM...[/yellow]")
                success, msg = self.db.repair_database()
                if success:
                    console.print(f"[green]✓ {msg}[/green]")
                else:
                    console.print(f"[red]✗ {msg}[/red]")
                Prompt.ask("\n[dim]Press Enter to continue...[/dim]")
            elif choice == "3":
                pending = self.db.queue_get_pending()
                active = self.db.conn.execute("SELECT * FROM download_queue WHERE status = 'active'").fetchall()
                if pending or active:
                    console.print("\n[red]⚠ WARNING: You have active or pending downloads in the queue.[/red]")
                    if not Confirm.ask("Cleaning cache will wipe their temporary files and selections. Continue?"):
                        continue
                
                console.print("\n[yellow]Scanning for .tmp and selection files...[/yellow]")
                files_to_delete = []
                bytes_freed = 0
                for path in self.config.output_dir.rglob("*.tmp"):
                    if path.is_file():
                        bytes_freed += path.stat().st_size
                        files_to_delete.append(path)
                cache_dir = Path(".cache")
                if cache_dir.exists():
                    for path in cache_dir.glob("*.json"):
                        if path.is_file():
                            bytes_freed += path.stat().st_size
                            files_to_delete.append(path)
                
                if not files_to_delete:
                    console.print("[green]✓ No cache files found. Everything is clean![/green]")
                else:
                    mb_freed = bytes_freed / 1024 / 1024
                    if Confirm.ask(f"[yellow]Found {len(files_to_delete)} temp files ({mb_freed:.2f} MB). Delete?[/yellow]", default=True):
                        for path in files_to_delete:
                            path.unlink()
                        console.print(f"[green]✓ Deleted {len(files_to_delete)} files.[/green]")
                
                Prompt.ask("\n[dim]Press Enter to continue...[/dim]")
            elif choice == "4":
                console.print("\n[yellow]Pinging all API mirrors...[/yellow]")
                results = asyncio.run(NetworkDiagnostics.get_all_latencies(self.config.proxy, getattr(self.config, 'dns', None)))
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
                Prompt.ask("\n[dim]Press Enter to continue...[/dim]")
            elif choice == "b":
                break
