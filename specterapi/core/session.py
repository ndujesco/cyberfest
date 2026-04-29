import sqlite3
import uuid
from pathlib import Path
from datetime import datetime

from .finding import Finding, Severity

SESSIONS_DIR = Path.home() / ".specterapi" / "sessions"


class Session:
    def __init__(self, session_id: str | None = None, target: str = ""):
        SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
        self.id = session_id or (
            datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + str(uuid.uuid4())[:4]
        )
        self.target = target
        self.db_path = SESSIONS_DIR / f"{self.id}.db"
        self._conn = sqlite3.connect(str(self.db_path))
        self._conn.row_factory = sqlite3.Row
        self._init_db()
        if target:
            self._conn.execute(
                "INSERT OR REPLACE INTO sessions(id,target,created_at) VALUES(?,?,?)",
                (self.id, target, datetime.now().isoformat()),
            )
            self._conn.commit()

    def _init_db(self):
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS sessions(
                id TEXT PRIMARY KEY, target TEXT, created_at TEXT, status TEXT DEFAULT 'active'
            );
            CREATE TABLE IF NOT EXISTS endpoints(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT, path TEXT, method TEXT DEFAULT 'GET',
                status_code INTEGER, auth_required INTEGER DEFAULT 1,
                response_size INTEGER, source_file TEXT, content_type TEXT, discovered_at TEXT,
                UNIQUE(session_id, path, method)
            );
            CREATE TABLE IF NOT EXISTS objects(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT, endpoint TEXT, object_id TEXT,
                id_type TEXT, raw_value TEXT, discovered_at TEXT
            );
            CREATE TABLE IF NOT EXISTS findings(
                id TEXT PRIMARY KEY, session_id TEXT, module TEXT,
                severity TEXT, title TEXT, endpoint TEXT, evidence TEXT,
                cvss REAL, cwe TEXT, created_at TEXT
            );
        """)
        self._conn.commit()

    @classmethod
    def list_sessions(cls) -> list[dict]:
        SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
        out = []
        for db_file in sorted(SESSIONS_DIR.glob("*.db"), reverse=True):
            try:
                conn = sqlite3.connect(str(db_file))
                conn.row_factory = sqlite3.Row
                row = conn.execute("SELECT * FROM sessions LIMIT 1").fetchone()
                if row:
                    out.append({
                        "id": row["id"],
                        "target": row["target"],
                        "created_at": row["created_at"],
                        "findings": conn.execute("SELECT COUNT(*) FROM findings").fetchone()[0],
                        "endpoints": conn.execute("SELECT COUNT(*) FROM endpoints").fetchone()[0],
                    })
                conn.close()
            except Exception:
                pass
        return out

    @classmethod
    def load(cls, session_id: str) -> "Session":
        db_path = SESSIONS_DIR / f"{session_id}.db"
        if not db_path.exists():
            raise FileNotFoundError(f"Session not found: {session_id}")
        s = cls.__new__(cls)
        s.id = session_id
        s.db_path = db_path
        s._conn = sqlite3.connect(str(db_path))
        s._conn.row_factory = sqlite3.Row
        s._init_db()
        row = s._conn.execute("SELECT target FROM sessions WHERE id=?", (session_id,)).fetchone()
        s.target = row["target"] if row else ""
        return s

    def add_endpoint(self, path: str, method: str = "GET", status_code: int | None = None,
                     auth_required: bool = True, response_size: int | None = None,
                     source_file: str | None = None, content_type: str | None = None):
        self._conn.execute(
            """INSERT OR IGNORE INTO endpoints
               (session_id,path,method,status_code,auth_required,response_size,source_file,content_type,discovered_at)
               VALUES(?,?,?,?,?,?,?,?,?)""",
            (self.id, path, method, status_code, int(auth_required),
             response_size, source_file, content_type, datetime.now().isoformat()),
        )
        self._conn.commit()

    def add_object(self, endpoint: str, object_id: str, id_type: str = "integer", raw_value: str = ""):
        self._conn.execute(
            "INSERT INTO objects(session_id,endpoint,object_id,id_type,raw_value,discovered_at) VALUES(?,?,?,?,?,?)",
            (self.id, endpoint, object_id, id_type, raw_value, datetime.now().isoformat()),
        )
        self._conn.commit()

    def add_finding(self, f: Finding):
        self._conn.execute(
            """INSERT OR REPLACE INTO findings
               (id,session_id,module,severity,title,endpoint,evidence,cvss,cwe,created_at)
               VALUES(?,?,?,?,?,?,?,?,?,?)""",
            (f.id, self.id, f.module, f.severity.value, f.title,
             f.endpoint, f.evidence, f.cvss, f.cwe, f.created_at),
        )
        self._conn.commit()

    def get_endpoints(self, unauthenticated_only: bool = False) -> list[dict]:
        q = "SELECT * FROM endpoints WHERE session_id=?"
        if unauthenticated_only:
            q += " AND auth_required=0"
        return [dict(r) for r in self._conn.execute(q, (self.id,)).fetchall()]

    def get_objects(self) -> list[dict]:
        return [dict(r) for r in self._conn.execute(
            "SELECT * FROM objects WHERE session_id=?", (self.id,)
        ).fetchall()]

    def get_findings(self) -> list[Finding]:
        rows = self._conn.execute(
            "SELECT * FROM findings WHERE session_id=? ORDER BY cvss DESC", (self.id,)
        ).fetchall()
        return [
            Finding(
                module=r["module"], severity=Severity(r["severity"]),
                title=r["title"], endpoint=r["endpoint"], evidence=r["evidence"],
                id=r["id"], cwe=r["cwe"] or "", cvss=r["cvss"],
            )
            for r in rows
        ]

    def summary(self) -> dict:
        counts = {s.value: 0 for s in Severity}
        for f in self.get_findings():
            counts[f.severity.value] += 1
        return counts

    def close(self):
        self._conn.close()
