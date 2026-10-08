# Hands-on Exercise: Docker Compose and Docker Stack

## BookShelf — A Database-Backed Application

### Objective

In this exercise, you will build, run, and deploy a simple database-backed web application using Docker.

The exercise is designed to give you hands-on experience with:

* Docker images and Dockerfiles
* Docker containers
* Docker Compose
* Container networking and service discovery
* Environment variables
* Persistent Docker volumes
* Docker Swarm
* Docker Stack
* Service replicas and scaling
* Self-healing and desired-state reconciliation
* Container registries
* Updating a running service

You will progressively deploy the same application using Docker Compose and Docker Stack, and observe the differences between the two approaches.

---

## 1. The Application

You will build a simple web application called **BookShelf**.

The application consists of two services:

1. **Web service**

   * Python application
   * Provides a simple web interface for managing books
   * Listens on port `8080`
   * Stores no persistent data locally

2. **Database service**

   * PostgreSQL
   * Stores the books managed by the application
   * Uses a Docker volume for persistent storage

The resulting architecture is:

```text
                    ┌─────────────────────┐
                    │        Web          │
                    │    Python app       │
                    │      :8080          │
                    └──────────┬──────────┘
                               │
                         HTTP / SQL
                               │
                               ▼
                    ┌─────────────────────┐
                    │         DB          │
                    │     PostgreSQL      │
                    │       :5432         │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   Persistent volume │
                    │       dbdata        │
                    └─────────────────────┘
```

The web application also displays the hostname of the container serving the request. This will allow you to observe the effect of running multiple web replicas later in the exercise.

---

# 2. Prerequisites

You need:

* Docker Engine or Docker Desktop
* Docker Compose
* A terminal
* A web browser

Verify your installation with:

```bash
docker --version
docker compose version
```

You should also verify that Docker is running:

```bash
docker info
```

---

# 3. Project Structure

Create the following directory structure:

```text
bookshelf/
├── compose.yaml
└── web/
    ├── Dockerfile
    ├── requirements.txt
    └── app.py
```

The provided `app.py` implements the BookShelf web application.

The file `requirements.txt` contains:

```text
psycopg[binary]
```

Create a `Dockerfile`:
* start from the image `python:3.13-slim`
* set the working directory as `/app`
* copy `requirements.txt`
* install the requirements by running `pip install --no-cache-dir -r requirements.txt`
* copy the Python application `requirements.txt` in the working directory
* run the following command when starting a container `python app.py`

---

# 4. Build the Docker Image

Build the web application image:

```bash
docker build -t ictinfr/bookshelf-web:1.0 ./web
```

Verify that the image has been created:

```bash
docker images
```

You should see an image named:

```text
ictinfr/bookshelf-web
```

with tag:

```text
1.0
```

### Questions

**Q1.** What is the difference between the Docker image and the container that will be created from it?

**Q2.** What is the purpose of the `WORKDIR`, `COPY`, `RUN`, and `CMD` instructions in the Dockerfile?

---

# 5. Run the Application with Docker Compose

Create a file named `compose.yaml` in the `bookshelf` directory.

The file will run two `services`:

* `web` running from the created image `ictinfr/bookshelf-web:1.0`
* `db` running from the image `postgres:17`

and a volume `dbdata`

The configuration of the `web` service is the following
* port mapping `8080:8080`
* environment variables `DB_HOST: db`, `POSTGRES_DB: bookshelf`, `POSTGRES_USER: postgres`, and `POSTGRES_PASSWORD: example`
* dependency on `db`

The configuration of the `db` service is the following
* environment variables `POSTGRES_DB: bookshelf`, `POSTGRES_USER: postgres`, and `POSTGRES_PASSWORD: example`
* volume mount `dbdata:/var/lib/postgresql/data`

Start the application:

```bash
docker compose up -d
```

Check the running services:

```bash
docker compose ps
```

You should see two services:

```text
web
db
```

Open the application in your browser:

```text
http://localhost:8080
```

---

# 6. Interacting with the Application

The BookShelf application provides a simple form for adding books.

Add several books, for example:

```text
The Lord of the Rings    J.R.R. Tolkien
Clean Code               Robert C. Martin
Design Patterns          Erich Gamma et al.
```

Refresh the page and verify that the books remain available.

Inspect the application logs:

```bash
docker compose logs web
```

Inspect the database logs:

```bash
docker compose logs db
```

You can also inspect all logs:

