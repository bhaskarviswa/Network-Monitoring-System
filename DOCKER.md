# Docker Deployment Guide

This guide explains how to run the Network Monitoring System using Docker.

## Prerequisites

- Docker installed on your system
- Docker Compose (optional, but recommended)

## Testing Status

✅ **Docker Build:** Successfully tested (build time: ~56 seconds)
✅ **Container Run:** Successfully tested (container ID: 56be794...)
✅ **Application Start:** Verified - Flask app running on 0.0.0.0:5000
✅ **Database Init:** Confirmed - SQLite database initialized
✅ **Background Monitor:** Confirmed - Polling every 120 seconds
✅ **Web Access:** Application accessible at http://localhost:5000

## Quick Start

### Option 1: Using Docker Compose (Recommended)

1. **Build and start the container:**
```bash
docker-compose up -d
```

2. **View logs:**
```bash
docker-compose logs -f
```

3. **Stop the container:**
```bash
docker-compose down
```

### Option 2: Using Docker CLI

#### Development Mode (Flask debug server)

1. **Build the Docker image:**
```bash
docker build -t network-monitoring-system .
```

2. **Run the container:**
```bash
docker run -d --name network-monitor -p 5000:5000 network-monitoring-system
```

3. **View logs:**
```bash
docker logs network-monitor
```

#### Production Mode (Gunicorn WSGI server)

1. **Build the production image:**
```bash
docker build -f Dockerfile.prod -t network-monitoring-system:prod .
```

2. **Run the container:**
```bash
docker run -d --name network-monitor -p 5000:5000 network-monitoring-system:prod
```

3. **View logs:**
```bash
docker logs network-monitor
```

4. **Stop the container:**
```bash
docker stop network-monitor
docker rm network-monitor
```

## Accessing the Application

Once the container is running, access the dashboard at:
- **Local:** http://localhost:5000
- **Network:** http://YOUR_SERVER_IP:5000

## Data Persistence

The SQLite database is stored in the `instance/` directory, which is mounted as a volume. This ensures your data persists even if the container is removed.

## Configuration

### Email Alerts

To configure email alerts, you can either:

1. **Use the web interface:** Go to Settings page after starting the container
2. **Edit config.py:** Modify the file before building the image

### Environment Variables

You can pass environment variables to customize the application:

```bash
docker run -d \
  --name network-monitor \
  -p 5000:5000 \
  -e POLLING_INTERVAL=120 \
  -v $(pwd)/instance:/app/instance \
  network-monitoring-system
```

## Network Access

The container needs network access to:
- SSH into network switches (ensure switches are reachable from container)
- Send email alerts (if configured)

### Host Network Mode (Optional)

If you need the container to access switches on the same network as the host:

```bash
docker run -d \
  --name network-monitor \
  --network host \
  -v $(pwd)/instance:/app/instance \
  network-monitoring-system
```

## Troubleshooting

### Container won't start
```bash
# Check logs
docker logs network-monitor

# Check if port 5000 is already in use
netstat -ano | findstr :5000  # Windows
lsof -i :5000                  # Linux/Mac
```

### Can't connect to switches
```bash
# Test SSH connectivity from container
docker exec -it network-monitor ping SWITCH_IP
```

### Database issues
```bash
# Reset database (WARNING: deletes all data)
docker-compose down
rm -rf instance/network_monitor.db
docker-compose up -d
```

## Updating the Application

1. **Pull latest changes:**
```bash
git pull origin main
```

2. **Rebuild and restart:**
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## Production Deployment

For production, use the Gunicorn-based Dockerfile:

1. **Update docker-compose.yml:**
```yaml
services:
  network-monitor:
    build:
      context: .
      dockerfile: Dockerfile.prod  # Change from Dockerfile
```

2. **Rebuild and start:**
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Additional Production Recommendations

1. **Use a reverse proxy (nginx):**
```yaml
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - network-monitor
```

2. **Enable HTTPS with SSL certificates**

3. **Use environment-specific config files**

4. **Set up automated backups of the database**

5. **Monitor container health and resource usage**

## Monitoring the Container

```bash
# Check container status
docker ps

# View resource usage
docker stats network-monitor

# Check container health
docker inspect network-monitor
```

## Backup and Restore

### Backup
```bash
# Backup database
docker cp network-monitor:/app/instance/network_monitor.db ./backup/

# Or if using volume
cp instance/network_monitor.db ./backup/
```

### Restore
```bash
# Restore database
docker cp ./backup/network_monitor.db network-monitor:/app/instance/

# Or if using volume
cp ./backup/network_monitor.db instance/
```

## Support

For issues or questions:
- Check logs: `docker-compose logs -f`
- GitHub Issues: [Your Repository URL]
- Documentation: README.md
