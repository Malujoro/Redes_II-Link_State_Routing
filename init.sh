#!/bin/bash
set -e

echo "Reiniciando o Docker Compose..."
docker compose down
docker compose up