```bash
docker compose logs
```

---

# 7. Container Networking

List the Docker networks:

```bash
docker network ls
```

You should find a network automatically created by Docker Compose.

Inspect it:

```bash
docker network inspect bookshelf_default
```

The exact network name may differ depending on the name of your project directory.

Notice that both `web` and `db` are connected to the same Docker network.

## Service Discovery

The web application connects to PostgreSQL using:

```text
DB_HOST=db
```

The important point is that `db` is **not** the IP address of the database container.

It is the **service name** defined in `compose.yaml`.

Docker provides DNS-based service discovery inside the Compose network.

### Questions

**Q3.** Why does the application use `db` as the database hostname instead of `localhost`?

**Q4.** What would happen if you changed:

```yaml
DB_HOST: db
```

to:

```yaml
DB_HOST: localhost
```

Explain why.

**Q5.** Find the IP address assigned to the database container.

How could you verify that the application does not need to know this IP address?

---

# 8. Persistent Storage

The PostgreSQL service uses the following volume:

```yaml
volumes:
  - dbdata:/var/lib/postgresql/data
```

List the Docker volumes:

```bash
docker volume ls
```

Inspect the volume:

```bash
docker volume inspect <volume-name>
```

Now stop the application:

```bash
docker compose down
```

Start it again:

```bash
docker compose up -d
```

Open:

```text
http://localhost:8080
```

Verify that your books are still present.

### Question

**Q6.** Why did the books remain available even though the PostgreSQL container was removed and recreated?

---

# 9. Scaling the Web Service

The web application is designed to be stateless: its persistent data is stored in PostgreSQL rather than inside the web container.

Scale the web service to three containers:

```bash
docker compose up -d --scale web=3
```

Check the running containers:

```bash
docker compose ps
```

You should now have three web containers and one database container.

Because all three web containers listen on port `8080` **inside the Docker network**, Docker Compose can run them simultaneously. The host port mapping may be handled differently depending on the Compose implementation; if necessary, remove the explicit host port mapping when scaling and access the service through an appropriate load-balancing configuration.

For this exercise, the main objective is to observe that multiple containers can provide the same service.

Inspect the containers:

```bash
docker ps
```

---

# 10. Web Container Identity

The application displays the hostname of the container serving the request.

Refresh the application several times and observe the hostname.

You may see different container hostnames when requests are distributed among replicas, depending on how the service is exposed.

### Question

**Q7.** Why is it desirable for the web service to be stateless when multiple replicas are running?

---

# 11. Docker Swarm

Docker Swarm provides orchestration capabilities on top of Docker.

Initialize a Swarm:

```bash
docker swarm init
```

Check the Swarm nodes:

```bash
docker node ls
```

Since you are probably using a single machine, you should see one node.

The node will initially act as both:

* manager
* worker

---

# 12. Local Docker Registry

Docker Stack is designed for deploying services in a Swarm, potentially across multiple machines.

In a multi-node deployment, every node needs access to the images used by the services.

For this exercise, use a local Docker registry rather than Docker Hub.

Start a registry:

```bash
docker run -d \
  --name registry \
  -p 5000:5000 \
  --restart=always \
  registry:2
```

Verify that it is running:

```bash
docker ps
```

Tag the BookShelf image for the local registry:

```bash
docker tag \
  ictinfr/bookshelf-web:1.0 \
  localhost:5000/ictinfr/bookshelf-web:1.0
```

Push the image:

```bash
docker push localhost:5000/ictinfr/bookshelf-web:1.0
```

The image is now available from the local registry.

### Question

**Q8.** Why does a multi-node Swarm deployment generally require a registry or another mechanism for distributing images?

---

# 13. Deploy the Application as a Docker Stack

Modify `compose.yaml` so that the web service uses the image from the local registry: `image: localhost:5000/ictinfr/bookshelf-web:1.0`

Before deploying the Stack, remove the Compose deployment:

```bash
docker compose down
```

Deploy the Stack:

```bash
docker stack deploy -c compose.yaml bookshelf
```

List the stacks:

```bash
docker stack ls
```

List the services:

```bash
docker stack services bookshelf
```

You should see:

```text
bookshelf_web
bookshelf_db
```

Inspect the tasks:

```bash
docker stack ps bookshelf
```

---

# 14. Service, Task, and Container

Docker Swarm introduces some terminology that is important to understand.

A **service** describes the desired state of an application component.

