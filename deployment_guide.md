# Production Deployment Guide: RAG Chatbot on DigitalOcean

This guide outlines the step-by-step process for deploying the RAG Chatbot application (FastAPI backend, Frontend, and Vector Database) to a production environment on DigitalOcean.

## 1. Infrastructure Provisioning

For a Docker Compose-based application with a backend, frontend, and vector database, we recommend using a **DigitalOcean Basic Droplet** initially, scaling up as needed, rather than the App Platform. App Platform can be more expensive for long-running vector databases and complex multi-container setups.

**Recommended Setup:**
*   **Service:** DigitalOcean Droplet (Virtual Machine)
*   **OS:** Ubuntu 24.04 LTS (x64)
*   **Plan:** Basic (Premium Intel or AMD)
*   **Size:** At least 2GB RAM / 1 CPU (Vector databases and ML models can be memory-intensive; monitor usage and upgrade to 4GB if necessary).
*   **Extras:** Enable Backups and IPv6. Include your SSH keys for secure access.

### 1.1 Provisioning Steps:
1. Log in to your DigitalOcean account.
2. Click **Create** -> **Droplets**.
3. Choose the region closest to your target audience.
4. Select the Ubuntu 24.04 image.
5. Choose the recommended plan and size.
6. Select your SSH Key for authentication.
7. Name your Droplet (e.g., `satusatu-chatbot-prod`) and click **Create Droplet**.

## 2. Server Environment Setup

Once the Droplet is running, you need to prepare the server to run Docker containers and handle your environment variables securely.

### 2.1 Install Dependencies
SSH into your new Droplet:
```bash
ssh root@<DROPLET_IP_ADDRESS>
```

Install Docker and Docker Compose:
```bash
# Update packages
apt update && apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose plugin
apt-get install docker-compose-plugin -y

# Verify installations
docker --version
docker compose version
```

### 2.2 Secure Handling of `.env` Variables
Never commit your `.env` file to version control. On the production server, create the `.env` file manually.

```bash
mkdir -p /opt/satusatu-chatbot
cd /opt/satusatu-chatbot
nano .env # Or use vim
```
Paste your production environment variables into this file. Ensure you define production-specific values for:
*   API Keys (OpenAI, Pinecone/Qdrant, etc.)
*   Database URLs
*   CORS Origins (`http://panjigautama.com`, `https://panjigautama.com`)
*   Environment type (`ENVIRONMENT=production`)

Set secure permissions on the `.env` file:
```bash
chmod 600 .env
```

## 3. Container Deployment

Transfer your application code and configuration to the server and start the containers.

### 3.1 Transfer Files
From your local machine, use `rsync` or `scp` to transfer the necessary files to the Droplet. You primarily need the `docker-compose.yml`, backend/frontend directories (or pre-built images if using a registry), and any proxy configurations.

If cloning from a private Git repository directly on the server (Recommended):
```bash
# On the server
apt install git -y
# Generate a deploy key and add it to GitHub/GitLab
ssh-keygen -t ed25519 -C "deploy@satusatu"
cat ~/.ssh/id_ed25519.pub

git clone git@github.com:rhapsodixx/poc-chatbot-satusatu.git /opt/satusatu-chatbot
cd /opt/satusatu-chatbot
```

### 3.2 Build and Run Containers
In the project directory on the server:

```bash
cd /opt/satusatu-chatbot

# Build the images (if building on the server)
docker compose -f docker-compose.yml build

# Start the containers in detached mode
docker compose -f docker-compose.yml up -d

# Check the status of the containers
docker compose ps
docker compose logs -f
```

*(Note: If your `docker-compose.yml` specifies an `html` or `dist` volume for the frontend, ensure the frontend build process runs successfully).*

## 4. Networking & Security

Exposing default Docker ports directly to the internet is completely unsafe. We will use **Nginx** as a reverse proxy, configure a custom domain, and secure it with Let's Encrypt SSL.

### 4.1 Domain Configuration
1. Go to your Domain Registrar (e.g., Namecheap, Route53, GoDaddy).
2. Create an **A Record** pointing your domain (e.g., `satusatuconcierge.panjigautama.com`) to your Droplet's Public IP Address.

### 4.2 Setup Nginx Reverse Proxy
Install Nginx on the host Droplet:
```bash
apt install nginx -y
```

Create an Nginx server block configuration for your application:
```bash
nano /etc/nginx/sites-available/satusatu-chatbot
```

Add the following configuration (adjust ports based on your `docker-compose.yml` internal mappings):
```nginx
server {
    listen 80;
    server_name satusatuconcierge.panjigautama.com; # Replace with your domain

    # Frontend block (assuming frontend runs on port 3000 internally)
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Backend API block (assuming backend runs on port 8000 internally)
    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable the site and reload Nginx:
```bash
ln -s /etc/nginx/sites-available/satusatu-chatbot /etc/nginx/sites-enabled/
nginx -t
systemctl reload nginx
```

### 4.3 Enable SSL/HTTPS via Let's Encrypt
Install Certbot and the Nginx plugin:
```bash
apt install certbot python3-certbot-nginx -y
```

Obtain and configure the SSL certificate:
```bash
certbot --nginx -d satusatuconcierge.panjigautama.com
```
Follow the prompts, and choose to redirect all HTTP traffic to HTTPS. Certbot will automatically set up a cron job to renew the certificates before they expire.

### 4.4 Configure DigitalOcean Firewall (UFW/Cloud Firewall)
For security, restrict incoming traffic to only necessary ports.
1. Go to DigitalOcean Console -> **Networking** -> **Firewalls**.
2. Create a Firewall and apply it to your Droplet.
3. **Inbound Rules:**
   - SSH (Port 22) -> Limit to specific IP addresses if possible, or All IPv4/IPv6.
   - HTTP (Port 80) -> All IPv4/IPv6 (for Let's Encrypt validation and redirects).
   - HTTPS (Port 443) -> All IPv4/IPv6.
4. Drop all other inbound traffic.

## 5. CI/CD Pipeline Strategy (GitHub Actions)

To automate future deployments and avoid manual SSH operations, implement a CI/CD pipeline using GitHub Actions.

### Pipeline Overview
1. **Trigger:** Push to the `main` or `production` branch.
2. **Build/Test Job:** Run code linters and unit tests (if applicable).
3. **Deploy Job:**
   - SSH into the DigitalOcean Droplet via GitHub Secrets.
   - Pull the latest code from the repository.
   - Rebuild the necessary Docker images.
   - Restart the containers with zero downtime (or minimal downtime).

### Example GitHub Action Configuration (`.github/workflows/deploy.yml`)
Add the following secrets to your GitHub Repository Settings: `DO_DROPLET_IP`, `DO_SSH_KEY` (private key), `DO_SSH_USER` (usually `root` or `deploy`).

```yaml
name: Deploy to DigitalOcean Production

on:
  push:
    branches:
      - main

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Deploy via SSH
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.DO_DROPLET_IP }}
          username: ${{ secrets.DO_SSH_USER }}
          key: ${{ secrets.DO_SSH_KEY }}
          script: |
            cd /opt/satusatu-chatbot
            git pull origin main
            docker compose -f docker-compose.yml build
            docker compose -f docker-compose.yml up -d --remove-orphans
            docker system prune -f # Clean up unused images
```

This ensures that every push to the main branch automatically updates your live application securely and consistently.
