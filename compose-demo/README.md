# Docker Compose Demo

This directory contains the **Docker Compose** version of the database-backed web application used in the Docker lecture.

The purpose of this demo is to show how Docker Compose can describe and run a **multi-container application** declaratively.

---

# 1. What does the demo illustrate?

The application consists of two services:

```text
             ┌─────────────────┐
             │       web       │
Browser ───► │ Python web app  │
   :8080     └────────┬────────┘
                      │
                    db:5432
                      │
              ┌───────▼────────┐
              │       db       │
              │   PostgreSQL   │
              └───────┬────────┘
                      │
                  dbdata volume
```

The web application:

1. accepts HTTP requests on port `8080`;
2. connects to PostgreSQL;
3. creates a `visits` table if necessary;
4. records each request;
5. retrieves the stored visits;
6. displays them in the browser.

The page also displays the hostname of the web container that handled the request.

This makes the application more concrete than a simple `nginx` example while keeping the code small enough for a live lecture demonstration.

---

# 2. Project structure

```text
compose-demo/
├── README.md
├── compose.yaml
└── web/
    ├── Dockerfile
    ├── requirements.txt
    └── app.py
```

## `web/app.py`

A minimal Python HTTP application using PostgreSQL.

## `web/requirements.txt`

Contains the PostgreSQL Python driver:

```text
psycopg[binary]
```

## `web/Dockerfile`

Builds the image for the web application.

## `compose.yaml`

Defines the complete multi-container application.

---

# 3. Application architecture

The Compose file defines:

- a `web` service;
- a `db` service;
- a `dbdata` named volume.

The web service exposes:

```text
localhost:8080
```

The PostgreSQL service is available to the web service as:

```text
db:5432
```

The hostname `db` is the Compose service name. Docker provides DNS resolution between services on the Compose network.

The web application does not need to know the database container's IP address.

---

# 4. Start the demo

From this directory:

```bash
cd compose-demo
```

Start the application and build the web image:

```bash
docker compose up --build
```

To run in the background:

```bash
docker compose up -d --build
```

Docker will:

1. build the web image;
2. pull the PostgreSQL image if necessary;
3. create a network;
4. create the database volume;
5. create the two containers;
6. start the services.

---

# 5. Open the application

Open the following URL in a browser:

<http://localhost:8080>

You should see a page similar to:

```text
Docker Compose Demo

Request served by:
<container hostname>

Visits stored in PostgreSQL
...
```

Refresh the page several times.

Each request is inserted into PostgreSQL and then displayed.

---

# 6. Inspect the application

List the Compose services:

```bash
docker compose ps
```

View all logs:

```bash
docker compose logs
```

Follow the logs:

```bash
docker compose logs -f
```

View only the web logs:

```bash
docker compose logs web
```

View only the database logs:

```bash
docker compose logs db
```

---

# 7. Inspect the Docker objects

List containers:

```bash
docker ps
```

List images:

```bash
docker image ls
```

List networks:

```bash
docker network ls
```

List volumes:

```bash
docker volume ls
```

Compose creates a network and a named volume for this application.

---

# 8. Inspect the database volume

The PostgreSQL service uses:

```yaml
volumes:
  - dbdata:/var/lib/postgresql/data
```

The volume is declared as:

```yaml
volumes:
  dbdata:
```

Inspect it:

```bash
docker volume inspect dbdata
```

Now stop and remove the containers:

```bash
docker compose down
```

Start the application again:

```bash
docker compose up -d
```

The previously stored visits should still exist.

Why?

Because the containers were removed, but the named volume was not.

---

# 9. Remove the database data

If you want to remove the volume as well:

```bash
docker compose down -v
```

This is intentionally destructive for this demo.

The next time the application starts, PostgreSQL will have an empty database and the Python application will recreate the `visits` table.

> Do not use `docker compose down -v` if you want to preserve the demonstration data.

---

# 10. Inspect the application from inside a container

Find the running containers:

```bash
docker compose ps
```

Open a shell in the web container:

```bash
docker compose exec web sh
```

Inside the container, for example:

```bash
ls
```

and:

```bash
python --version
```

Exit:

```bash
exit
```

You can also inspect the database container:

```bash
docker compose exec db sh
```

---

# 11. Understanding the database connection

The Compose file supplies:

```yaml
environment:
  DB_HOST: db
  POSTGRES_DB: demo
  POSTGRES_USER: postgres
  POSTGRES_PASSWORD: example
```

The Python application reads these values from environment variables.

The important point is:

```text
DB_HOST=db
```

The application connects to:

```text
db:5432
```

not to:

```text
localhost:5432
```

Inside the web container, `localhost` means the web container itself, not the database container.

---

# 12. Why does the application retry?

The Compose file contains:

```yaml
depends_on:
  - db
```

This expresses a dependency between the services, but starting the database container does not necessarily mean that PostgreSQL is immediately ready to accept connections.

The Python application therefore retries the database connection until PostgreSQL becomes available.

This is an important real-world lesson:

> **Container startup and application readiness are not necessarily the same thing.**

---

# 13. Stop and restart the application

Stop the services without removing the containers:

```bash
docker compose stop
```

Start them again:

```bash
docker compose start
```

Restart:

```bash
docker compose restart
```

---

# 14. Shut down the demo

To stop and remove the application containers and network:

```bash
docker compose down
```

To also remove the database volume:

```bash
docker compose down -v
```

---

# 15. Suggested live-demo sequence

For a lecture demonstration, the following sequence is recommended.

### Step 1 — Start

```bash
docker compose up --build
```

### Step 2 — Open

Open:

<http://localhost:8080>

### Step 3 — Generate data

Refresh the page several times.

Observe that the visits are stored in PostgreSQL.

### Step 4 — Inspect

```bash
docker compose ps
docker compose logs
docker volume ls
docker network ls
```

### Step 5 — Explain service-name networking

Point out that the web service connects to:

```text
db:5432
```

### Step 6 — Demonstrate persistence

```bash
docker compose down
docker compose up -d
```

Refresh the page and observe that the visits remain.

### Step 7 — Demonstrate volume removal

```bash
docker compose down -v
docker compose up -d
```

The previous visits are gone.

