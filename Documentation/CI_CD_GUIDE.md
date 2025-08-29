# CI/CD Pipeline Guide

This document provides a comprehensive guide to the CI/CD pipeline implemented for the TAG Grading Scraper project.

## 🚀 Overview

The project implements a complete CI/CD pipeline using GitHub Actions with the following components:

- **Continuous Integration (CI)**: Automated testing, linting, and quality checks
- **Continuous Deployment (CD)**: Automated deployment to staging and production
- **Docker Integration**: Automated container building and publishing
- **Security Scanning**: Vulnerability detection and security analysis
- **Quality Gates**: Automated quality checks and validation

## 📁 Pipeline Structure

```
.github/
├── workflows/
│   ├── ci.yml              # Continuous Integration
│   ├── cd.yml              # Continuous Deployment
│   └── docker.yml          # Docker Build and Publish
├── ISSUE_TEMPLATE/
│   ├── bug_report.md       # Bug report template
│   └── feature_request.md  # Feature request template
└── pull_request_template.md # Pull request template
```

## 🔄 CI Pipeline (ci.yml)

### Triggers
- **Push**: Any push to `main`, `develop`, or `feature/*` branches
- **Pull Request**: Any PR to `main` or `develop` branches
- **Scheduled**: Daily at 2 AM UTC for maintenance

### Jobs

#### 1. Lint and Format Check
- **Purpose**: Ensure code quality and consistency
- **Tools**: Black, isort, flake8, mypy, pylint
- **Output**: Pass/fail with detailed feedback

#### 2. Test with SQLite
- **Purpose**: Run unit tests with SQLite database
- **Coverage**: Generates coverage reports
- **Output**: Test results and coverage metrics

#### 3. Test with PostgreSQL
- **Purpose**: Run unit tests with PostgreSQL database
- **Services**: PostgreSQL 13 container
- **Output**: Test results and coverage metrics

#### 4. Validate Database Schema
- **Purpose**: Verify database schema integrity
- **Tests**: Schema validation and PostgreSQL detection
- **Output**: Validation results and warnings

#### 5. Security Checks
- **Purpose**: Identify security vulnerabilities
- **Tools**: Safety, Bandit
- **Output**: Security reports and artifacts

#### 6. Build Package
- **Purpose**: Create distributable packages
- **Dependencies**: Requires all previous jobs to pass
- **Output**: Build artifacts

#### 7. Quality Gates
- **Purpose**: Final validation and summary
- **Dependencies**: All previous jobs
- **Output**: Quality gate summary

### Configuration

```yaml
env:
  PYTHON_VERSION: '3.9'
  POSTGRES_VERSION: '13'
  SQLITE_VERSION: '3'
```

## 🚀 CD Pipeline (cd.yml)

### Triggers
- **Tags**: Semantic versioning tags (v*.*.*)
- **Workflow Run**: After successful CI completion on main branch

### Jobs

#### 1. Deploy to Staging
- **Trigger**: `develop` branch with successful CI
- **Actions**: Schema validation, deployment tests
- **Output**: Staging deployment status

#### 2. Deploy to Production
- **Trigger**: Version tags (v*.*.*)
- **Actions**: Full production deployment
- **Output**: Production deployment and release

#### 3. Deploy Database Migrations
- **Trigger**: Version tags and develop branch
- **Actions**: Database schema updates
- **Output**: Migration status

#### 4. Rollback Capability
- **Trigger**: Manual workflow dispatch
- **Actions**: Version rollback
- **Output**: Rollback status

### Environment Protection

```yaml
environment: production
```

Production deployments require manual approval and environment protection rules.

## 🐳 Docker Pipeline (docker.yml)

### Triggers
- **Push**: Main and develop branches, version tags
- **Pull Request**: Any PR to main or develop

### Jobs

#### 1. Build and Test Docker Image
- **Purpose**: Create and test container images
- **Platforms**: linux/amd64, linux/arm64
- **Output**: Docker images and test results

