#!/bin/bash
# Generate self-signed SSL certificates for GraphFlow development
#
# Usage:
#   ./scripts/generate-certs.sh                    # Use default .certs directory
#   GRAPHFLOW_CERT_DIR=/custom/path ./scripts/generate-certs.sh
#
# Environment variables:
#   GRAPHFLOW_CERT_DIR  - Directory to store certificates (default: .certs)
#   GRAPHFLOW_CERT_DAYS - Certificate validity in days (default: 365)
#   GRAPHFLOW_CERT_CN   - Common Name for certificate (default: localhost)

set -e

# Configuration with defaults
CERT_DIR="${GRAPHFLOW_CERT_DIR:-.certs}"
CERT_DAYS="${GRAPHFLOW_CERT_DAYS:-365}"
CERT_CN="${GRAPHFLOW_CERT_CN:-localhost}"

KEY_FILE="$CERT_DIR/graphflow.key"
CERT_FILE="$CERT_DIR/graphflow.crt"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Generating self-signed SSL certificates for GraphFlow...${NC}"

# Check for OpenSSL
if ! command -v openssl &> /dev/null; then
    echo -e "${RED}Error: OpenSSL is required but not installed.${NC}"
    exit 1
fi

# Create certificate directory
mkdir -p "$CERT_DIR"

# Check if certificates already exist
if [ -f "$KEY_FILE" ] && [ -f "$CERT_FILE" ]; then
    echo -e "${BLUE}Certificates already exist. Checking validity...${NC}"

    # Check if certificate is still valid
    if openssl x509 -checkend 86400 -noout -in "$CERT_FILE" 2>/dev/null; then
        echo -e "${GREEN}Existing certificates are still valid.${NC}"
        echo "  Key:  $KEY_FILE"
        echo "  Cert: $CERT_FILE"
        echo ""
        echo "To regenerate, delete the existing files first:"
        echo "  rm $KEY_FILE $CERT_FILE"
        exit 0
    else
        echo -e "${BLUE}Certificate expired or expiring soon. Regenerating...${NC}"
    fi
fi

# Generate private key and self-signed certificate
# Using Subject Alternative Name (SAN) for modern browser compatibility
openssl req -x509 -nodes -days "$CERT_DAYS" \
    -newkey rsa:2048 \
    -keyout "$KEY_FILE" \
    -out "$CERT_FILE" \
    -subj "/CN=$CERT_CN" \
    -addext "subjectAltName=DNS:localhost,DNS:$CERT_CN,IP:127.0.0.1,IP:::1" \
    2>/dev/null

# Set proper permissions
chmod 600 "$KEY_FILE"
chmod 644 "$CERT_FILE"

echo -e "${GREEN}Certificates generated successfully!${NC}"
echo ""
echo "  Private key: $KEY_FILE"
echo "  Certificate: $CERT_FILE"
echo "  Valid for:   $CERT_DAYS days"
echo ""
echo "Certificate details:"
openssl x509 -in "$CERT_FILE" -noout -dates -subject 2>/dev/null | sed 's/^/  /'
echo ""
echo -e "${BLUE}Note: For browser access, you may need to:${NC}"
echo "  1. Accept the security warning when first visiting https://localhost"
echo "  2. Or add the certificate to your system trust store"
