#!/usr/bin/env pipenv-shebang
import gitlab
import os
import subprocess
from subprocess import check_output


def gitlab_instance(gitlab_url, private_token):
    return gitlab.Gitlab(
        gitlab_url,
        private_token=private_token,
    )


def list_gitlab_project(gitlab_instance):
    return gitlab_instance.projects.list(all=True, membership=True)


def solve_git_url_on_both_gitlab(projects_list_gitlab_com, projects_list):
    git_url = {}
    for project in projects_list_gitlab_com:
        gitlab_com = project.ssh_url_to_repo
        for project_self_host in projects_list:
            if project_self_host.name in project.name:
                self_host = project_self_host.ssh_url_to_repo
                git_url[project.name] = {"origin": gitlab_com, "origin2": self_host}

    return git_url


def git_clone_and_add_origin2_to_all_projects(git_url):
    os.chdir(repo_path)
    try:
        for project in git_url:

            print(["git", "clone", git_url[project]["origin"]])
            folder_name = subprocess.run(
                ["git", "clone", git_url[project]["origin"]],
                capture_output=True,
                text=True,
            ).stderr.split("'")[1]

            print(f"cd {os.path.join(repo_path, folder_name)}")
            os.chdir(os.path.join(repo_path, folder_name))

            print(["git", "remote", "add", "origin2", git_url[project]["origin2"]])
            print(
                subprocess.run(
                    ["git", "remote", "add", "origin2", git_url[project]["origin2"]],
                    capture_output=True,
                    text=True,
                )
            )
            os.chdir(repo_path)
    except Exception as e:
        print(f"ERROR during cloning project {project}")


def sync_git_folders_code(repo_path):
    repos = [
        f for f in os.listdir(repo_path) if os.path.isdir(os.path.join(repo_path, f))
    ]
    for repo in repos:
        print(f"on repo {repo}")
        os.chdir(os.path.join(repo_path, repo))

        try:
            print("git fetch --all")
            subprocess.run(["git", "fetch", "--all"])
            print("git push --force origin2 --all")
            subprocess.run(["git", "push", "--force", "origin2", "--all"])
            print("git push --force origin2 --tags")
            subprocess.run(["git", "push", "--force", "origin2", "--tags"])

        except Exception as e:
            print("-" * 20)
            print(e)
            print("-" * 20)


script_path = os.path.dirname(os.path.abspath(__file__))
repo_path = os.path.join(script_path, "repo")

if not os.path.exists(repo_path):
    os.makedirs(repo_path)

os.chdir(repo_path)

gitlab_com_token = os.getenv("GITLAB_COM_TOKEN")
gitlab_on_prem_token = os.getenv("GITLAB_ON_PREM_TOKEN")

gl_com_inst = gitlab_instance(os.getenv("GITLAB_COM_URL"), gitlab_com_token)
gl_onprem_inst = gitlab_instance(
    os.getenv("GITLAB_SELF_HOST_URL"), gitlab_on_prem_token
)

print("get project list on gitlab.com")
gl_com_projects = list_gitlab_project(gl_com_inst)

print("get project list on self host gitlab")
gl_onprem_projects = list_gitlab_project(gl_onprem_inst)

print("get ssh url on both gitlab")
git_url = solve_git_url_on_both_gitlab(gl_com_projects, gl_onprem_projects)

print("clone and add origin2 to all repository")
git_clone_and_add_origin2_to_all_projects(git_url)

print("run git commands to sync push origin to origin2")
sync_git_folders_code(repo_path)
