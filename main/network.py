import time
import json
import urllib.request
import random
import asyncio
import logging
from typing import Optional, Tuple, List
import aiohttp
from aiohttp import ClientTimeout

from main.constants import USER_AGENTS, HOSTNAME_MIRRORS, console
from main.config import ConfigManager

class NetworkKernel:
    """Handles network operations and API communication."""
    def __init__(self, config: ConfigManager):
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        self._last_req = 0
        self._rate_limit_lock = asyncio.Lock()

    async def boot(self) -> None:
        """Initialize HTTP session."""
        if self.session is None or self.session.closed:
            headers = {
                "User-Agent": random.choice(USER_AGENTS),
                "Referer": "https://asmr.one/",
                "Origin": "https://asmr.one"
            }
            
            timeout = ClientTimeout(
                total=None, 
                connect=self.config.timeout, 
                sock_read=self.config.timeout
            )
            
            connector = None
            if self.config.proxy and self.config.proxy.startswith("socks"):
                from aiohttp_socks import ProxyConnector
                connector = ProxyConnector.from_url(self.config.proxy)
            elif getattr(self.config, 'dns', None):
                dns_ip = self.config.dns
                if dns_ip.lower() == "auto":
                    fastest_dns = await NetworkDiagnostics.scan_best_dns(self.config.proxy)
                    if fastest_dns:
                        dns_ip = fastest_dns
                        self.config.dns = fastest_dns # Save it for the session
                    else:
                        dns_ip = None # fallback to threaded resolver if scan fails
                        
                if dns_ip and dns_ip.lower() != "auto":
                    from aiohttp.resolver import AsyncResolver
                    resolver = AsyncResolver(nameservers=[dns_ip])
                    connector = aiohttp.TCPConnector(resolver=resolver)
                else:
                    from aiohttp.resolver import ThreadedResolver
                    connector = aiohttp.TCPConnector(resolver=ThreadedResolver())
            else:
                # Always use ThreadedResolver (system DNS via socket API).
                # This is critical on Windows with VPNs: aiodns (the aiohttp
                # default) queries DNS directly and bypasses the VPN tunnel,
                # causing timeouts. ThreadedResolver calls getaddrinfo() which
                # respects the OS routing table and VPN adapter.
                from aiohttp.resolver import ThreadedResolver
                connector = aiohttp.TCPConnector(resolver=ThreadedResolver())
                
            self.session = aiohttp.ClientSession(
                headers=headers, 
                timeout=timeout,
                connector=connector
            )

    async def shutdown(self) -> None:
        """Close HTTP session."""
        if self.session and not self.session.closed:
            await self.session.close()

    async def fetch(self, endpoint: str, params: dict = None) -> Optional[dict]:
        """Fetch JSON data from API endpoint."""
        await self.boot()
        
        # Rate limiting: 0.5s between requests
        async with self._rate_limit_lock:
            now = time.time()
            elapsed = now - self._last_req
            if elapsed < 0.5:
                await asyncio.sleep(0.5 - elapsed)
            self._last_req = time.time()

        url = f"{self.config.mirror}{endpoint}"
        proxy = self.config.proxy if self.config.proxy and not self.config.proxy.startswith("socks") else None

        for attempt in range(3):
            try:
                async with self.session.get(url, params=params, proxy=proxy) as resp:
                    if resp.status == 429:  # Rate limit
                        await asyncio.sleep(2 ** (attempt + 2))
                        continue
                    if resp.status == 404:
                        return None
                    resp.raise_for_status()
                    return await resp.json()
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                logging.warning(f"API request failed on attempt {attempt + 1}/3 for {url}: {e}")
                if attempt == 2:
                    logging.exception(f"API request finally failed for {url}")
                await asyncio.sleep(1)
            except Exception as e:
                logging.exception(f"Unexpected error during fetch for {url}")
                return None
        return None

    async def stream(self, url, headers: dict = None) -> aiohttp.ClientResponse:
        """Stream a file download."""
        await self.boot()
        proxy = self.config.proxy if self.config.proxy and not self.config.proxy.startswith("socks") else None
        
        import yarl
        if isinstance(url, yarl.URL):
            cdn_url = url
            url_str = str(url)
        else:
            url_str = str(url)
            cdn_url = yarl.URL(url_str)
        
        # If the URL points to the CDN (not the API mirror), download directly.
        # The mirror-rotation logic is only for API endpoints; CDN hostnames are
        # different servers and should never have their host swapped.
        api_hosts = {yarl.URL(m).host for m in HOSTNAME_MIRRORS}
        if cdn_url.host not in api_hosts:
            try:
                resp = await self.session.get(cdn_url, headers=headers, proxy=proxy)
                return resp
            except Exception as e:
                logging.error(f"CDN stream failed for {url_str}: {e}")
                raise
        
        # For API-hosted files, try all mirrors in order
        mirrors = [self.config.mirror] + [m for m in HOSTNAME_MIRRORS if m != self.config.mirror]
        last_exc = None
        for mirror in mirrors:
            mirror_url = yarl.URL(mirror)
            current_url = cdn_url.with_scheme(mirror_url.scheme).with_host(mirror_url.host)
            if mirror_url.port:
                current_url = current_url.with_port(mirror_url.port)
                
            try:
                resp = await self.session.get(current_url, headers=headers, proxy=proxy)
                if resp.status in (500, 502, 503, 504):
                    resp.close()
                    continue
                return resp
            except Exception as e:
                logging.warning(f"Mirror {mirror} failed for stream: {e}")
                last_exc = e
                
        logging.error(f"All mirrors failed for stream {url_str}")
        if last_exc:
            raise last_exc
        raise Exception(f"All mirrors failed to stream {url_str}")


