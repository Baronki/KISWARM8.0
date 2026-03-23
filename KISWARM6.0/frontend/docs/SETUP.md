# KINFP-Portal Setup & Installation Guide

This guide provides step-by-step instructions for setting up KINFP-Portal in development and production environments.

## System Requirements

Before installing KINFP-Portal, ensure your system meets the following requirements:

| Component | Minimum | Recommended | Notes |
|-----------|---------|-------------|-------|
| **Node.js** | 16.x | 22.13.0+ | LTS versions recommended |
| **pnpm** | 8.0 | 9.0+ | Package manager |
| **MySQL** | 8.0 | 8.0.35+ | Or TiDB 7.0+ |
| **RAM** | 2GB | 4GB+ | For dev server and database |
| **Disk Space** | 2GB | 5GB+ | For dependencies and database |
| **OS** | Linux/macOS/Windows | Linux (Ubuntu 22.04+) | Windows requires WSL2 |

## Development Setup

### Step 1: Clone the Repository

```bash
git clone https://github.com/Baronki/kinfp-portal.git
cd kinfp-portal
```

### Step 2: Install Node.js and pnpm

**On Ubuntu/Debian:**
```bash
# Install Node.js 22 (LTS)
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install pnpm
npm install -g pnpm@latest

# Verify installation
node --version
pnpm --version
```

**On macOS (using Homebrew):**
```bash
# Install Node.js
brew install node

# Install pnpm
brew install pnpm

# Verify installation
node --version
pnpm --version
```

**On Windows (using WSL2):**
```bash
# Inside WSL2 Ubuntu terminal
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt-get install -y nodejs
npm install -g pnpm@latest
```

### Step 3: Install Project Dependencies

```bash
# Install all dependencies
pnpm install

# Verify installation
pnpm list
```

This command installs dependencies for both frontend and backend, as defined in `package.json`.

### Step 4: Set Up the Database

**Option A: Using MySQL (Local)**

```bash
# Install MySQL Server
# On Ubuntu
sudo apt-get install mysql-server

# On macOS
brew install mysql

# Start MySQL service
sudo systemctl start mysql      # Ubuntu
brew services start mysql       # macOS

# Create database and user
mysql -u root -p << EOF
CREATE DATABASE kinfp_portal;
CREATE USER 'kinfp_user'@'localhost' IDENTIFIED BY 'secure_password_here';
GRANT ALL PRIVILEGES ON kinfp_portal.* TO 'kinfp_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
EOF
```

**Option B: Using Docker (Recommended)**

```bash
# Pull and run MySQL container
docker run --name kinfp-mysql \
  -e MYSQL_ROOT_PASSWORD=root_password \
  -e MYSQL_DATABASE=kinfp_portal \
  -e MYSQL_USER=kinfp_user \
  -e MYSQL_PASSWORD=user_password \
  -p 3306:3306 \
  -d mysql:8.0

# Verify connection
mysql -h 127.0.0.1 -u kinfp_user -p kinfp_portal
```

**Option C: Using TiDB Cloud (Production)**

