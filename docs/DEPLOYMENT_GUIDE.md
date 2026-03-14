# LifeRPG Production Deployment Guide

This comprehensive guide covers deploying LifeRPG to production environments with security, scalability, and cost optimization in mind.

## Deployment Options Overview

### Free Tier Options (Perfect for Students)

1. **Frontend**: Vercel/Netlify (Free tier)
2. **Backend**: Railway/Render (Free tier with limitations)
3. **Database**: SQLite (file-based, included)
4. **Monitoring**: Built-in health checks

### Low-Cost Options ($5-15/month)

1. **VPS**: DigitalOcean Droplet, Linode, Vultr
2. **Platform**: Railway Pro, Render Pro
3. **Container**: Docker on cloud VPS

### Production-Ready Options ($20-50/month)

1. **Cloud**: AWS/GCP/Azure with proper scaling
2. **Database**: Managed PostgreSQL
3. **CDN**: CloudFlare Pro
4. **Monitoring**: External monitoring services

---

## Quick Start: Free Deployment

### Option 1: Vercel + Railway (Recommended for Students)

#### Step 1: Prepare Repository

```bash
# Ensure all code is committed and pushed
git add .
git commit -m "Production deployment preparation"
git push origin master
```

#### Step 2: Deploy Frontend to Vercel