class NetworkDiagnostics:
    """Handles network diagnostic tests like latency and uptimerobot checks."""

    @staticmethod
    async def scan_best_dns(proxy: Optional[str] = None) -> Optional[str]:
        """Fetch Japanese public DNS servers and test for the fastest one."""
        console.print("[cyan]Fetching public Japan DNS list...[/cyan]")
        url = "https://public-dns.info/nameserver/jp.json"
        
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            loop = asyncio.get_event_loop()
            def fetch():
                with urllib.request.urlopen(req, timeout=10) as r:
                    return json.loads(r.read().decode("utf-8"))
            data = await loop.run_in_executor(None, fetch)
        except Exception as e:
            console.print(f"[red]Failed to fetch DNS list: {e}[/red]")
            return None

        # Filter for high reliability and take a random sample of 30 to test
        reliable = [d["ip"] for d in data if d.get("reliability", 0) >= 0.9]
        if not reliable:
            return None
            
        candidates = random.sample(reliable, min(30, len(reliable)))
        console.print(f"[cyan]Testing {len(candidates)} reliable DNS servers...[/cyan]")
        
        async def ping_dns(ip: str) -> Tuple[str, float]:
            start = time.time()
            try:
                from aiohttp.resolver import AsyncResolver
                resolver = AsyncResolver(nameservers=[ip])
                connector = aiohttp.TCPConnector(resolver=resolver)
                
                async with aiohttp.ClientSession(connector=connector) as session:
                    p = proxy if proxy and not proxy.startswith("socks") else None
                    # We just need to check if it resolves and connects quickly
                    # using the fastest API mirror endpoint (asmr-200.com)
                    async with session.head("https://api.asmr-200.com/api/tracks/01568205", proxy=p, timeout=5) as resp:
                        resp.raise_for_status()
                        return ip, time.time() - start
            except Exception:
                return ip, float('inf')

        results = await asyncio.gather(*[ping_dns(ip) for ip in candidates])
        valid = [(ip, t) for ip, t in results if t != float('inf')]
        
        if not valid:
            console.print("[red]All scanned DNS servers failed.[/red]")
            return None
            
        valid.sort(key=lambda x: x[1])
        fastest_ip = valid[0][0]
        console.print(f"[green]Selected fastest DNS: {fastest_ip} ({valid[0][1]*1000:.0f}ms)[/green]")
        await asyncio.sleep(0.250)  # Allow aiohttp to clean up pycares tasks
        return fastest_ip

    @staticmethod
    async def test_mirrors(proxy: Optional[str], dns: Optional[str] = None) -> Optional[str]:
        """Test all mirrors concurrently and return the fastest one."""
        console.print("[cyan]Testing API mirrors...[/cyan]")
        results = await NetworkDiagnostics.get_all_latencies(proxy, dns)
        valid = [r for r in results if r[1] != float('inf')]
        if not valid:
            return None
        fastest = valid[0]
        console.print(f"[green]Selected fastest mirror: {fastest[0]} ({fastest[1]*1000:.0f}ms)[/green]")
        await asyncio.sleep(0.250)
        return fastest[0]

    @staticmethod
    async def get_uptimerobot_status(mirror: str, session: aiohttp.ClientSession) -> Optional[str]:
        keys = {
            "https://api.asmr-200.com": "m803458103-44bace29afaebe480d5aa7bf"
        }
        key = keys.get(mirror)
        if not key:
            return None
            
        try:
            url = "https://api.uptimerobot.com/v2/getMonitors"
            payload = f"api_key={key}&format=json"
            headers = {
                "Cache-Control": "no-cache",
                "Content-Type": "application/x-www-form-urlencoded"
            }
            async with session.post(url, data=payload, headers=headers, timeout=5) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get("stat") == "ok" and data.get("monitors"):
                        status_code = data["monitors"][0].get("status")
                        if status_code == 2:
                            return "UP"
                        elif status_code in (8, 9):
                            return "DOWN"
                        else:
                            return f"Status {status_code}"
        except Exception:
            pass
        return None

    @staticmethod
    async def get_all_latencies(proxy: Optional[str], dns: Optional[str] = None) -> List[Tuple[str, float, Optional[str], Optional[str]]]:
        """Test all mirrors and return their latencies and error messages."""
        async def ping(mirror: str, session: aiohttp.ClientSession) -> Tuple[str, float, Optional[str], Optional[str]]:
            global_status = await NetworkDiagnostics.get_uptimerobot_status(mirror, session)
            
            start = time.time()
            try:
                url = f"{mirror}/api/tracks/01568205"
                p = proxy if proxy and not proxy.startswith("socks") else None
                async with session.head(url, proxy=p, timeout=5) as resp:
                    resp.raise_for_status()
                    return mirror, time.time() - start, None, global_status
            except aiohttp.ClientResponseError as e:
                return mirror, float('inf'), f"HTTP {e.status}", global_status
            except asyncio.TimeoutError:
                return mirror, float('inf'), "Timeout", global_status
            except aiohttp.ClientConnectorError:
                return mirror, float('inf'), "Connection Refused", global_status
            except Exception as e:
                return mirror, float('inf'), type(e).__name__, global_status

        connector = None
        if proxy and proxy.startswith("socks"):
            from aiohttp_socks import ProxyConnector
            connector = ProxyConnector.from_url(proxy)
        elif dns and dns.lower() != "auto":
            from aiohttp.resolver import AsyncResolver
            resolver = AsyncResolver(nameservers=[dns])
            connector = aiohttp.TCPConnector(resolver=resolver)
        else:
            from aiohttp.resolver import ThreadedResolver
            connector = aiohttp.TCPConnector(resolver=ThreadedResolver())
            
        headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "Referer": "https://asmr.one/",
            "Origin": "https://asmr.one"
        }
        async with aiohttp.ClientSession(headers=headers, connector=connector) as session:
            tasks = [ping(m, session) for m in HOSTNAME_MIRRORS]
            results = await asyncio.gather(*tasks)
            return sorted(results, key=lambda x: x[1])
