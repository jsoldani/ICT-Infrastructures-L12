import os
import socket
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

import psycopg


DB_HOST = os.getenv("DB_HOST", "db")
DB_NAME = os.getenv("POSTGRES_DB", "bookshelf")
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "example")

PORT = 8080


def get_connection():
    """Connect to PostgreSQL, retrying until the database is available."""
    while True:
        try:
            return psycopg.connect(
                host=DB_HOST,
                dbname=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD,
            )
        except psycopg.OperationalError:
            print("Database not ready. Retrying in 2 seconds...")
            time.sleep(2)


def init_database():
    """Create the books table if it does not exist."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS books (
                    id SERIAL PRIMARY KEY,
                    title VARCHAR(255) NOT NULL,
                    author VARCHAR(255) NOT NULL
                )
            """)
        conn.commit()


def get_books():
    """Return all books from the database."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, title, author
                FROM books
                ORDER BY id
            """)
            return cur.fetchall()


def add_book(title, author):
    """Add a new book to the database."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO books (title, author)
                VALUES (%s, %s)
                """,
                (title, author),
            )
        conn.commit()


class BookShelfHandler(BaseHTTPRequestHandler):

    def send_html(self, html, status=200):
        content = html.encode("utf-8")

        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()

        self.wfile.write(content)

    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/":
            self.show_books()

        elif parsed.path == "/health":
            self.send_html("<h1>OK</h1>")

        else:
            self.send_html("<h1>404 - Not Found</h1>", 404)

    def do_POST(self):
        parsed = urlparse(self.path)

        if parsed.path != "/books":
            self.send_html("<h1>404 - Not Found</h1>", 404)
            return

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8")

        data = parse_qs(body)

        title = data.get("title", [""])[0].strip()
        author = data.get("author", [""])[0].strip()

        if not title or not author:
            self.send_html(
                "<h1>400 - Title and author are required</h1>",
                400,
            )
            return

        add_book(title, author)

        self.send_response(303)
        self.send_header("Location", "/")
        self.end_headers()

    def show_books(self):
        books = get_books()

        rows = ""

        for book_id, title, author in books:
            rows += f"""
                <tr>
                    <td>{book_id}</td>
                    <td>{title}</td>
                    <td>{author}</td>
                </tr>
            """

        hostname = socket.gethostname()

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>BookShelf</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    max-width: 800px;
                    margin: 40px auto;
                }}

                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin-top: 20px;
                }}

                th, td {{
                    border: 1px solid #ccc;
                    padding: 8px;
                    text-align: left;
                }}

                th {{
                    background: #eee;
                }}

                input {{
                    padding: 6px;
                    margin-right: 5px;
                }}

                button {{
                    padding: 6px 12px;
                }}

                .info {{
                    margin-top: 30px;
                    color: #666;
                    font-size: 0.9em;
                }}
            </style>
        </head>

        <body>
            <h1>📚 BookShelf</h1>

            <form method="POST" action="/books">
                <input
                    type="text"
                    name="title"
                    placeholder="Book title"
                    required
                >

                <input
                    type="text"
                    name="author"
                    placeholder="Author"
                    required
                >

                <button type="submit">Add book</button>
            </form>

            <h2>Books</h2>

            <table>
                <tr>
                    <th>ID</th>
                    <th>Title</th>
                    <th>Author</th>
                </tr>

                {rows}
            </table>

            <div class="info">
                Web container: <strong>{hostname}</strong><br>
                Database host: <strong>{DB_HOST}</strong>
            </div>
        </body>
        </html>
        """

        self.send_html(html)


if __name__ == "__main__":
    print("Initializing database...")
    init_database()

    print(f"Starting BookShelf on port {PORT}...")
    print(f"Database host: {DB_HOST}")

    server = HTTPServer(("0.0.0.0", PORT), BookShelfHandler)
    server.serve_forever()