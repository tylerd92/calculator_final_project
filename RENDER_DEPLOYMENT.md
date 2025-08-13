# Render Deployment Guide

## Overview
This guide covers deploying the Calculator API to Render, a cloud platform that simplifies deployment.

## Prerequisites
1. Render account (sign up at render.com)
2. GitHub repository with your code
3. Basic understanding of environment variables

## Deployment Steps

### 1. Database Setup
1. In Render dashboard, create a new PostgreSQL database:
   - Go to "New" → "PostgreSQL"
   - Name: `calculator-db`
   - Plan: Free (or Starter for production)
   - Region: Choose closest to your users

2. Note the connection details (Render will provide these automatically)

### 2. Web Service Setup
1. In Render dashboard, create a new Web Service:
   - Go to "New" → "Web Service"
   - Connect your GitHub repository
   - Name: `calculator-app`
   - Environment: `Python 3`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `./start.sh`

### 3. Environment Variables
Set these in your Render Web Service environment variables:

**Required Variables:**
- `ENVIRONMENT`: `production`
- `DATABASE_URL`: Link to your PostgreSQL database (use "Add from Database")
- `JWT_SECRET_KEY`: Generate a secure random string
- `JWT_REFRESH_SECRET_KEY`: Generate another secure random string
- `CORS_ORIGINS`: `https://your-app-name.onrender.com`

**Optional Variables:**
- `LOG_LEVEL`: `INFO`
- `ACCESS_TOKEN_EXPIRE_MINUTES`: `30`
- `REFRESH_TOKEN_EXPIRE_DAYS`: `7`
- `BCRYPT_ROUNDS`: `12`

### 4. Automatic Deployment
1. Render will automatically deploy when you push to your main branch
2. You can also manually trigger deployments from the dashboard

## Key Differences from Docker Deployment

### What Render Handles Automatically:
- **SSL/TLS certificates**: Automatic HTTPS with valid certificates
- **Load balancing**: Built-in load balancing and scaling
- **Health checks**: Uses your `/health` endpoint automatically
- **Environment management**: Web-based environment variable management
- **Database backups**: Automatic PostgreSQL backups (on paid plans)
- **Monitoring**: Basic monitoring and logging included

### What You Don't Need:
- ❌ Docker containers
- ❌ Nginx configuration
- ❌ SSL certificate management
- ❌ Docker Compose orchestration
- ❌ Manual server management
- ❌ Load balancer setup

### What Changes:
- ✅ Single application deployment (no multi-container setup)
- ✅ Environment variables via web dashboard
- ✅ Database as a separate managed service
- ✅ Automatic scaling based on traffic
- ✅ Zero-downtime deployments

## Testing Your Deployment

1. **Health Check**: Visit `https://your-app-name.onrender.com/health`
2. **API Documentation**: Visit `https://your-app-name.onrender.com/docs`
3. **Web Interface**: Visit `https://your-app-name.onrender.com`

## Environment Variables Guide

### Setting JWT Secrets
Generate secure random strings for JWT secrets:

```bash
# Generate JWT secrets (run these locally)
python -c "import secrets; print('JWT_SECRET_KEY:', secrets.token_urlsafe(32))"
python -c "import secrets; print('JWT_REFRESH_SECRET_KEY:', secrets.token_urlsafe(32))"
```

### Database Connection
- Render automatically provides `DATABASE_URL`
- No need to set individual database parameters
- Connection pooling is handled by Render

### CORS Configuration
Update `CORS_ORIGINS` with your actual Render URL:
```
https://your-app-name.onrender.com
```

## Monitoring and Logs

### Viewing Logs
1. Go to your service in Render dashboard
2. Click "Logs" tab
3. View real-time application logs

### Metrics
- Render provides basic metrics (requests, response times, errors)
- Available in the "Metrics" tab of your service

## Production Considerations

### Performance
- **Free tier**: Spins down after 15 minutes of inactivity
- **Paid tiers**: Always-on, better performance
- **Database**: Consider upgrading database plan for production

### Security
- Render provides automatic HTTPS
- Environment variables are encrypted
- Regular security updates

### Scaling
- Render can auto-scale based on traffic
- Configure scaling in service settings

## Troubleshooting

### Common Issues

1. **Build Failures**:
   - Check build logs in Render dashboard
   - Verify `requirements.txt` is correct
   - Ensure `start.sh` is executable

2. **Database Connection Errors**:
   - Verify `DATABASE_URL` is linked correctly
   - Check database service is running
   - Review connection string format

3. **Environment Variable Issues**:
   - Ensure all required variables are set
   - Check for typos in variable names
   - Verify JWT secrets are properly generated

4. **CORS Errors**:
   - Update `CORS_ORIGINS` with correct Render URL
   - Check for `https://` prefix

### Getting Help
- Check Render documentation: docs.render.com
- Review application logs in Render dashboard
- Test endpoints individually to isolate issues

## Migration from Docker Setup

If migrating from your current Docker setup:

1. **Database**: Export data from current PostgreSQL and import to Render database
2. **Environment Variables**: Transfer from `.env.production` to Render dashboard
3. **Static Files**: Ensure `static/` directory is included in repository
4. **Templates**: Ensure `templates/` directory is included in repository

## Cost Considerations

### Free Tier Limitations:
- 750 hours/month (enough for development/testing)
- Services sleep after 15 minutes of inactivity
- Limited database storage

### Paid Tiers:
- Always-on services
- Better performance
- More database storage and features
- Priority support

Choose based on your usage requirements and budget.
