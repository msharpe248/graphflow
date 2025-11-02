# GitHub Setup Guide

This guide will help you push the GraphFlow repository to GitHub.

## Steps to Push to GitHub

### 1. Create GitHub Repository

1. Go to [GitHub](https://github.com) and log in
2. Click the "+" icon in the top right → "New repository"
3. Fill in the details:
   - **Repository name**: `graphflow`
   - **Description**: "Low-code agent builder for creating, compiling, and running AI agents with graph-based workflows"
   - **Visibility**: Choose Public or Private
   - **DO NOT** initialize with README, .gitignore, or license (we already have these)
4. Click "Create repository"

### 2. Push Existing Repository

After creating the repository, GitHub will show you commands. Use these:

```bash
# Add GitHub as remote origin
git remote add origin https://github.com/YOUR_USERNAME/graphflow.git

# Or if using SSH (recommended):
git remote add origin git@github.com:YOUR_USERNAME/graphflow.git

# Push to GitHub
git push -u origin main
```

Replace `YOUR_USERNAME` with your GitHub username.

### 3. Verify Upload

Visit your repository on GitHub to verify all files were uploaded:
- https://github.com/YOUR_USERNAME/graphflow

## Repository Settings (Optional)

### Add Topics

Add relevant topics to help others discover your project:
- Settings → Topics → Add:
  - `ai`
  - `agent`
  - `low-code`
  - `workflow`
  - `pydantic-ai`
  - `langgraph`
  - `graph`
  - `automation`
  - `react`
  - `fastapi`

### Set Up GitHub Pages (Optional)

You can host documentation using GitHub Pages:
1. Settings → Pages
2. Source: Deploy from a branch
3. Branch: main → /docs
4. Create a `docs/` folder with documentation

### Enable Issues and Discussions

1. Settings → Features
2. Enable "Issues" for bug tracking
3. Enable "Discussions" for community Q&A

## Initial Commit Summary

**Commit**: `1a9c5eb`
**Files**: 85 files, 15,843 insertions
**Packages**:
- graph-core (Python library)
- graph-compiler (Transpiler)
- graph-runtime (FastAPI server)
- graph-builder (React UI)

## Next Steps

1. **Add a badge** to README.md:
   ```markdown
   ![GitHub](https://img.shields.io/github/license/YOUR_USERNAME/graphflow)
   ![GitHub stars](https://img.shields.io/github/stars/YOUR_USERNAME/graphflow)
   ```

2. **Set up CI/CD** (optional):
   - GitHub Actions for testing
   - Automated deployment
   - Code quality checks

3. **Create releases**:
   - Tag versions with `git tag v0.1.0`
   - Push tags with `git push --tags`
   - Create releases on GitHub

4. **Add screenshots**:
   - Take screenshots of the UI
   - Add to README.md or docs/

## Troubleshooting

### Authentication Issues

If you get authentication errors:
```bash
# For HTTPS, you may need a personal access token
# Settings → Developer settings → Personal access tokens

# Or switch to SSH:
git remote set-url origin git@github.com:YOUR_USERNAME/graphflow.git
```

### Push Rejected

If the push is rejected:
```bash
# Force push (only for initial setup)
git push -u origin main --force
```

## Post-Push Checklist

- [ ] Repository visible on GitHub
- [ ] README displays correctly
- [ ] LICENSE file is recognized
- [ ] All packages uploaded
- [ ] Repository description added
- [ ] Topics/tags added
- [ ] Social preview image (optional)

---

**Your repository is ready to share with the world!** 🎉