1. Create account at [TiDB Cloud](https://tidbcloud.com)
2. Create a new cluster
3. Get connection string from cluster details
4. Use connection string in `.env` file

### Step 5: Configure Environment Variables

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```env
# Database Configuration
DATABASE_URL=mysql://kinfp_user:secure_password_here@localhost:3306/kinfp_portal

# OAuth Configuration (Manus)
VITE_APP_ID=your_manus_app_id
VITE_OAUTH_PORTAL_URL=https://oauth.manus.im
OAUTH_SERVER_URL=https://oauth-server.manus.im

# Storage Configuration (S3)
BUILT_IN_FORGE_API_URL=https://api.manus.im
BUILT_IN_FORGE_API_KEY=your_forge_api_key
VITE_FRONTEND_FORGE_API_URL=https://api.manus.im
VITE_FRONTEND_FORGE_API_KEY=your_frontend_api_key

# JWT Configuration
JWT_SECRET=your_jwt_secret_key_min_32_chars

# Owner Information
OWNER_NAME=Marco Heyd
OWNER_OPEN_ID=your_owner_open_id

# Analytics (Optional)
VITE_ANALYTICS_ENDPOINT=https://analytics.manus.im
VITE_ANALYTICS_WEBSITE_ID=your_website_id

# App Configuration
VITE_APP_TITLE="KINFP - KI-natives Finanzprotokoll"
VITE_APP_LOGO=https://cdn.example.com/logo.png
```

**Important**: Never commit `.env` file to version control. Add it to `.gitignore`.

### Step 6: Initialize the Database

Run Drizzle migrations to create tables:

```bash
# Generate migrations from schema
pnpm db:push

# Verify tables were created
mysql -u kinfp_user -p kinfp_portal -e "SHOW TABLES;"
```

Expected output:
```
Tables_in_kinfp_portal
files
users
```

### Step 7: Start the Development Server

```bash
# Start dev server (runs both frontend and backend)
pnpm dev

# Output should show:
# VITE v7.1.9  ready in 549 ms
# ➜  Local:   http://localhost:3000/
# ➜  Network: http://169.254.0.21:3000/
```

Open `http://localhost:3000` in your browser. The application should load with the KINFP Portal homepage.

### Step 8: Verify Installation

Check that all systems are working:

```bash
# Test database connection
mysql -u kinfp_user -p kinfp_portal -e "SELECT COUNT(*) FROM users;"

# Run tests
pnpm test

# Build for production
pnpm build
```

## Environment Variables Reference

### Required Variables

| Variable | Purpose | Example |
|----------|---------|---------|
| `DATABASE_URL` | Database connection string | `mysql://user:pass@localhost:3306/db` |
| `VITE_APP_ID` | Manus OAuth application ID | `app_123456` |
| `JWT_SECRET` | JWT signing secret (min 32 chars) | `your_secret_key_here` |
| `BUILT_IN_FORGE_API_KEY` | S3 storage API key | `key_xyz789` |

### Optional Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `VITE_ANALYTICS_ENDPOINT` | Analytics service URL | (disabled) |
| `VITE_APP_TITLE` | Browser tab title | "KINFP Portal" |
| `VITE_APP_LOGO` | App logo URL | (default logo) |

## Troubleshooting

### Database Connection Issues

**Error**: `Error: connect ECONNREFUSED 127.0.0.1:3306`

**Solution**: Ensure MySQL is running:
```bash
# Check MySQL status
sudo systemctl status mysql

# Start MySQL if stopped
sudo systemctl start mysql

# Or verify Docker container is running
docker ps | grep mysql
```

### Port Already in Use

**Error**: `Error: listen EADDRINUSE :::3000`

**Solution**: Kill the process using port 3000:
```bash
# On Linux/macOS
lsof -i :3000
kill -9 <PID>

# Or use a different port
PORT=3001 pnpm dev
```

### Module Not Found

**Error**: `Cannot find module '@/components/ui/button'`

**Solution**: Reinstall dependencies:
```bash
rm -rf node_modules pnpm-lock.yaml
pnpm install
```

### OAuth Configuration Issues

**Error**: `Invalid OAuth callback URL`

**Solution**: Ensure `VITE_OAUTH_PORTAL_URL` matches your Manus OAuth configuration. For local development, use:
```env
VITE_OAUTH_PORTAL_URL=http://localhost:3000
```

### S3 Storage Issues

**Error**: `Storage upload failed (403 Forbidden)`

**Solution**: Verify S3 credentials:
```bash
# Check if credentials are set
echo $BUILT_IN_FORGE_API_KEY
echo $BUILT_IN_FORGE_API_URL

# Verify S3 bucket permissions
# Contact Manus support if issues persist
```

## Production Setup

### Prerequisites

- Ubuntu 22.04 LTS server
- 2GB+ RAM
- 20GB+ disk space
- Domain name (optional)
- SSL certificate (recommended)

### Deployment Steps

#### 1. Server Preparation

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y curl wget git build-essential

# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt install -y nodejs

# Install pnpm
npm install -g pnpm
```

#### 2. Clone and Setup

```bash
# Clone repository
git clone https://github.com/Baronki/kinfp-portal.git
cd kinfp-portal

# Install dependencies
pnpm install

# Create .env file with production values
nano .env
```

#### 3. Database Setup

```bash
# Use TiDB Cloud for production (recommended)
# Or install MySQL with proper security:

sudo apt install mysql-server
sudo mysql_secure_installation

# Create production database
mysql -u root -p << EOF
CREATE DATABASE kinfp_portal;
CREATE USER 'kinfp_prod'@'localhost' IDENTIFIED BY 'strong_password_here';
GRANT ALL PRIVILEGES ON kinfp_portal.* TO 'kinfp_prod'@'localhost';
FLUSH PRIVILEGES;
EOF

# Run migrations
pnpm db:push
```

#### 4. Build Application

```bash
# Build frontend and backend
pnpm build

# Output will be in dist/ directory
```

#### 5. Start with PM2 (Process Manager)

```bash
# Install PM2 globally
npm install -g pm2

# Start application
pm2 start dist/index.js --name "kinfp-portal"

# Save PM2 configuration
pm2 save

# Enable auto-restart on reboot
pm2 startup
```

#### 6. Configure Reverse Proxy (Nginx)

```bash
# Install Nginx
sudo apt install nginx

# Create Nginx configuration
sudo nano /etc/nginx/sites-available/kinfp-portal
```

Add the following configuration:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL certificates (use Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # Proxy to Node.js application
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

Enable the configuration:

```bash
# Create symbolic link
sudo ln -s /etc/nginx/sites-available/kinfp-portal /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
```

#### 7. SSL Certificate (Let's Encrypt)

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot certonly --nginx -d your-domain.com

# Auto-renewal
sudo systemctl enable certbot.timer
```

### Monitoring

```bash
# View application logs
pm2 logs kinfp-portal

# Monitor system resources
pm2 monit

# Check application status
pm2 status
```

## Manus WebDev Deployment

KINFP-Portal is pre-configured for deployment on Manus WebDev:

1. **Create Checkpoint**: Save your changes with `webdev_save_checkpoint`
2. **Publish**: Click "Publish" button in Manus Management UI
3. **Custom Domain**: Configure in Settings → Domains
4. **Environment Variables**: Set in Settings → Secrets

## Backup & Recovery

### Database Backup

```bash
# Backup MySQL database
mysqldump -u kinfp_user -p kinfp_portal > backup.sql

# Restore from backup
mysql -u kinfp_user -p kinfp_portal < backup.sql
```

### Application Backup

```bash
# Backup entire project
tar -czf kinfp-portal-backup.tar.gz kinfp-portal/

# Restore from backup
tar -xzf kinfp-portal-backup.tar.gz
```

## Performance Tuning

### Database Optimization

```sql
-- Add indexes for frequently queried columns
ALTER TABLE files ADD INDEX idx_userId (userId);
ALTER TABLE files ADD INDEX idx_category (category);
ALTER TABLE files ADD INDEX idx_uploadedAt (uploadedAt);

-- Check query performance
EXPLAIN SELECT * FROM files WHERE userId = 1;
```

### Application Optimization

```bash
# Enable compression in Nginx
gzip on;
gzip_types text/plain text/css application/json application/javascript;

# Increase Node.js memory limit
NODE_OPTIONS="--max-old-space-size=2048" pnpm start
```

## Support & Resources

- **GitHub Issues**: [Report bugs](https://github.com/Baronki/kinfp-portal/issues)
- **Documentation**: See `/docs` directory
- **Email**: info@kinfp.io
- **Manus Support**: [help.manus.im](https://help.manus.im)

---

**Last Updated**: March 4, 2026  
**Version**: 13.0  
**Status**: Production Ready
