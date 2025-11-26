# DynamoDB Backend

The DynamoDB backend provides scalable cloud storage using AWS DynamoDB.

## Overview

DynamoDB is ideal for:

- Cloud-native deployments
- Distributed crawling systems
- High availability requirements
- Serverless architectures

## Installation

Install with DynamoDB support:

```bash
pip install ragcrawl[dynamodb]
```

## Configuration

```python
from ragcrawl.config.storage_config import StorageConfig, DynamoDBConfig

config = StorageConfig(
    backend=DynamoDBConfig(
        table_prefix="ragcrawl_",
        region="us-west-2",
        endpoint_url=None,  # Use for local DynamoDB
    )
)
```

### Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `table_prefix` | str | `"ragcrawl_"` | Prefix for table names |
| `region` | str | `"us-east-1"` | AWS region |
| `endpoint_url` | str | `None` | Custom endpoint (for local) |

## AWS Credentials

The backend uses standard AWS credential resolution:

1. Environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`)
2. AWS credentials file (`~/.aws/credentials`)
3. IAM role (for EC2/Lambda)

## Usage

### Basic Usage

```python
from ragcrawl.storage import create_storage_backend

backend = create_storage_backend(config)
backend.initialize()  # Creates tables if needed

sites = backend.list_sites()
backend.close()
```

### Local Development

Use DynamoDB Local for development:

```bash
# Start DynamoDB Local
docker run -p 8000:8000 amazon/dynamodb-local
```

```python
config = StorageConfig(
    backend=DynamoDBConfig(
        table_prefix="dev_",
        region="us-east-1",
        endpoint_url="http://localhost:8000",
    )
)
```

## Table Structure

### Tables Created

| Table | Partition Key | Sort Key | Description |
|-------|--------------|----------|-------------|
| `{prefix}sites` | `site_id` | - | Site records |
| `{prefix}runs` | `site_id` | `run_id` | Crawl runs |
| `{prefix}pages` | `site_id` | `page_id` | Pages |
| `{prefix}versions` | `page_id` | `version_id` | Content versions |
| `{prefix}frontier` | `run_id` | `item_id` | Queue items |

### Global Secondary Indexes

- `runs`: GSI on `run_id` for direct lookup
- `pages`: GSI on `url` for URL lookups

## IAM Permissions

Required IAM permissions:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "dynamodb:CreateTable",
                "dynamodb:DescribeTable",
                "dynamodb:GetItem",
                "dynamodb:PutItem",
                "dynamodb:UpdateItem",
                "dynamodb:DeleteItem",
                "dynamodb:Query",
                "dynamodb:Scan"
            ],
            "Resource": "arn:aws:dynamodb:*:*:table/ragcrawl_*"
        }
    ]
}
```

## Cost Optimization

### On-Demand vs Provisioned

By default, tables use on-demand capacity. For predictable workloads, consider provisioned capacity:

```python
# Set via AWS Console or CLI after table creation
aws dynamodb update-table \
    --table-name ragcrawl_pages \
    --billing-mode PROVISIONED \
    --provisioned-throughput ReadCapacityUnits=100,WriteCapacityUnits=50
```

### TTL for Frontier Items

Enable TTL on frontier table to auto-delete old items:

```python
# Frontier items can be cleaned up after run completion
```

## API Reference

::: ragcrawl.storage.dynamodb.backend.DynamoDBBackend
    options:
      show_root_heading: true
      members:
        - __init__
        - initialize
        - close
        - health_check
