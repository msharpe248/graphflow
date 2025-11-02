# Contributing to GraphFlow

Thank you for your interest in contributing to GraphFlow! This document provides guidelines and instructions for contributing.

## Getting Started

1. **Fork the repository**
2. **Clone your fork**
   ```bash
   git clone https://github.com/your-username/graphflow.git
   cd graphflow
   ```
3. **Set up development environment**
   ```bash
   # Python packages
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -e packages/graph-core
   pip install -e packages/graph-compiler
   pip install -e packages/graph-runtime

   # UI (optional)
   cd packages/graph-builder
   npm install
   ```

## Development Workflow

### Making Changes

1. **Create a branch** for your feature or bugfix
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following our coding standards

3. **Test your changes**
   ```bash
   # Test Python packages
   pytest packages/graph-core
   pytest packages/graph-compiler
   pytest packages/graph-runtime

   # Test end-to-end
   python test_end_to_end.py

   # Test UI
   cd packages/graph-builder
   npm run build
   ```

4. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

### Commit Message Format

Use conventional commits:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `refactor:` Code refactoring
- `test:` Adding tests
- `chore:` Maintenance tasks

### Pull Request Process

1. **Update documentation** if needed
2. **Ensure all tests pass**
3. **Update CHANGELOG.md** with your changes
4. **Submit pull request** with clear description

## Code Standards

### Python

- Follow PEP 8 style guide
- Use type hints where appropriate
- Add docstrings for public functions/classes
- Keep functions focused and small

### TypeScript/React

- Use TypeScript for all new code
- Follow React best practices
- Use functional components with hooks
- Keep components small and focused

### Documentation

- Update README.md if adding features
- Add inline comments for complex logic
- Update API documentation in docstrings

## Adding New Features

### New Step Types

1. Create step class in `packages/graph-core/graphflow_core/steps/`
2. Register with `@StepRegistry.register()`
3. Add to `stepTypes.ts` in UI
4. Update templates in compiler if needed
5. Add tests

### New Compilers

1. Create generator in `packages/graph-compiler/graphflow_compiler/generators/`
2. Extend `CodeGenerator` base class
3. Create Jinja2 templates
4. Register in `CompilerRegistry`
5. Add tests

### UI Components

1. Create component in `packages/graph-builder/src/components/`
2. Follow existing patterns
3. Use TypeScript
4. Add to appropriate view

## Testing

### Unit Tests
```bash
pytest packages/graph-core/tests/
pytest packages/graph-compiler/tests/
```

### Integration Tests
```bash
python test_end_to_end.py
```

### UI Tests
```bash
cd packages/graph-builder
npm run test  # When added
```

## Questions?

- Open an issue for bugs or feature requests
- Start a discussion for questions or ideas
- Join our community (links TBD)

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
