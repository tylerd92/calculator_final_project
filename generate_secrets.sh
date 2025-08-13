#!/bin/bash

# Script to generate secure secrets for production deployment

echo "🔐 Generating production secrets..."

# Function to generate random string
generate_secret() {
    openssl rand -base64 32 | tr -d "=+/" | cut -c1-32
}

# Generate secrets
POSTGRES_PASSWORD=$(generate_secret)
JWT_SECRET_KEY=$(generate_secret)
JWT_REFRESH_SECRET_KEY=$(generate_secret)

echo ""
echo "📝 Generated secrets (save these securely):"
echo "=========================================="
echo "POSTGRES_PASSWORD=$POSTGRES_PASSWORD"
echo "JWT_SECRET_KEY=$JWT_SECRET_KEY"
echo "JWT_REFRESH_SECRET_KEY=$JWT_REFRESH_SECRET_KEY"
echo ""
echo "⚠️  Update your .env.production file with these values!"
echo "⚠️  Also update CORS_ORIGINS with your actual domain(s)"
echo ""

# Optionally create/update .env.production file
read -p "Do you want to update .env.production automatically? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if [ -f ".env.production" ]; then
        # Backup existing file
        cp .env.production .env.production.backup
        echo "📄 Backed up existing .env.production to .env.production.backup"
    fi
    
    # Update the file
    sed -i "s/POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=$POSTGRES_PASSWORD/" .env.production
    sed -i "s/JWT_SECRET_KEY=.*/JWT_SECRET_KEY=$JWT_SECRET_KEY/" .env.production
    sed -i "s/JWT_REFRESH_SECRET_KEY=.*/JWT_REFRESH_SECRET_KEY=$JWT_REFRESH_SECRET_KEY/" .env.production
    
    echo "✅ Updated .env.production with new secrets"
    echo "⚠️  Don't forget to update CORS_ORIGINS with your domain!"
fi

echo ""
echo "🔒 Remember:"
echo "  - Keep these secrets secure and private"
echo "  - Don't commit .env.production to version control"
echo "  - Use different secrets for different environments"