#### 2. Security Scan Docker Image
- **Purpose**: Vulnerability detection
- **Tools**: Trivy, Snyk
- **Output**: Security reports

#### 3. Deploy Docker Image
- **Purpose**: Container deployment
- **Environments**: Staging and production
- **Output**: Deployment status

### Registry Configuration

```yaml
env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}
```

## 🔧 Configuration

### Environment Variables

#### Required Secrets
```bash
# GitHub automatically provides
GITHUB_TOKEN

# Optional for advanced features
SNYK_TOKEN          # Snyk security scanning
DOCKER_USERNAME     # Docker registry access
DOCKER_PASSWORD     # Docker registry access
```

#### Environment Variables
```bash
# Database Configuration
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=test_db

# Application Settings
LOG_LEVEL=INFO
ENVIRONMENT=ci
```

### Branch Protection Rules

Enable branch protection for `main` and `develop`:

1. **Require status checks to pass before merging**
   - CI - Continuous Integration
   - CD - Continuous Deployment
   - Docker Build and Publish

2. **Require branches to be up to date before merging**

3. **Require pull request reviews before merging**

4. **Restrict pushes that create files**

## 🧪 Testing Strategy

### Test Categories

#### Unit Tests
- **Scope**: Individual functions and classes
- **Database**: SQLite (fast, isolated)
- **Coverage**: Core business logic

#### Integration Tests
- **Scope**: Component interactions
- **Database**: PostgreSQL (real database)
- **Coverage**: Database operations, API endpoints

#### Schema Validation
- **Scope**: Database schema integrity
- **Database**: Both SQLite and PostgreSQL
- **Coverage**: Table structure, relationships, constraints

#### Security Tests
- **Scope**: Vulnerability detection
- **Tools**: Safety, Bandit, Trivy, Snyk
- **Coverage**: Dependencies, code, containers

### Test Configuration

```yaml
# pytest configuration in pyproject.toml
[tool.pytest.ini_options]
markers = [
    "slow: marks tests as slow",
    "integration: marks tests as integration tests",
    "unit: marks tests as unit tests",
    "postgresql: marks tests that require PostgreSQL",
    "sqlite: marks tests that use SQLite",
]
```

## 📊 Quality Gates

### Code Quality
- **Formatting**: Black formatting validation
- **Imports**: isort import sorting
- **Linting**: flake8, pylint
- **Types**: mypy type checking

### Test Quality
- **Coverage**: Minimum coverage thresholds
- **Performance**: Test execution time limits
- **Reliability**: Test flakiness detection

### Security Quality
- **Vulnerabilities**: No high/critical vulnerabilities
- **Dependencies**: Up-to-date dependencies
- **Code Security**: Bandit security checks

## 🚀 Deployment Strategy

### Staging Deployment
- **Trigger**: Successful CI on `develop` branch
- **Purpose**: Pre-production testing
- **Database**: Staging database
- **Validation**: Automated health checks

### Production Deployment
- **Trigger**: Version tags (v*.*.*)
- **Purpose**: Production release
- **Database**: Production database
- **Validation**: Comprehensive testing

### Rollback Strategy
- **Manual Trigger**: Workflow dispatch
- **Version Selection**: Choose target version
- **Database**: Restore from backup
- **Validation**: Health check verification

## 🔒 Security Features

### Vulnerability Scanning
- **Dependencies**: Safety for Python packages
- **Code**: Bandit for security issues
- **Containers**: Trivy for Docker images
- **Advanced**: Snyk for comprehensive analysis

### Security Policies
- **Secret Scanning**: GitHub secret detection
- **Dependency Review**: Automated dependency analysis
- **Code Scanning**: Static analysis security testing
- **Container Security**: Image vulnerability scanning

## 📈 Monitoring and Observability

### Pipeline Metrics
- **Success Rate**: Pipeline completion percentage
- **Execution Time**: Job and step duration
- **Failure Analysis**: Common failure patterns
- **Resource Usage**: CPU, memory, storage

