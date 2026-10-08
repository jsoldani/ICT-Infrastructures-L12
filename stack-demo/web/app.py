import os
import time
import socket
from http.server import BaseHTTPRequestHandler, HTTPServer

import psycopg


DB_HOST = os.getenv("DB_HOST", "db")
DB_NAME = os.getenv("POSTGRES_DB", "demo")
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "example")


def get_connection():
    return psycopg.connect(
        host=DB_HOST,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
    )


def initialise_database():
    while True:
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS visits (
                            id SERIAL PRIMARY KEY,
                            container VARCHAR(255) NOT NULL,
                            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                conn.commit()

            print("Connected to PostgreSQL.")
            return

        except psycopg.OperationalError:
            print("Waiting for PostgreSQL...")
            time.sleep(2)


class RequestHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        container = socket.gethostname()

        try:
            with get_connection() as conn:
                with conn.cursor() as cur:

                    cur.execute(
                        "INSERT INTO visits (container) VALUES (%s)",
                        (container,)
                    )

                    cur.execute("""
                        SELECT id, container, timestamp
                        FROM visits
                        ORDER BY id DESC
                    """)

                    visits = cur.fetchall()

                conn.commit()

            rows = "\n".join(
                f"""
                <tr>
                    <td>{id}</td>
                    <td>{container}</td>
                    <td>{timestamp}</td>
                </tr>
                """
                for id, container, timestamp in visits
            )

            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Docker Stack Demo</title>
            </head>
            <body>
                <h1>Docker Stack Demo</h1>

                <p>
                    Request served by:
                    <strong>{container}</strong>
                </p>

                <h2>Visits stored in PostgreSQL</h2>

                <table border="1" cellpadding="6">
                    <tr>
                        <th>ID</th>
                        <th>Container</th>
                        <th>Timestamp</th>
                    </tr>
                    {rows}
                </table>
            </body>
            </html>
            """

            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(html.encode())

        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(
                f"Database error: {e}".encode()
            )

    def log_message(self, format, *args):
        print(
            f"{self.address_string()} - "
            f"{format % args}"
        )


if __name__ == "__main__":
    initialise_database()

    server = HTTPServer(
        ("0.0.0.0", 8080),
        RequestHandler
    )

    print("Web server listening on port 8080...")

    server.serve_forever()