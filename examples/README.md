# Examples

This directory contains example scripts demonstrating various features of ragcrawl.

## Available Examples

### quickstart_duckdb.py

Basic example showing how to crawl a website with local DuckDB storage.

```bash
python examples/quickstart_duckdb.py
```

Features demonstrated:
- Basic crawler configuration
- DuckDB storage setup
- Multi-page output
- JSON export

### sync_example.py

Shows how to perform incremental syncs to keep your knowledge base updated.

```bash
python examples/sync_example.py
```

Features demonstrated:
- Initial crawl
- Incremental sync
- Change detection

### chunking_for_rag.py

Demonstrates how to chunk documents for RAG (Retrieval-Augmented Generation) systems.

```bash
python examples/chunking_for_rag.py
```

Features demonstrated:
- Heading-based chunking
- Token-based chunking
- Export for vector databases

### dynamodb_setup.py

Shows how to use DynamoDB for cloud-based storage.

```bash
# With AWS credentials
python examples/dynamodb_setup.py

# With DynamoDB Local
docker run -p 8000:8000 amazon/dynamodb-local
USE_DYNAMODB_LOCAL=true python examples/dynamodb_setup.py
```

Features demonstrated:
- DynamoDB configuration
- Cloud storage setup
- Data querying

### hooks_and_callbacks.py

Demonstrates using hooks for monitoring and content filtering.

```bash
python examples/hooks_and_callbacks.py
```

Features demonstrated:
- Progress monitoring
- Error handling
- Content redaction
- Custom content filters

## Running the Examples

1. Install the package:
   ```bash
   pip install -e ".[all]"
   ```

2. Run an example:
   ```bash
   python examples/<example_name>.py
   ```

3. Check the output:
   - `.duckdb` files: Local database storage
   - `*_output/`: Generated Markdown files
   - `.json`/`.jsonl`: Exported data

## Customizing Examples

Feel free to modify the examples to:
- Change seed URLs to your target site
- Adjust crawl limits (max_pages, max_depth)
- Try different output modes
- Add custom hooks and filters
