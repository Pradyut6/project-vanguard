import os
import time
import logging
import psycopg2
from flask import Flask, jsonify, request
from prometheus_flask_exporter import PrometheusMetrics

# Structured logging for Grafana Loki ingestion
logging.basicConfig(
    level=logging.INFO,
    format='{"time": "%(asctime)s", "level": "%(levelname)s", "module": "%(module)s", "message": "%(message)s"}'
)
logger = logging.getLogger("vanguard-api")

app = Flask(__name__)
metrics = PrometheusMetrics(app)

# Simulated memory leak buffer for KB-003 Chaos testing
LEAK_BUFFER = []

def get_db_connection():
    return psycopg2.connect(
        host=os.environ.get("POSTGRES_HOST", "localhost"),
        database=os.environ.get("POSTGRES_DB", "vanguard_db"),
        user=os.environ.get("POSTGRES_USER", "vanguard_user"),
        password=os.environ.get("POSTGRES_PASSWORD", ""),
        port=os.environ.get("POSTGRES_PORT", "5432"),
        connect_timeout=3
    )

def init_db():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS incidents (
                id SERIAL PRIMARY KEY,
                title VARCHAR(150) NOT NULL,
                severity VARCHAR(20) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()
        cur.close()
        conn.close()
        logger.info("Database table 'incidents' verified/initialized.")
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")

@app.route("/health", methods=["GET"])
def health_check():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1;")
        cur.close()
        conn.close()
        return jsonify({"status": "healthy", "database": "connected", "os": "Ubuntu 24.04 LTS"}), 200
    except Exception as e:
        logger.error(f"Healthcheck DB failure: {str(e)}")
        return jsonify({"status": "unhealthy", "error": str(e)}), 503

@app.route("/incidents", methods=["GET", "POST"])
def handle_incidents():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        if request.method == "POST":
            data = request.get_json(force=True)
            title = data.get("title", "Unnamed Incident")
            severity = data.get("severity", "P3")
            cur.execute(
                "INSERT INTO incidents (title, severity) VALUES (%s, %s) RETURNING id;",
                (title, severity)
            )
            new_id = cur.fetchone()[0]
            conn.commit()
            cur.close()
            conn.close()
            logger.info(f"Created incident ID={new_id} severity={severity}")
            return jsonify({"id": new_id, "title": title, "severity": severity}), 201
        else:
            cur.execute("SELECT id, title, severity, created_at FROM incidents ORDER BY id DESC LIMIT 50;")
            rows = cur.fetchall()
            cur.close()
            conn.close()
            incidents = [{"id": r[0], "title": r[1], "severity": r[2], "created_at": str(r[3])} for r in rows]
            return jsonify({"count": len(incidents), "incidents": incidents}), 200
    except Exception as e:
        logger.exception("Failed processing /incidents request")
        return jsonify({"error": str(e)}), 500

@app.route("/chaos/memory-leak", methods=["POST"])
def trigger_memory_leak():
    if os.environ.get("ENABLE_CHAOS_ENDPOINTS", "false").lower() != "true":
        return jsonify({"error": "Chaos endpoints disabled"}), 403
    mb_to_allocate = int(request.args.get("mb", 50))
    logger.warning(f"CHAOS TRIGGERED: Allocating {mb_to_allocate}MB into memory buffer")
    LEAK_BUFFER.append(bytearray(mb_to_allocate * 1024 * 1024))
    return jsonify({
        "warning": "Memory allocated",
        "total_leaked_chunks": len(LEAK_BUFFER),
        "approx_leaked_mb": len(LEAK_BUFFER) * mb_to_allocate
    }), 200

with app.app_context():
    init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
