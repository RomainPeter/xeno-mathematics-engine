# Running with Docker

This document explains how to build and run the xeno-mathematics-engine using Docker.

## Prerequisites

- Docker installed on your system
- Git (to clone the repository)

## Building the Docker Image

From the project root directory:

```bash
docker build -t xme/dev:latest .
```

This will:
1. Use the multi-stage Dockerfile with Nix
2. Build the xme CLI tool
3. Create a minimal runtime image

## Running the Container

### Basic Usage

```bash
docker run --rm xme/dev:latest
```

This will show the help message for the xme CLI tool.

### Interactive Mode

```bash
docker run -it --rm xme/dev:latest bash
```

This will give you an interactive shell inside the container.

### Mounting Data

To work with local files:

```bash
docker run -it --rm -v $(pwd):/workspace xme/dev:latest
```

### Custom Commands

```bash
docker run --rm xme/dev:latest --version
docker run --rm xme/dev:latest --help
```

## Development

### Building for Development

```bash
docker build -t xme/dev:latest .
```

### Testing the Build

```bash
# Test that the image builds successfully
docker build -t xme/dev:latest .

# Test that the CLI works
docker run --rm xme/dev:latest --help

# Test with a specific command
docker run --rm xme/dev:latest --version
```

## CI/CD Integration

The Docker image is automatically built in the GitHub Actions CI pipeline:

- **Trigger**: On every push and pull request
- **Job**: `docker-build`
- **Registry**: Currently builds locally (not pushed to registry)
- **Attestation**: Optional cosign attestation when `COSIGN_KEY` secret is set

## Security

The Docker image uses:
- **Base**: `nixpkgs/nix:latest` for reproducible builds
- **Multi-stage**: Separate build and runtime stages
- **Minimal**: Only includes necessary runtime dependencies
- **Signed**: Optional cosign attestation for supply chain security

## Troubleshooting

### Build Issues

If the build fails:
1. Check that you have Docker installed
2. Ensure you're in the project root directory
3. Check that all required files are present

### Runtime Issues

If the container doesn't start:
1. Check that the image was built successfully
2. Verify the entrypoint is correct
3. Check Docker logs: `docker logs <container_id>`

### Permission Issues

On Linux/macOS, you might need to adjust file permissions:
```bash
chmod +x scripts/verify_2cat_pack.sh
```

## Advanced Usage

### Custom Nix Configuration

You can override the Nix configuration by mounting a custom `nix.conf`:

```bash
docker run -v /path/to/custom/nix.conf:/etc/nix/nix.conf xme/dev:latest
```

### Environment Variables

Set environment variables for the container:

```bash
docker run -e XME_CONFIG_PATH=/config xme/dev:latest
```

### Resource Limits

Limit container resources:

```bash
docker run --memory=1g --cpus=2 xme/dev:latest
```
