# Git Workflow Guide for Analytics Assist

This document outlines the git workflow for the Analytics Assist application to help manage development and production code effectively.

## Branch Structure

The repository has three main branches:

1. **main** - The current production code
2. **development** - For active development and testing
3. **production** - Stable release code deployed to production

## Workflow Process

### Making Changes

1. Always work in the **development** branch for new features or bug fixes:
   ```
   git checkout development
   ```

2. Make your changes, test them thoroughly

3. Commit your changes with descriptive messages:
   ```
   git add .
   git commit -m "Brief description of changes"
   ```

### Merging to Production

Once changes in the development branch are tested and ready for production:

1. Switch to the production branch:
   ```
   git checkout production
   ```

2. Merge the development branch into production:
   ```
   git merge development
   ```

3. Resolve any conflicts if they occur

4. Push the changes to the remote repository (if applicable):
   ```
   git push origin production
   ```

### Updating Main

After confirming the production branch is stable:

1. Switch to the main branch:
   ```
   git checkout main
   ```

2. Merge the production branch into main:
   ```
   git merge production
   ```

3. Push the changes to the remote repository (if applicable):
   ```
   git push origin main
   ```

## Best Practices

1. **Regular commits**: Make small, focused commits with descriptive messages
2. **Pull before push**: Always pull the latest changes before pushing to avoid conflicts
3. **Feature branches**: For major features, consider creating feature-specific branches off the development branch
4. **Testing**: Always test changes thoroughly before merging to production
5. **Documentation**: Update documentation when implementing new features

## Common Git Commands

- View branch status: `git status`
- List all branches: `git branch`
- Create and switch to a new branch: `git checkout -b branch-name`
- Switch between branches: `git checkout branch-name`
- Merge branches: `git merge source-branch`
- View commit history: `git log`
- Discard local changes: `git checkout -- file-name`
- Stash changes temporarily: `git stash`
- Apply stashed changes: `git stash apply`

## Handling Hotfixes

For urgent fixes needed in production:

1. Create a hotfix branch from production:
   ```
   git checkout production
   git checkout -b hotfix-description
   ```

2. Make the necessary fixes and commit

3. Merge the hotfix into both production and development:
   ```
   git checkout production
   git merge hotfix-description
   
   git checkout development
   git merge hotfix-description
   ```

4. Delete the hotfix branch:
   ```
   git branch -d hotfix-description
   ```