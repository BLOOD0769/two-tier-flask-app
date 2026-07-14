# Two-Tier Flask + MySQL Guestbook App

A learning project demonstrating a **two-tier web application** with a full
**CI/CD pipeline**: push code to GitHub → Jenkins auto-builds a Docker image →
deploys a Flask container + MySQL container together via Docker Compose.

---

## Architecture

```
Developer (laptop)
      │  git push
      ▼
   GitHub repo
      │  webhook (on push to main)
      ▼
  Jenkins (running on an EC2 instance)
      │
      ├─ 1. Clone Repository   (checkout scm)
      ├─ 2. Build Docker Image (docker build)
      ├─ 3. Run Docker Compose (docker-compose up -d --build)
      └─ 4. Integration Tests  (curl /health)
                  │
        ┌─────────┴─────────┐
        ▼                   ▼
  flask_web container   mysql_db container
  (port 5000)            (port 3306)
        └──────── app_network ────────┘
                        │
                  db_data volume
              (persists MySQL data)
```

- **Tier 1 (web):** Flask app serving a guestbook page. Reads/writes entries to MySQL.
- **Tier 2 (db):** MySQL 8.0, storing data in a named Docker volume so it survives
  container restarts and rebuilds (but NOT `docker-compose down -v`, which deletes volumes).

---

## Project files

| File | Purpose |
|---|---|
| `app.py` | Flask application — routes, DB connection with retry logic, `/health` check |
| `requirements.txt` | Pinned Python dependencies |
| `templates/index.html` | Guestbook page template |
| `Dockerfile` | Builds the Flask app image (Python 3.12-slim base, runs via gunicorn) |
| `docker-compose.yml` | Defines `web` + `db` services, shared network, named volume |
| `init.sql` | Auto-creates the `entries` table + seed row on MySQL's first startup |
| `.env.example` | Template for required environment variables (no real secrets) |
| `.gitignore` | Excludes `.env`, `__pycache__/`, `*.pyc`, `.DS_Store`, `venv/` |
| `Jenkinsfile` | Declarative pipeline: clone → build → deploy → test |
| `README.md` | This file |

---

## Running locally (on your own machine)

**Requirements:** Docker + Docker Compose installed.

```bash
# 1. Copy the environment template and fill in real values
cp .env.example .env

# 2. Build and start both containers
docker-compose up -d --build

# 3. Visit the app
# http://localhost:5000

# 4. Check the health endpoint
curl http://localhost:5000/health

# 5. Stop everything (keeps your data)
docker-compose down

# 6. Stop AND wipe the database (careful — deletes all entries)
docker-compose down -v
```

---

## Where the data actually lives

MySQL writes its files to `/var/lib/mysql` **inside** the `db` container.
That path is mounted to a Docker **named volume** (`db_data`), which physically
lives on the host machine's disk (e.g. on the EC2 instance, under
`/var/lib/docker/volumes/...`). This means your guestbook entries survive
Jenkins rebuilding the containers on every push — they're only lost if someone
explicitly runs `docker-compose down -v`.

To inspect the data directly:
```bash
docker exec -it mysql_db mysql -u app_user -p guestbook
# (enter the MYSQL_PASSWORD from your .env file)
mysql> SELECT * FROM entries;
mysql> exit
```

---

## CI/CD with Jenkins (deployed on AWS EC2)

**Infrastructure used:**
- 1x AWS EC2 instance (Ubuntu, t2.micro)
- Docker + Docker Compose installed directly on the EC2 host
- Jenkins installed directly on the EC2 host (not containerized)
- A 2GB swap file added on the EC2 instance (the t2.micro's 908MB RAM is tight
  when Docker, MySQL, and Jenkins all run at once — swap prevents OOM issues)

**Pipeline flow (see `Jenkinsfile`):**
1. **Clone Repository** — `checkout scm`, using a GitHub Personal Access Token
   stored in Jenkins credentials (ID: `github-creds`)
2. **Build Docker Image** — `docker build -t two-tier-flask-app .`
3. **Run Docker Compose** — tears down old containers, rebuilds and starts new ones
4. **Integration Tests** — waits 10s, then `curl -f http://localhost:5000/health`;
   fails the whole build if this doesn't return `200 OK`

**Trigger:** A GitHub webhook (`http://<ec2-ip>:8080/github-webhook/`) notifies
Jenkins on every push to `main`, so builds happen automatically — no manual
"Build Now" needed after initial setup.

---

## Notable setup gotchas (for future reference)

If you ever rebuild this EC2/Jenkins setup from scratch, these are the real
issues hit during initial setup — worth checking first if something breaks:

1. **Jenkins GPG key rotation:** Jenkins rotates its apt signing key periodically.
   If `apt-get update` shows `NO_PUBKEY` errors for `pkg.jenkins.io`, the key URL
   in the setup guide may be outdated — check https://pkg.jenkins.io/debian/ for
   the current key filename (e.g. `jenkins.io-2026.key`).
2. **Java version mismatch:** Newer Jenkins versions may require a newer Java
   (e.g. Java 21) even if an older guide says Java 17 is enough. If
   `systemctl start jenkins` fails silently, run
   `sudo -u jenkins java -jar /usr/share/java/jenkins.war --httpPort=8080`
   manually to see the real error.
3. **Docker permission denied in Jenkins builds:** `sudo usermod -aG docker jenkins`
   sometimes doesn't take effect until Jenkins is fully **stopped and started**
   (not just `restart`). Verify with `groups jenkins` — it should list `docker`.
4. **Built-in node goes offline:** on a `t2.micro`, Jenkins' default disk-space
   monitor thresholds can be inaccurate (e.g. checking `/tmp` size on a tmpfs
   that's smaller than the threshold itself). If the node shows offline, check
   **Manage Jenkins → Nodes → Built-In Node** for the specific reason.
5. **Low memory on t2.micro (908MB RAM):** add a swap file to avoid builds
   failing under memory pressure:
   ```bash
   sudo fallocate -l 2G /swapfile
   sudo chmod 600 /swapfile
   sudo mkswap /swapfile
   sudo swapon /swapfile
   echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
   ```

---

## Cost management note

This project was deployed on an AWS EC2 `t3.micro` (Free Tier eligible for the
first 12 months of an AWS account). To avoid ongoing charges:
- **Stop** (don't terminate) the instance when not in use — this avoids compute
  charges while preserving the full setup (Jenkins, Docker, all configs).
- Note: EBS storage (the 20GB disk) is billed separately from compute, and is
  only free for the first 12 months (30GB/month free tier limit). After that,
  a stopped instance's storage will incur a small monthly charge (~$1.60-$2 for
  20GB) until the instance is terminated.
- An Elastic IP is only free while attached to a *running* instance — attaching
  one to an instance you plan to stop frequently will incur idle-IP charges.
