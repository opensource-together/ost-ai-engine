# GitHub Scraper Service Makefile

.PHONY: help build test clean lint format deps run

# Default target
help:
	@echo "Available targets:"
	@echo "  build   - Build the application"
	@echo "  test    - Run tests"
	@echo "  clean   - Clean build artifacts"
	@echo "  lint    - Run linters"
	@echo "  format  - Format code"
	@echo "  deps    - Download dependencies"
	@echo "  run     - Run the application"

# Build the application
build:
	@echo "🔨 Building GitHub scraper..."
	go build -ldflags="-s -w" -o main .
	@echo "✅ Build completed"

# Run tests
test:
	@echo "🧪 Running tests..."
	go test -v ./...
	@echo "✅ Tests completed"

# Clean build artifacts
clean:
	@echo "🧹 Cleaning build artifacts..."
	rm -f main
	go clean -cache
	@echo "✅ Clean completed"

# Run linters
lint:
	@echo "🔍 Running linters..."
	golangci-lint run
	@echo "✅ Linting completed"

# Format code
format:
	@echo "🎨 Formatting code..."
	go fmt ./...
	goimports -w .
	@echo "✅ Formatting completed"

# Download dependencies
deps:
	@echo "📦 Downloading dependencies..."
	go mod tidy
	go mod download
	@echo "✅ Dependencies updated"

# Run the application with default settings
run: build
	@echo "🚀 Running GitHub scraper..."
	./main --query "language:go stars:>100" --max-repos 5

# Run with custom settings
run-custom: build
	@echo "🚀 Running with custom settings..."
	./main --query "language:python stars:>500" --max-repos 10

# Install development tools
install-tools:
	@echo "🛠️ Installing development tools..."
	go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest
	go install golang.org/x/tools/cmd/goimports@latest
	@echo "✅ Tools installed"

# Performance benchmark
bench:
	@echo "⚡ Running performance benchmarks..."
	go test -bench=. -benchmem ./...
	@echo "✅ Benchmarks completed"

# Security scan
security:
	@echo "🔒 Running security scan..."
	gosec ./...
	@echo "✅ Security scan completed"