For example:

```text
bookshelf_web
```

with:

```text
replicas = 3
```

A **task** is a specific assignment by Swarm to run one instance of a service.

A **container** is the actual running container implementing that task.

Conceptually:

```text
Service
   │
   ├── Task 1 ── Container 1
   │
   ├── Task 2 ── Container 2
   │
   └── Task 3 ── Container 3
```

Inspect the web service:

```bash
docker service inspect bookshelf_web
```

List its tasks:

```bash
docker service ps bookshelf_web
```

### Question

**Q9.** Explain the difference between a Docker service, a Swarm task, and a container.

---

# 15. Scaling the Service

Scale the web service from three to five replicas:

```bash
docker service scale bookshelf_web=5
```

Check the result:

```bash
docker service ps bookshelf_web
```

You should now see five running tasks.

Check the service status:

```bash
docker stack services bookshelf
```

The number of replicas should be:

```text
5/5
```

---

# 16. Self-Healing

One of the important features of an orchestrator is that it maintains the desired state.

Find one of the web containers:

```bash
docker ps
```

Select one of the containers belonging to the `bookshelf_web` service and stop it:

```bash
docker kill <container-id>
```

Now inspect the service:

```bash
docker service ps bookshelf_web
```

You should observe that Swarm starts another task to restore the desired number of replicas.

Check again:

```bash
docker stack services bookshelf
```

The service should eventually return to:

```text
5/5
```

### Question

**Q10.** Why does Swarm create a replacement container after one of the web containers is killed?

Explain the concept of **desired state reconciliation**.

---

# 17. Updating the Application

Modify `app.py`.

For example, change the page title or add a message such as:

```text
BookShelf v1.1
```

Build a new image:

```bash
docker build -t ictinfr/bookshelf-web:1.1 ./web
```

Tag it for the local registry:

```bash
docker tag \
  ictinfr/bookshelf-web:1.1 \
  localhost:5000/ictinfr/bookshelf-web:1.1
```

Push it:

```bash
docker push localhost:5000/ictinfr/bookshelf-web:1.1
```

Update the running service:

```bash
docker service update \
  --image localhost:5000/ictinfr/bookshelf-web:1.1 \
  bookshelf_web
```

Inspect the update:

```bash
docker service ps bookshelf_web
```

Observe how Swarm replaces the old tasks with tasks running the new image.

### Question

**Q11.** What happens to the existing web containers when the service image is updated?

Why is it important that the web application is stateless?

---

# 18. Constraints

The following constraints apply:

* **Do not use Docker Hub** for the BookShelf web image.
* Use the local registry described in Section 12.
* Do not hard-code the IP address of the PostgreSQL container.
* Do not store application data inside the web container.
* Use a Docker volume for PostgreSQL data.
* Do not configure multiple PostgreSQL replicas as a solution to database replication.
* Do not manually run the application containers with `docker run` after creating the Compose/Stack configuration.
* Use Docker Compose for the local deployment and Docker Stack for the Swarm deployment.
* Use service names for service-to-service communication.

> **Note:** The registry address `localhost:5000` is suitable for a single-machine classroom exercise. In a real multi-node Swarm, `localhost` would refer to each individual node, so the registry would need to be exposed through an address reachable by all nodes.

---

# 19. Optional Challenge

Extend the application with a simple REST-like API.

Implement:

```text
GET /books
```

to return the books in JSON format.

For example:

```json
[
  {
    "id": 1,
    "title": "Clean Code",
    "author": "Robert C. Martin"
  },
  {
    "id": 2,
    "title": "The Lord of the Rings",
    "author": "J.R.R. Tolkien"
  }
]
```

You may also implement:

```text
POST /books
```

to add a new book.

Finally, explain why the web service can still be scaled horizontally while using the same PostgreSQL database.

---

# 20. Questions Summary

1. What is the difference between a Docker image and a container?
2. What do the main Dockerfile instructions do?
3. Why does the application use `db` instead of `localhost`?
4. What happens if `DB_HOST=localhost`?
5. How does Docker provide service discovery?
6. Why does the database survive container recreation?
7. Why is the web service stateless?
8. Why does a multi-node Swarm need access to a shared image registry?
9. What are services, tasks, and containers?
10. How does Swarm provide self-healing?
11. What happens when a service image is updated?
12. What are the main differences between Compose and Stack?
13. Why can't PostgreSQL simply be scaled by increasing the replica count?