1. Go to [vercel.com](https://vercel.com)
2. Connect your GitHub repository
3. Configure build settings:
   ```
   Framework: Create React App
   Root Directory: modern/frontend
   Build Command: npm run build
   Output Directory: build
   ```
4. Add environment variables:
   ```
   REACT_APP_API_URL=https://your-backend.railway.app
   REACT_APP_ENVIRONMENT=production
   ```

#### Step 3: Deploy Backend to Railway

1. Go to [railway.app](https://railway.app)
2. Create new project from GitHub
3. Configure:
   ```
   Root Directory: modern/backend
   Start Command: uvicorn app:app --host 0.0.0.0 --port $PORT
   ```
4. Add environment variables:
   ```
   ENVIRONMENT=production
   SECRET_KEY=your-secure-secret-key
   DATABASE_URL=sqlite:///production.db
   CORS_ORIGINS=["https://your-app.vercel.app"]
   ```

### Option 2: Netlify + Render

#### Frontend (Netlify)

1. Go to [netlify.com](https://netlify.com)
2. Connect GitHub repository
3. Build settings:
   ```
   Publish directory: modern/frontend/build
   Build command: cd modern/frontend && npm install && npm run build
   ```

#### Backend (Render)

1. Go to [render.com](https://render.com)
2. Create Web Service
3. Settings:
   ```
   Root Directory: modern/backend
   Build Command: pip install -r requirements.txt
   Start Command: uvicorn app:app --host 0.0.0.0 --port $PORT
   ```

---

## Docker Deployment

### Complete Docker Setup

#### 1. Production Dockerfile (Backend)

```dockerfile
# modern/backend/Dockerfile.prod
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt requirements_ai.txt ./
RUN pip install --no-cache-dir -r requirements_ai.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -r appuser && chown appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health/ || exit 1

EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 2. Production docker-compose.yml

```yaml
version: "3.8"

services:
  backend:
    build:
      context: ./modern/backend
      dockerfile: Dockerfile.prod
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=production
      - DATABASE_URL=sqlite:///data/production.db
      - SECRET_KEY=${SECRET_KEY}
    volumes:
      - ./data:/app/data
      - ./ai_models:/app/ai_models
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health/"]
      interval: 30s
      timeout: 10s
      retries: 3

  frontend:
    build:
      context: ./modern/frontend
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      - REACT_APP_API_URL=http://localhost:8000
    depends_on:
      - backend
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - frontend
      - backend
    restart: unless-stopped
```

#### 3. Nginx Configuration

```nginx
# nginx.conf
events {
    worker_connections 1024;
}

http {
    upstream backend {
        server backend:8000;
    }

    upstream frontend {
        server frontend:3000;
    }

    server {
        listen 80;
        server_name your-domain.com;

        # Redirect to HTTPS
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl;
        server_name your-domain.com;

        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;

        # Frontend
        location / {
            proxy_pass http://frontend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }

        # Backend API
        location /api {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        }

        # Health checks
        location /health {
            proxy_pass http://backend;
        }
    }
}
```

---

## VPS Deployment (DigitalOcean/Linode)

### 1. Server Setup

```bash
# Create and connect to VPS
ssh root@your-server-ip

# Update system
apt update && apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
systemctl start docker
systemctl enable docker

# Install Docker Compose
pip3 install docker-compose

# Install other tools
apt install -y git nginx certbot python3-certbot-nginx
```

### 2. Deploy Application

```bash
# Clone repository
git clone https://github.com/yourusername/LifeRPG.git
cd LifeRPG

# Create environment file
cat > .env << EOF
SECRET_KEY=$(openssl rand -hex 32)
ENVIRONMENT=production
DATABASE_URL=sqlite:///data/production.db
REACT_APP_API_URL=https://your-domain.com
EOF

# Create data directory
mkdir -p data ai_models

# Start services
docker-compose -f docker-compose.prod.yml up -d
```

### 3. SSL Setup with Let's Encrypt

```bash
# Get SSL certificate
certbot --nginx -d your-domain.com

# Auto-renewal
crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

---

## Monitoring and Maintenance

### Health Monitoring Script

```bash
#!/bin/bash
# monitoring/health-check.sh

BACKEND_URL="https://your-domain.com"
SLACK_WEBHOOK="your-slack-webhook-url"

# Check backend health
if ! curl -f "$BACKEND_URL/api/v1/health/" > /dev/null 2>&1; then
    echo "Backend health check failed"
    curl -X POST -H 'Content-type: application/json' \
        --data '{"text":"🚨 LifeRPG Backend is down!"}' \
        $SLACK_WEBHOOK
fi

# Check disk space
DISK_USAGE=$(df / | grep -vE '^Filesystem' | awk '{print $5}' | sed 's/%//g')
if [ $DISK_USAGE -gt 80 ]; then
    echo "High disk usage: ${DISK_USAGE}%"
fi
```

### Backup Script

```bash
#!/bin/bash
# scripts/backup.sh

BACKUP_DIR="/backups"
DB_FILE="data/production.db"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup database
cp $DB_FILE "$BACKUP_DIR/liferpg_db_$DATE.db"

# Backup user uploads (if any)
tar -czf "$BACKUP_DIR/uploads_$DATE.tar.gz" uploads/

# Keep only last 30 days of backups
find $BACKUP_DIR -name "*.db" -mtime +30 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete

echo "Backup completed: $DATE"
```

---

## Security Checklist

### Essential Security Measures

#### 1. Environment Security

- [ ] Strong SECRET_KEY in production
- [ ] Environment variables for all secrets
- [ ] No hardcoded credentials in code
- [ ] HTTPS enabled with valid certificates
- [ ] CORS properly configured

#### 2. Application Security

- [ ] Input validation on all endpoints
- [ ] Rate limiting implemented
- [ ] Authentication required for sensitive operations
- [ ] SQL injection prevention (using parameterized queries)
- [ ] XSS prevention in frontend

#### 3. Server Security

- [ ] Firewall configured (only necessary ports open)
- [ ] SSH key authentication (disable password auth)
- [ ] Regular system updates
- [ ] Non-root user for application
- [ ] Log monitoring set up

#### 4. Database Security

- [ ] Database file permissions restricted
- [ ] Regular backups
- [ ] Backup encryption for sensitive data

---

## Performance Optimization

### Backend Optimization

1. **Enable Compression**

   ```python
   from fastapi.middleware.gzip import GZipMiddleware
   app.add_middleware(GZipMiddleware, minimum_size=1000)
   ```

2. **Response Caching**

   ```python
   from fastapi_cache import FastAPICache
   from fastapi_cache.backends.redis import RedisBackend
   ```

3. **AI Model Optimization**
   - Pre-load models on startup
   - Implement model caching
   - Use quantized models for lower memory usage

### Frontend Optimization

1. **Code Splitting**

   ```javascript
   const LazyComponent = React.lazy(() => import("./Component"));
   ```

2. **Service Worker for Caching**
3. **Image Optimization**
4. **Bundle Analysis**

---

## Cost Optimization

### Free Tier Maximization

- **Vercel**: 100GB bandwidth, unlimited sites
- **Railway**: 500 hours/month, $5 credit
- **Render**: 750 hours/month
- **GitHub**: Free hosting for static sites

### Budget Planning ($10-20/month)

- Domain: $12/year
- VPS: $5-10/month
- SSL: Free (Let's Encrypt)
- CDN: Free (CloudFlare)

### Scaling Strategy

1. **Start Free**: Use free tiers
2. **Grow Smart**: Upgrade one service at a time
3. **Monitor Usage**: Use built-in analytics
4. **Optimize First**: Before upgrading resources

---

## Troubleshooting

### Common Issues

#### Build Failures

```bash
# Clear caches
npm cache clean --force
pip cache purge

# Rebuild containers
docker-compose down
docker-compose build --no-cache
```

#### Memory Issues

```bash
# Check memory usage
free -h
docker stats

# Restart services
docker-compose restart
```

#### SSL Certificate Issues

```bash
# Renew certificates
certbot renew --dry-run
certbot renew

# Check certificate status
certbot certificates
```

---

## Support and Maintenance

### Regular Maintenance Tasks

- [ ] Weekly: Check application logs
- [ ] Weekly: Verify backups
- [ ] Monthly: Update dependencies
- [ ] Monthly: Review security logs
- [ ] Quarterly: Performance review
- [ ] Quarterly: Cost optimization review

### Emergency Response Plan

1. **Monitor alerts** (health checks, error rates)
2. **Incident response** (restart services, check logs)
3. **Communication** (user notifications if needed)
4. **Post-incident** (root cause analysis, prevention)

---

## Student-Specific Tips

### Academic Projects

- Use `.edu` domain for free services
- GitHub Student Pack benefits
- AWS/GCP/Azure education credits
- Free SSL certificates through GitHub Pages

### Portfolio Enhancement

- Custom domain for professionalism
- Performance metrics documentation
- User feedback and testimonials
- Technical blog posts about the project

### Learning Opportunities

- Infrastructure as Code (Terraform)
- CI/CD pipeline improvements
- Monitoring and observability
- Security best practices implementation

---

This deployment guide provides multiple pathways from free student hosting to production-ready infrastructure. Choose the approach that matches your current needs and budget, with clear upgrade paths as your project grows.
