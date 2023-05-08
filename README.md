GitLab Migration Scripts
This repository contains Python scripts to help you migrate GitLab groups, projects, and CI/CD environment variables from one GitLab instance to another (e.g., GitLab.com to a self-hosted GitLab instance)
You have a script to migrate user as well, creating a yaml of existing permission, you need to review and complete with user emails .


Scripts
copy_gitlab_cicd_envs.py: This script migrates the CI/CD environment variables for groups and projects.
copy_gitlab_groups_and_repository.py: This script migrates GitLab groups, subgroups, and projects (repositories) without the Git history.
sync_repositories.py clone and push force branches and tags to all projects
sync_permissions.py generate a yaml file to automated sending invitations to users


Requirements

pipenv
pipenv-shebang
gitlab
pyYaml

.env file need to be setup with those env vars
GITLAB_COM_TOKEN: Access token for the source GitLab instance (e.g., GitLab.com).
GITLAB_ON_PREM_TOKEN: Access token for the destination GitLab instance (e.g., self-hosted GitLab).
GITLAB_COM_URL: URL of the source GitLab instance (e.g., https://gitlab.com).
GITLAB_SELF_HOST_URL: URL of the destination GitLab instance (e.g., https://your-self-hosted-gitlab.example.com).
Run the scripts in the following order:

#Limitations

The copy_gitlab_groups_and_repository.py script only migrates GitLab groups, subgroups, and project metadata. It does not migrate the actual Git repository history. You need to push your repository to the new instance manually or use another tool to transfer the Git history.
The scripts do not handle issues, merge requests, milestones, labels, or any other GitLab-specific features beyond groups, projects, and CI/CD environment variables.

You need to get the users emails by yourself if you are not administrator on gitlab.com (payed account) or adapt the script to grab emails.
