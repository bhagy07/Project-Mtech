import os
import paramiko
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class SSHLogFetcherTool:
    """Connects to remote servers over SSH/SFTP and streams log lines using file line tracking."""

    def __init__(self):
        # Keeps track of last read line offset per (service, log_path)
        self.offsets: Dict[str, int] = {}

    @staticmethod
    def get_date_variations(target_date=None) -> List[str]:
        """
        Generates all standard enterprise date timestamp representations for a given date.
        Handles dd-MMM-yy (07-Sep-26), dd-MMM-yyyy (07-Sep-2026), ISO (2026-09-07),
        Indian/DMY (07-09-2026, 07/09/2026), Syslog (Sep 07, Sep  7),
        Underscores (2026_09_07, 07_09_2026), Dots (2026.09.07, 07.09.2026),
        Upper/Lower month variations, and compact (20260907, 07092026, 070926).
        """
        from datetime import datetime, date
        if target_date is None:
            target_date = datetime.now()
        elif isinstance(target_date, str):
            for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d-%b-%y", "%d-%b-%Y", "%d/%m/%Y", "%m/%d/%Y", "%Y%m%d", "%d%m%Y"):
                try:
                    target_date = datetime.strptime(target_date.strip(), fmt)
                    break
                except Exception:
                    pass
            if isinstance(target_date, str):
                return [target_date]

        if isinstance(target_date, date) and not isinstance(target_date, datetime):
            target_date = datetime.combine(target_date, datetime.min.time())

        day_2 = target_date.strftime("%d")           # 07
        day_1 = str(int(day_2))                     # 7
        month_2 = target_date.strftime("%m")         # 09
        month_1 = str(int(month_2))                 # 9
        month_name = target_date.strftime("%b")      # Sep
        month_upper = month_name.upper()             # SEP
        month_lower = month_name.lower()             # sep
        month_full = target_date.strftime("%B")      # September
        year_4 = target_date.strftime("%Y")          # 2026
        year_2 = target_date.strftime("%y")          # 26

        variations = [
            # Standard Financial / Trader formats (07-Sep-26, 07-Sep-2026, etc.)
            f"{day_2}-{month_name}-{year_2}",        # 07-Sep-26
            f"{day_1}-{month_name}-{year_2}",        # 7-Sep-26
            f"{day_2}-{month_upper}-{year_2}",       # 07-SEP-26
            f"{day_2}-{month_lower}-{year_2}",       # 07-sep-26
            f"{day_2}-{month_name}-{year_4}",        # 07-Sep-2026
            f"{day_1}-{month_name}-{year_4}",        # 7-Sep-2026
            f"{day_2}-{month_upper}-{year_4}",       # 07-SEP-2026
            f"{day_2}_{month_name}_{year_2}",        # 07_Sep_26
            f"{day_2}_{month_name}_{year_4}",        # 07_Sep_2026
            f"{day_2}{month_name}{year_2}",          # 07Sep26
            f"{day_2}{month_name}{year_4}",          # 07Sep2026
            f"{day_2}/{month_name}/{year_4}",        # 07/Sep/2026
            f"{day_2}/{month_name}/{year_2}",        # 07/Sep/26

            # ISO 8601 & Standard Dash Formats
            f"{year_4}-{month_2}-{day_2}",           # 2026-09-07
            f"{year_4}_{month_2}_{day_2}",           # 2026_09_07
            f"{year_4}.{month_2}.{day_2}",           # 2026.09.07
            f"{year_4}/{month_2}/{day_2}",           # 2026/09/07

            # DMY / Indian Formats
            f"{day_2}-{month_2}-{year_4}",           # 07-09-2026
            f"{day_2}_{month_2}_{year_4}",           # 07_09_2026
            f"{day_2}.{month_2}.{year_4}",           # 07.09.2026
            f"{day_2}/{month_2}/{year_4}",           # 07/09/2026
            f"{day_2}-{month_2}-{year_2}",           # 07-09-26
            f"{day_2}_{month_2}_{year_2}",           # 07_09_26
            f"{day_2}/{month_2}/{year_2}",           # 07/09/26
            f"{day_1}-{month_2}-{year_4}",           # 7-09-2026
            f"{day_1}/{month_2}/{year_4}",           # 7/09/2026

            # MDY / US Formats
            f"{month_2}-{day_2}-{year_4}",           # 09-07-2026
            f"{month_2}_{day_2}_{year_4}",           # 09_07_2026
            f"{month_2}/{day_2}/{year_4}",           # 09/07/2026
            f"{month_2}/{day_2}/{year_2}",           # 09/07/26

            # Syslog & Daemon Formats
            f"{month_name} {day_2}",                 # Sep 07
            f"{month_name}  {day_1}",                # Sep  7 (syslog space padding)
            f"{month_name} {day_1}",                 # Sep 7

            # Compact Numbers (Log Rotation / Archive Files)
            f"{year_4}{month_2}{day_2}",             # 20260907
            f"{day_2}{month_2}{year_4}",             # 07092026
            f"{day_2}{month_2}{year_2}",             # 070926
            f"{year_2}{month_2}{day_2}",             # 260907
        ]
        return list(dict.fromkeys(variations))

    @classmethod
    def build_date_regex(cls, target_date=None) -> str:
        """Constructs an optimized multi-format regex pattern for grep."""
        variations = cls.get_date_variations(target_date)
        escaped_vars = [v.replace("/", "\\/").replace(".", "\\.") for v in variations]
        return "(" + "|".join(escaped_vars) + ")"

    @staticmethod
    def expand_dynamic_path_tokens(path: str, target_date=None) -> str:
        """Expands dynamic date tokens like {DATE:dd-MMM-yy} (e.g. 07-Sep-26) or {TODAY}."""
        from datetime import datetime, date
        if target_date is None:
            target_date = datetime.now()
        elif isinstance(target_date, date) and not isinstance(target_date, datetime):
            target_date = datetime.combine(target_date, datetime.min.time())
        
        path = path.replace("{DATE:dd-MMM-yy}", target_date.strftime("%d-%b-%y"))
        path = path.replace("{DATE:d-MMM-yy}", f"{int(target_date.strftime('%d'))}-{target_date.strftime('%b-%y')}")
        path = path.replace("{DATE:dd-MMM-yyyy}", target_date.strftime("%d-%b-%Y"))
        path = path.replace("{DATE:d-MMM-yyyy}", f"{int(target_date.strftime('%d'))}-{target_date.strftime('%b-%Y')}")
        path = path.replace("{DATE:dd_MMM_yy}", target_date.strftime("%d_%b_%y"))
        path = path.replace("{DATE:dd_MMM_yyyy}", target_date.strftime("%d_%b_%Y"))
        path = path.replace("{DATE:ddMMMyy}", target_date.strftime("%d%b%y"))
        path = path.replace("{DATE:ddMMMyyyy}", target_date.strftime("%d%b%Y"))
        path = path.replace("{DATE:yyyy-MM-dd}", target_date.strftime("%Y-%m-%d"))
        path = path.replace("{DATE:yyyy_MM_dd}", target_date.strftime("%Y_%m_%d"))
        path = path.replace("{DATE:yyyyMMdd}", target_date.strftime("%Y%m%d"))
        path = path.replace("{DATE:dd-MM-yyyy}", target_date.strftime("%d-%m-%Y"))
        path = path.replace("{DATE:dd_MM_yyyy}", target_date.strftime("%d_%m_%Y"))
        path = path.replace("{DATE:dd.MM.yyyy}", target_date.strftime("%d.%m.%Y"))
        path = path.replace("{DATE:ddMMyyyy}", target_date.strftime("%d%m%Y"))
        path = path.replace("{DATE:ddMMyy}", target_date.strftime("%d%m%y"))
        path = path.replace("{DATE}", target_date.strftime("%d-%b-%y"))
        path = path.replace("{TODAY}", target_date.strftime("%d-%b-%y"))
        return path

    def fetch_new_log_entries(self, service_cfg: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Returns a dictionary mapping log_path -> list of new log lines.
        Handles date folders (e.g. 07-Sep-26), wildcards, trader folders, and nohup.out.
        """
        service_name = service_cfg["name"]
        host = service_cfg["host"]
        ssh_user = service_cfg.get("ssh_user", "root")
        ssh_key = service_cfg.get("ssh_key_path")
        port = int(service_cfg.get("ssh_port", 22))

        # Collect target log paths from config
        configured_paths: List[str] = []
        if "log_paths" in service_cfg and service_cfg["log_paths"]:
            configured_paths.extend(service_cfg["log_paths"])
        elif "log_path" in service_cfg and service_cfg["log_path"]:
            configured_paths.append(service_cfg["log_path"])

        results: Dict[str, List[str]] = {}

        if not configured_paths:
            return results

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            ssh.connect(
                hostname=host,
                port=port,
                username=ssh_user,
                key_filename=ssh_key if (ssh_key and os.path.exists(ssh_key)) else None,
                timeout=5
            )

            # Resolve dynamic tokens ({DATE:dd-MMM-yy}) and wildcards/directories
            resolved_paths: List[str] = []
            for raw_path in configured_paths:
                path = self.expand_dynamic_path_tokens(raw_path)
                if "*" in path or not path.endswith((".out", ".log", ".txt", ".gz")):
                    # It's a wildcard pattern or a directory (like /logs/NPG/pguatweb/UMP_NPG_SERVICE/07-Sep-26)
                    cmd_ls = f"find {path} -maxdepth 2 -type f \\( -name '*.log' -o -name '*.out' -o -name '*.txt' \\) 2>/dev/null | head -n 8"
                    stdin, stdout, stderr = ssh.exec_command(cmd_ls)
                    matched_files = [f.strip() for f in stdout.readlines() if f.strip()]
                    if matched_files:
                        resolved_paths.extend(matched_files)
                    else:
                        # Fallback to direct path
                        resolved_paths.append(path)
                else:
                    resolved_paths.append(path)

            # Deduplicate resolved paths while preserving order
            final_paths = list(dict.fromkeys(resolved_paths))

            for log_path in final_paths:
                offset_key = f"{service_name}:{log_path}"
                last_line = self.offsets.get(offset_key, 0)

                # Tail from last offset line onwards
                cmd = f"tail -n +{last_line + 1} {log_path} 2>/dev/null | head -n 300"
                stdin, stdout, stderr = ssh.exec_command(cmd)
                lines = stdout.readlines()

                if lines:
                    self.offsets[offset_key] = last_line + len(lines)

                results[log_path] = [line.strip() for line in lines if line.strip()]

        except Exception as e:
            logger.error(f"Failed to fetch SSH/SFTP logs from {host} for service '{service_name}' -> {e}")
        finally:
            ssh.close()

        return results

    def scan_user_logs_multi_path(
        self,
        service_cfg: Dict[str, Any],
        base_directories: List[str],
        file_pattern: str = "*user*.log",
        keywords: List[str] = None,
        date_filter: str = None,
        max_files: int = 30,
        max_lines_per_file: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Discovers user-wise log files across multiple directory paths on the remote server
        and scans them for specified keywords or exceptions.
        Returns a list of dictionaries with file details, matched line count, and snippet lines.
        """
        host = service_cfg["host"]
        ssh_user = service_cfg.get("ssh_user", "root")
        ssh_key = service_cfg.get("ssh_key_path")
        port = int(service_cfg.get("ssh_port", 22))

        if not keywords:
            keywords = ["ERROR", "Exception", "NullPointerException", "Failed", "Timeout"]

        keyword_pattern = "|".join([k.strip() for k in keywords if k.strip()])
        if not keyword_pattern:
            keyword_pattern = "error|exception|fail"

        results = []
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            ssh.connect(
                hostname=host,
                port=port,
                username=ssh_user,
                key_filename=ssh_key if (ssh_key and os.path.exists(ssh_key)) else None,
                timeout=8
            )

            date_regex = self.build_date_regex(date_filter) if date_filter else None
            date_vars = self.get_date_variations(date_filter) if date_filter else []

            # Frontend static assets & binary files to exclude from server log analysis
            ignored_exts = (
                '.js', '.mjs', '.cjs', '.css', '.map', '.html', '.htm', '.xhtml',
                '.svg', '.png', '.jpg', '.jpeg', '.gif', '.ico', '.webp', '.bmp',
                '.woff', '.woff2', '.ttf', '.eot', '.otf', '.json', '.jar', '.war',
                '.ear', '.class', '.zip', '.tar', '.pdf', '.docx', '.xlsx', '.ts',
                '.tsx', '.jsx', '.scss', '.sass', '.less'
            )
            ignored_dirs = (
                '/node_modules/', '/assets/', '/static/js/', '/static/css/',
                '/dist/', '/vendor/', '/bower_components/', '/build/'
            )

            # Step 1: Find all matching files across base directories
            discovered_files = []
            for base_dir in base_directories:
                base_dir = base_dir.strip()
                if not base_dir:
                    continue

                if date_filter and date_vars:
                    # Match by date tokens in path or filename (e.g. *07-Sep-26*, *2026-09-07*)
                    date_find_clauses = " -o ".join([f"-name '*{v}*'" for v in date_vars[:8]])
                    cmd_find = (
                        f"find {base_dir} -maxdepth 3 -type f \\( -name '{file_pattern}' -o {date_find_clauses} \\) "
                        f"-not -name '*.js' -not -name '*.css' -not -name '*.map' -not -name '*.html' "
                        f"-not -name '*.png' -not -name '*.ico' -not -name '*.json' 2>/dev/null | head -n {max_files * 2}"
                    )
                else:
                    cmd_find = (
                        f"find {base_dir} -maxdepth 3 -type f -name '{file_pattern}' "
                        f"-not -name '*.js' -not -name '*.css' -not -name '*.map' -not -name '*.html' "
                        f"-not -name '*.png' -not -name '*.ico' -not -name '*.json' 2>/dev/null | head -n {max_files * 2}"
                    )

                stdin, stdout, stderr = ssh.exec_command(cmd_find)
                files = [f.strip() for f in stdout.readlines() if f.strip()]
                discovered_files.extend(files)

            # Filter out any static web assets / Angular bundle files
            clean_discovered = []
            for f in discovered_files:
                f_low = f.lower()
                if any(f_low.endswith(ext) for ext in ignored_exts):
                    continue
                if any(ig_d in f_low for ig_d in ignored_dirs):
                    continue
                clean_discovered.append(f)

            # Deduplicate discovered files
            discovered_files = list(dict.fromkeys(clean_discovered))[:max_files]

            # Step 2: Scan each file for keyword matches
            for file_path in discovered_files:
                # Extract probable username/tag from filename or folder path
                import posixpath
                base_name = posixpath.basename(file_path)
                user_tag = base_name.replace(".log", "").replace("user_", "").replace("app_", "")

                if date_regex:
                    cmd_grep = f"grep -E '{date_regex}' {file_path} 2>/dev/null | grep -i -E '{keyword_pattern}' | head -n {max_lines_per_file}"
                    stdin, stdout, stderr = ssh.exec_command(cmd_grep)
                    matched_lines = [line.rstrip("\r\n") for line in stdout.readlines() if line.strip()]
                    
                    # If empty but the file path itself contains the date, fallback to standard keyword grep
                    if not matched_lines and any(v in file_path for v in date_vars):
                        cmd_fallback = f"grep -i -E '{keyword_pattern}' {file_path} 2>/dev/null | head -n {max_lines_per_file}"
                        stdin, stdout, stderr = ssh.exec_command(cmd_fallback)
                        matched_lines = [line.rstrip("\r\n") for line in stdout.readlines() if line.strip()]
                else:
                    cmd_grep = f"grep -i -E '{keyword_pattern}' {file_path} 2>/dev/null | head -n {max_lines_per_file}"
                    stdin, stdout, stderr = ssh.exec_command(cmd_grep)
                    matched_lines = [line.rstrip("\r\n") for line in stdout.readlines() if line.strip()]

                if matched_lines:
                    results.append({
                        "file_path": file_path,
                        "file_name": base_name,
                        "user_tag": user_tag,
                        "match_count": len(matched_lines),
                        "lines": matched_lines
                    })

        except Exception as e:
            logger.error(f"Failed scanning user logs on {host} -> {e}")
        finally:
            ssh.close()

        return results
