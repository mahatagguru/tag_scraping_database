# Docker Hub Setup Guide

This guide explains how to set up Docker Hub integration for your TAG Grading Scraper project.

## 🚀 Why Docker Hub?

Since GitHub Container Registry (ghcr.io) requires special permissions that your account doesn't have, we're switching to Docker Hub which is:
- ✅ **Easier to set up** - Standard Docker registry
- ✅ **Better free tier** - More generous limits
- ✅ **Widely supported** - Works with all Docker tools
- ✅ **No permission issues** - Standard account access

## 🔧 Setup Steps

### 1. Create Docker Hub Account

1. Go to [hub.docker.com](https://hub.docker.com)
2. Sign up for a free account
3. Verify your email address

### 2. Create Access Token

1. Log into Docker Hub
2. Go to **Account Settings** → **Security**
3. Click **New Access Token**
4. Give it a name (e.g., "GitHub Actions")
5. Copy the token (you'll need it for GitHub secrets)

### 3. Set GitHub Secrets

In your GitHub repository, go to **Settings** → **Secrets and variables** → **Actions** and add:

```
DOCKERHUB_USERNAME = your_dockerhub_username
DOCKERHUB_TOKEN = your_access_token
```

### 4. Update Repository Settings

The workflow will now push to:
```
docker.io/mahatagguru/tag-scraping-tool:main
docker.io/mahatagguru/tag-scraping-tool:develop
docker.io/mahatagguru/tag-scraping-tool:latest
```

## 📋 What Changed

### Before (GitHub Container Registry):
```yaml
env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}
```

### After (Docker Hub):
```yaml
env:
  REGISTRY: docker.io
  IMAGE_NAME: mahatagguru/tag-scraping-tool
```

## 🐳 Using the Images

### Pull from Docker Hub:
```bash
docker pull mahatagguru/tag-scraping-tool:latest
docker pull mahatagguru/tag-scraping-tool:main
```

### Run the container:
```bash
docker run -p 8000:8000 mahatagguru/tag-scraping-tool:latest
```

### Use in docker-compose:
```yaml
version: '3.8'
services:
  tag-scraper:
    image: mahatagguru/tag-scraping-tool:latest
    ports:
      - "8000:8000"
```

## 🔍 Troubleshooting

### Common Issues:

1. **Authentication Failed**
   - Check `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN` secrets
   - Ensure the access token is valid and not expired

2. **Push Denied**
   - Verify your Docker Hub account has permission to push
   - Check if the repository name matches your Docker Hub username

3. **Rate Limiting**
   - Docker Hub free tier has rate limits
   - Consider upgrading for production use

## 🚀 Benefits of This Setup

- ✅ **No permission issues** - Standard Docker Hub access
- ✅ **Better integration** - Works with all Docker tools
- ✅ **Public images** - Easy to share and distribute
- ✅ **CI/CD ready** - Seamless GitHub Actions integration
- ✅ **Version control** - Tagged releases for different branches

## 📚 Additional Resources

- [Docker Hub Documentation](https://docs.docker.com/docker-hub/)
- [GitHub Actions Docker Login](https://github.com/docker/login-action)
- [Docker Hub Rate Limits](https://docs.docker.com/docker-hub/download-rate-limit/)

---

**Your Docker images will now be available at: `docker.io/mahatagguru/tag-scraping-tool`** 🐳✨
