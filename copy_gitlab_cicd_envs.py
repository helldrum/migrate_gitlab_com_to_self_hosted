#!/usr/bin/env pipenv-shebang
import os
import gitlab
import pprint


def gitlab_instance(gitlab_url, private_token):
    return gitlab.Gitlab(
        gitlab_url,
        private_token=private_token,
    )


def get_groups_vars(gitlab_instance):
    print("get groups vars envs")
    group_vars = {}
    for group in gitlab_instance.groups.list(all=True, membership=True):
        for var in group.variables.list():
            if not group_vars.get(group.name):
                group_vars[group.name] = []
            group_vars[group.name].append(
                {
                    "variable_type": var.variable_type,
                    "key": var.key,
                    "protected": var.protected,
                    "masked": var.masked,
                    "environment_scope": var.environment_scope,
                    "value": var.value,
                }
            )
    return group_vars


def get_projects_vars(gitlab_instance):
    print("get project envs vars.")
    env_vars = {}
    for project in gitlab_instance.projects.list(all=True, membership=True, lazy=False):
        try:
            variables = project.variables.list(get_all=True)
            if variables:
                env_vars[project.name] = []
                for var in variables:
                    env_vars[project.name].append(
                        {
                            "variable_type": var.variable_type,
                            "key": var.key,
                            "protected": var.protected,
                            "masked": var.masked,
                            "environment_scope": var.environment_scope,
                            "value": var.value,
                        }
                    )
        except Exception as e:
            print(e)
    return env_vars


def set_group_var_or_skip_creation(gitlab_instance, group_vars):
    for group in gitlab_instance.groups.list(all=True, membership=True):
        if group.name in group_vars.keys():
            for env in group_vars[group.name]:
                try:
                    print(f"set variables {env} on group {group.name}")

                    group.variables.create(
                        {
                            "key": env["key"],
                            "value": env["value"],
                            "protected": env["protected"],
                            "variable_type": env["variable_type"],
                            "masked": env["masked"],
                            "environment_scope": env["environment_scope"],
                        }
                    )
                except Exception as e:
                    print(e)
                    print(f"skip env {env} creation")


def set_projects_vars_or_skip_creation(gitlab_instance, env_vars):
    for project in gitlab_instance.projects.list(all=True, membership=True, lazy=False):
        if project.name in env_vars.keys():
             for env in env_vars[project.name]:
                try:
                    print(f"set variables {env['key']} on project {project.name}")

                    project.variables.create(
                        {
                            "key": env["key"],
                            "value": env["value"],
                            "protected": env["protected"],
                            "variable_type": env["variable_type"],
                            "masked": env["masked"],
                            "environment_scope": env["environment_scope"],
                        }
                    )
                except Exception as e:
                    print(e)
                    print(f"skip env {env} creation")

gitlab_com_token = os.getenv("GITLAB_COM_TOKEN")
gitlab_on_prem_token = os.getenv("GITLAB_ON_PREM_TOKEN")

gl_com_inst = gitlab_instance(os.getenv("GITLAB_COM_URL"), gitlab_com_token)
gl_onprem_inst = gitlab_instance(
    os.getenv("GITLAB_SELF_HOST_URL"), gitlab_on_prem_token
)

gl_com_groups_vars = get_groups_vars(gl_com_inst)
set_group_var_or_skip_creation(gl_onprem_inst, gl_com_groups_vars)

gl_com_projects_vars = get_projects_vars(gl_com_inst)
set_projects_vars_or_skip_creation(gl_onprem_inst,gl_com_projects_vars)
