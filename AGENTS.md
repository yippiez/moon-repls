## Project Overview

Serverless REPLs organized by language and platform:
```
REPLs/
├── bash/aws/
├── javascript/cloudflare-workers/  
└── python/aws/
```

## Development Environment

DevContainer using `pahud/aws-sam-cli` with SAM CLI, AWS CLI, Python dependencies pre-installed.

**Start container:**
```bash
devcontainer up --workspace-folder .
```

**Run bash REPL tests:**
```bash
devcontainer exec --workspace-folder . python3 REPLs/bash/aws/test.py
```

## Testing Commands

**Bash REPL local testing:**
```bash
cd REPLs/bash/aws && python3 test.py
```
