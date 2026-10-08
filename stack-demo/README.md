# Docker Stack Demo

This directory contains the **Docker Stack** version of the database-backed web application used in the Docker lecture.

It builds upon the Docker Compose demo and introduces **Docker Swarm orchestration**.

The same application is deliberately used in both demos so that students can clearly see what changes when moving from a local multi-container application to an orchestrated deployment.

---

# 1. What does the demo illustrate?

The application consists of:

- a Python web service;
- a PostgreSQL database;
- persistent database storage.

The main difference from the Compose demo is that the web service is deployed as a **Swarm service with multiple replicas**.

Conceptually:

```text
                         Docker Stack
                              │
                ┌─────────────┴─────────────┐
                │                           │
          web service                  db service
          replicas = 3                 replicas = 1
                │                           │
        ┌───────┼───────┐                   │
        ▼       ▼       ▼                   ▼
      web-1   web-2   web-3                db
                │                           │
                └───────────┬───────────────┘
                            ▼
                       dbdata volume
```

---

# 2. Why is this a separate demo?

The `compose-demo` directory demonstrates:

> **How to run a multi-container application.**

The `stack-demo` directory demonstrates:

> **How to orchestrate application services using Docker Swarm.**

The application itself is almost unchanged. The deployment model is what changes.

This is intentional: students can focus on the additional concepts introduced by Swarm rather than learning a completely different application.

---

# 3. Main differences from the Compose demo

| Compose demo | Stack demo |
|---|---|
| Local multi-container application | Swarm-managed application |
| `docker compose up` | `docker stack deploy` |
| Containers are the main abstraction | Services and tasks are introduced |
| No cluster scheduler | Swarm scheduler |
| No native cluster replication | Service replicas |
| Local execution | Cluster-oriented execution |
| No desired-state orchestration | Desired-state reconciliation |
| Limited self-healing | Swarm maintains service replicas |
| `build:` can be used locally | Images should normally be available from a registry |

The Stack demo therefore adds:

- Docker Swarm;
- nodes;
- services;
- tasks;
- replicas;
- scaling;
- self-healing;
- service updates.

---

# 4. Project structure

```text
stack-demo/
├── README.md
├── compose.yaml
└── web/
    ├── Dockerfile
    ├── requirements.txt
    └── app.py
```

The application code is intentionally very similar to the Compose demo.

The main change is the deployment configuration.

---

# 5. Why use a registry?

The web service is specified using an image:

```yaml
image: YOUR_DOCKERHUB_USERNAME/stack-demo-web:1.0
```

rather than:

```yaml
build: ./web
```

This is important when a Stack spans multiple machines.

Suppose the Swarm has:

```text
Manager
   │
   ├── Worker 1
   ├── Worker 2
   └── Worker 3
```

If a web task is scheduled on Worker 2, that node needs access to the application image.

A registry provides a common source:

```text
                    Registry
                   /    |    \
                  /     |     \
              Node 1  Node 2  Node 3
```

For this reason, build the image and push it to a registry before deploying the Stack.

---

# 6. Prepare the image

Replace:

```text
YOUR_DOCKERHUB_USERNAME
```

with your Docker Hub username.

Build the image:

```bash
docker build \
  -t YOUR_DOCKERHUB_USERNAME/stack-demo-web:1.0 \
  ./web
```

Check it:

```bash
docker image ls
```

Log in to Docker Hub:

```bash
docker login
```

Push the image:

```bash
docker push YOUR_DOCKERHUB_USERNAME/stack-demo-web:1.0
```

Make sure `compose.yaml` contains the same image name:

```yaml
image: YOUR_DOCKERHUB_USERNAME/stack-demo-web:1.0
```

---

# 7. Initialize Docker Swarm

Docker Stack requires Docker Swarm.

Initialize a Swarm:

```bash
docker swarm init
```

Inspect the nodes:

```bash
docker node ls
```

For a classroom demonstration on one machine, you will normally have one node.

A real Swarm can contain multiple nodes.

---

# 8. Deploy the Stack

From this directory:

```bash
docker stack deploy -c compose.yaml demo
```

Here:

- `-c compose.yaml` specifies the application definition;
- `demo` is the Stack name.

