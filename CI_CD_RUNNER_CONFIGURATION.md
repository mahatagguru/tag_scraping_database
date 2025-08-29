# CI/CD Runner Configuration Guide

This guide explains how to configure and optimize GitHub Actions runners for your TAG Grading Scraper project.

## 🚀 **Runner Types & Parallelization Strategies**

### **1. GitHub Hosted Runners (Current Setup)**

Your workflows currently use `runs-on: ubuntu-latest`, which provides:
- ✅ **Automatic scaling** - GitHub handles runner allocation
- ✅ **No maintenance** - Always up-to-date
- ✅ **Parallel execution** - Multiple jobs can run simultaneously
- ✅ **Free tier** - 2000 minutes/month for public repos

### **2. Matrix Strategy for Parallelization**

We've implemented matrix strategies to increase parallelization:

#### **Linting Matrix (5 parallel jobs):**
```yaml
lint:
  strategy:
    matrix:
      tool: [black, isort, flake8, mypy, pylint]
```

#### **Testing Matrix (3 parallel jobs):**
```yaml
test-sqlite:
  strategy:
    matrix:
      python-version: ['3.9', '3.10', '3.11']
```

#### **Security Matrix (2 parallel jobs):**
```yaml
security:
  strategy:
    matrix:
      tool: [safety, bandit]
```

## 📊 **Current Parallelization**

| Job | Runners | Parallel Jobs | Total Runners |
|-----|---------|---------------|---------------|
| Lint | 5 | 5 | 5 |
| Test SQLite | 3 | 3 | 3 |
| Test PostgreSQL | 1 | 1 | 1 |
| Validate Schema | 1 | 1 | 1 |
| Security | 2 | 2 | 2 |
| Build | 1 | 1 | 1 |
| Quality Gates | 1 | 1 | 1 |
| **Total** | **14** | **14** | **14** |

## 🔧 **How to Increase Runners**

### **Option 1: Add More Matrix Dimensions**

```yaml
# Example: Add more Python versions
test-sqlite:
  strategy:
    matrix:
      python-version: ['3.8', '3.9', '3.10', '3.11', '3.12']
      os: [ubuntu-latest, windows-latest, macos-latest]
```

### **Option 2: Split Large Jobs**

```yaml
# Split database tests by sport
test-baseball:
  runs-on: ubuntu-latest
  # Test baseball-specific functionality

test-football:
  runs-on: ubuntu-latest
  # Test football-specific functionality

test-basketball:
  runs-on: ubuntu-latest
  # Test basketball-specific functionality
```

### **Option 3: Add Parallel Build Jobs**

```yaml
# Build for different platforms
build-linux:
  runs-on: ubuntu-latest
  # Build Linux package

build-windows:
  runs-on: windows-latest
  # Build Windows package

build-macos:
  runs-on: macos-latest
  # Build macOS package
```

## ⚡ **Performance Optimization**

### **1. Job Dependencies**

```yaml
# Only run tests after linting passes
test-sqlite:
  needs: lint
  runs-on: ubuntu-latest

test-postgresql:
  needs: lint
  runs-on: ubuntu-latest
```

### **2. Caching Dependencies**

```yaml
- name: Cache pip dependencies
  uses: actions/cache@v3
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
    restore-keys: |
      ${{ runner.os }}-pip-
```

### **3. Parallel vs Sequential Execution**

```yaml
# Parallel (faster, more runners)
jobs:
  job1: # Runs immediately
  job2: # Runs immediately
  job3: # Runs immediately

# Sequential (slower, fewer runners)
jobs:
  job1: # Runs first
  job2:
    needs: job1 # Waits for job1
  job3:
    needs: job2 # Waits for job2
```

## 🐳 **Docker Build Parallelization**

Your Docker workflow can also be parallelized:

```yaml
# Build for multiple platforms simultaneously
build:
  strategy:
    matrix:
      platform: [linux/amd64, linux/arm64, linux/arm/v7]
      include:
        - platform: linux/amd64
          platform-name: "Linux AMD64"
        - platform: linux/arm64
          platform-name: "Linux ARM64"
        - platform: linux/arm/v7
          platform-name: "Linux ARM v7"
```

## 📈 **Runner Scaling Strategies**

### **Small Projects (Current)**
- **Runners**: 5-10 parallel jobs
- **Strategy**: Matrix for different tools/versions
- **Cost**: Free tier sufficient

### **Medium Projects**
- **Runners**: 10-20 parallel jobs
- **Strategy**: Split by functionality + matrix
- **Cost**: May need paid minutes

### **Large Projects**
- **Runners**: 20+ parallel jobs
- **Strategy**: Self-hosted runners + matrix
- **Cost**: Self-hosted infrastructure

## 🔍 **Monitoring Runner Usage**

### **GitHub Actions Insights**
1. Go to your repository
2. Click **Actions** tab
3. Click **Insights** in the left sidebar
4. View **Workflow runs** and **Job duration**

### **Runner Status**
```bash
# Check current runner usage
gh api repos/:owner/:repo/actions/runs --paginate
```

## 🚨 **Runner Limits & Considerations**

### **GitHub Hosted Runner Limits**
- **Public repos**: 2000 minutes/month free
- **Private repos**: 2000 minutes/month free
- **Concurrent jobs**: Up to 20 per repository
- **Job timeout**: 6 hours maximum

### **Cost Optimization**
```yaml
# Use shorter timeouts
timeout-minutes: 30

# Cancel redundant workflows
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
```

## 🛠️ **Custom Runner Setup (Advanced)**

### **Self-Hosted Runners**
```yaml
# Use your own infrastructure
runs-on: self-hosted
```

### **Runner Groups**
```yaml
# Organize runners by environment
runs-on: [self-hosted, linux, production]
```

## 📋 **Recommended Configuration**

### **For Your Current Project:**
```yaml
# Keep current matrix strategies
# Add caching for dependencies
# Consider splitting large test suites
# Monitor runner usage and costs
```

### **Future Scaling:**
```yaml
# Add more Python versions
# Split tests by sport/functionality
# Add platform-specific builds
# Implement self-hosted runners if needed
```

## 🔧 **Quick Commands**

### **Check Current Runner Usage:**
```bash
gh api repos/:owner/:repo/actions/runs --paginate | jq '.workflow_runs[] | {id, status, conclusion, duration}'
```

### **Cancel Running Workflows:**
```bash
gh api repos/:owner/:repo/actions/runs --paginate | jq '.workflow_runs[] | select(.status == "in_progress") | .id' | xargs -I {} gh api repos/:owner/:repo/actions/runs/{} --method DELETE
```

---

**Your current setup already provides excellent parallelization with 14 parallel jobs! 🚀✨**