### Quality Metrics
- **Code Coverage**: Test coverage trends
- **Security Issues**: Vulnerability counts
- **Code Quality**: Linting and type check results
- **Performance**: Test execution times

## 🛠️ Customization

### Adding New Jobs

1. **Define the job** in the appropriate workflow file
2. **Set dependencies** using `needs` keyword
3. **Configure environment** and tools
4. **Add to quality gates** if applicable

### Modifying Triggers

```yaml
on:
  push:
    branches: [ main, develop, feature/*, custom-branch ]
  pull_request:
    branches: [ main, develop, custom-branch ]
  schedule:
    - cron: '0 2 * * *'  # Custom schedule
```

### Environment-Specific Configuration

```yaml
jobs:
  deploy:
    environment: ${{ github.ref == 'refs/heads/main' && 'production' || 'staging' }}
```

## 🔍 Troubleshooting

### Common Issues

#### CI Failures
1. **Linting Errors**: Run `black`, `isort`, `flake8` locally
2. **Test Failures**: Check test environment and dependencies
3. **Coverage Issues**: Verify test coverage thresholds
4. **Security Issues**: Update dependencies or fix code issues

#### CD Failures
1. **Environment Issues**: Check environment protection rules
2. **Deployment Errors**: Verify deployment configuration
3. **Database Issues**: Check migration scripts and database connectivity
4. **Permission Issues**: Verify GitHub token permissions

#### Docker Issues
1. **Build Failures**: Check Dockerfile and dependencies
2. **Security Issues**: Update base images and dependencies
3. **Registry Issues**: Verify authentication and permissions
4. **Platform Issues**: Check multi-platform build configuration

### Debugging Steps

1. **Check Workflow Logs**: Detailed execution logs in GitHub Actions
2. **Verify Environment**: Check environment variables and secrets
3. **Test Locally**: Reproduce issues in local environment
4. **Check Dependencies**: Verify tool versions and compatibility

## 📚 Best Practices

### Pipeline Design
- **Modular Jobs**: Separate concerns into focused jobs
- **Dependency Management**: Clear job dependencies and order
- **Error Handling**: Graceful failure and recovery
- **Resource Optimization**: Efficient resource usage

### Security
- **Secret Management**: Use GitHub secrets for sensitive data
- **Access Control**: Minimal required permissions
- **Vulnerability Scanning**: Regular security checks
- **Dependency Updates**: Automated dependency management

### Quality Assurance
- **Automated Testing**: Comprehensive test coverage
- **Code Quality**: Automated formatting and linting
- **Performance Monitoring**: Track execution times
- **Documentation**: Keep pipeline documentation updated

## 🚀 Future Enhancements

### Planned Features
- [ ] **Advanced Testing**: Performance and load testing
- [ ] **Deployment Strategies**: Blue-green, canary deployments
- [ ] **Monitoring Integration**: Prometheus, Grafana integration
- [ ] **Advanced Security**: SAST, DAST, IAST integration
- [ ] **Multi-Environment**: Development, staging, production
- [ ] **Automated Rollbacks**: Intelligent rollback triggers

### Integration Opportunities
- **Slack/Teams**: Deployment notifications
- **Jira**: Issue tracking integration
- **Datadog**: Performance monitoring
- **AWS/GCP**: Cloud deployment integration
- **Kubernetes**: Container orchestration

---

## 📞 Support

For CI/CD pipeline issues:

1. **Check Documentation**: Review this guide and workflow files
2. **Review Logs**: Examine GitHub Actions execution logs
3. **Search Issues**: Look for similar problems in GitHub Issues
4. **Create Issue**: Use the bug report template for new issues

## 🔗 Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Workflow Syntax Reference](https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions)
- [Security Best Practices](https://docs.github.com/en/actions/security-guides/security-hardening-for-github-actions)
- [Environment Protection](https://docs.github.com/en/actions/deployment/targeting-different-environments/using-environments-for-deployment)