Check the deployed stacks:

```bash
docker stack ls
```

You should see:

```text
NAME      SERVICES
demo      2
```

---

# 9. Inspect the services

Run:

```bash
docker stack services demo
```

The expected result is conceptually:

```text
NAME       MODE        REPLICAS
demo_web   replicated  3/3
demo_db    replicated  1/1
```

The important difference from Compose is that `web` is now a **service with a desired number of replicas**.

---

# 10. Inspect tasks

Run:

```bash
docker stack ps demo
```

You should see three tasks for the web service and one for PostgreSQL.

The conceptual model is:

```text
Stack
 │
 ├── Service: demo_web
 │    ├── Task → Container
 │    ├── Task → Container
 │    └── Task → Container
 │
 └── Service: demo_db
      └── Task → Container
```

A **service** expresses what should be running.

A **task** is an individual scheduled instance of that service.

---

# 11. Open the application

Open:

<http://localhost:8080>

Refresh the page several times.

Each request:

1. reaches the web service;
2. is handled by a web replica;
3. is recorded in PostgreSQL;
4. is displayed in the browser.

The application displays the hostname of the web container.

This allows you to observe which replica processed a request.

---

# 12. Scale the web service

Initially:

```yaml
deploy:
  replicas: 3
```

Scale it to five replicas:

```bash
docker service scale demo_web=5
```

Check:

```bash
docker stack services demo
```

You should see:

```text
demo_web   replicated   5/5
```

Inspect the tasks:

```bash
docker stack ps demo
```

The Stack now maintains five web replicas.

---

# 13. Desired state

The important idea is that Swarm maintains a **desired state**.

If the desired state is:

```text
5 web replicas
```

but only four are running:

```text
Desired: 5
Actual:  4
```

Swarm attempts to reconcile the difference.

Conceptually:

```text
Desired state
      │
      ▼
Swarm controller
      │
      ▼
Compare desired vs actual
      │
      ▼
Create/stop/update tasks
      │
      ▼
Actual state approaches desired state
```

This is one of the fundamental differences between simply running containers and using an orchestrator.

---

# 14. Demonstrate self-healing

List the running containers:

```bash
docker ps
```

Find one belonging to `demo_web`.

Stop it:

```bash
docker kill <container-id>
```

Immediately inspect the service:

```bash
docker service ps demo_web
```

Swarm should create a replacement.

The service returns to its desired number of replicas.

This demonstrates:

> **The individual container is disposable; the service's desired state is what Swarm maintains.**

---

# 15. Update the application

The image is versioned using tags.

For example:

```text
stack-demo-web:1.0
stack-demo-web:2.0
```

Modify `web/app.py`.

For example, change the title to:

```html
<h1>Docker Stack Demo - Version 2</h1>
```

Build version 2:

```bash
docker build \
  -t YOUR_DOCKERHUB_USERNAME/stack-demo-web:2.0 \
  ./web
```

Push it:

```bash
docker push YOUR_DOCKERHUB_USERNAME/stack-demo-web:2.0
```

Update the service:

```bash
docker service update \
  --image YOUR_DOCKERHUB_USERNAME/stack-demo-web:2.0 \
  demo_web
```

Inspect the update:

```bash
docker service ps demo_web
```

Swarm replaces tasks running version `1.0` with tasks running version `2.0`.

---

# 16. Deploying the updated Stack definition

Alternatively, modify `compose.yaml`:

```yaml
image: YOUR_DOCKERHUB_USERNAME/stack-demo-web:2.0
```

Then run:

```bash
docker stack deploy -c compose.yaml demo
```

Swarm compares the desired configuration with the current state and updates the service.

---

# 17. Why is PostgreSQL not replicated?

The web service is configured as:

```yaml
deploy:
  replicas: 3
```

The database is:

```yaml
deploy:
  replicas: 1
```

This is intentional.

The web application is effectively stateless:

```text
web-1 ─┐
web-2 ─┼──► PostgreSQL
web-3 ─┘
```

The persistent state is stored in PostgreSQL.

Simply setting:

```yaml
replicas: 3
```

for PostgreSQL would **not** automatically create a correct PostgreSQL replication cluster.

Real stateful services require mechanisms for:

- replication;
- consistency;
- failover;
- storage;
- backups;
- recovery.

This demo intentionally leaves those topics outside its scope.

---

# 18. Important note about multi-node Swarms

On a single machine, this demo is useful for learning:

- Stack deployment;
- services;
- replicas;
- tasks;
- scaling;
- self-healing;
- updates.

However, it does not demonstrate actual workload distribution across multiple physical/virtual machines.

For a multi-node Swarm:

```text
             Manager
             /     \
            /       \
       Worker 1   Worker 2
```

the same Stack can schedule replicas across different nodes.

The application image must be accessible to all nodes through a registry.

---

# 19. Useful Stack commands

List stacks:

```bash
docker stack ls
```

List services:

```bash
docker stack services demo
```

List tasks:

```bash
docker stack ps demo
```

Deploy/update:

```bash
docker stack deploy -c compose.yaml demo
```

Remove the Stack:

```bash
docker stack rm demo
```

---

# 20. Useful Swarm service commands

List services:

```bash
docker service ls
```

Inspect a service:

```bash
docker service inspect demo_web
```

List its tasks:

```bash
docker service ps demo_web
```

Scale:

```bash
docker service scale demo_web=5
```

View service logs:

```bash
docker service logs demo_web
```

Update the image:

```bash
docker service update \
  --image YOUR_DOCKERHUB_USERNAME/stack-demo-web:2.0 \
  demo_web
```

---

# 21. Suggested live-demo sequence

For a lecture demonstration, use the following sequence.

## Step 1 — Build the image

```bash
docker build \
  -t YOUR_DOCKERHUB_USERNAME/stack-demo-web:1.0 \
  ./web
```

## Step 2 — Push it

```bash
docker login
docker push YOUR_DOCKERHUB_USERNAME/stack-demo-web:1.0
```

## Step 3 — Initialize Swarm

```bash
docker swarm init
```

## Step 4 — Deploy

```bash
docker stack deploy -c compose.yaml demo
```

## Step 5 — Inspect

```bash
docker stack ls
docker stack services demo
docker stack ps demo
```

## Step 6 — Open the application

Open:

<http://localhost:8080>

Refresh several times.

## Step 7 — Scale

```bash
docker service scale demo_web=5
```

Then:

```bash
docker stack services demo
```

## Step 8 — Demonstrate self-healing

```bash
docker ps
docker kill <web-container-id>
docker service ps demo_web
```

Observe that Swarm creates a replacement.

## Step 9 — Update the application

Build and push version 2:

```bash
docker build \
  -t YOUR_DOCKERHUB_USERNAME/stack-demo-web:2.0 \
  ./web

docker push YOUR_DOCKERHUB_USERNAME/stack-demo-web:2.0
```

Update:

```bash
docker service update \
  --image YOUR_DOCKERHUB_USERNAME/stack-demo-web:2.0 \
  demo_web
```

Inspect:

```bash
docker service ps demo_web
```

---

# 22. Cleanup

Remove the Stack:

```bash
docker stack rm demo
```

If you no longer need the Swarm:

```bash
docker swarm leave --force
```

Check remaining volumes:

```bash
docker volume ls
```

If you want to remove the database data as well, remove the relevant volume.

> Be careful when deleting volumes: doing so permanently removes the stored PostgreSQL data.

---

# 23. Key concepts demonstrated

This demo illustrates:

- Docker Swarm;
- Docker Stack;
- services;
- tasks;
- replicas;
- desired state;
- service scheduling;
- scaling;
- self-healing;
- service updates;
- image versioning;
- service-name networking;
- persistent volumes;
- stateless vs stateful services;
- container registries.

The key conceptual progression is:

```text
Compose
  │
  │ multi-container application
  ▼
Swarm
  │
  │ orchestration
  ▼
Stack
  │
  ├── Services
  ├── Tasks
  ├── Replicas
  ├── Scaling
  ├── Self-healing
  └── Updates
```

The central lesson is:

> **Docker Compose describes and runs a multi-container application; Docker Stack uses the same application-oriented concepts to deploy services under Docker Swarm orchestration.**
