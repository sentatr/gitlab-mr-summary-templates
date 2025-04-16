import asyncio
import aiohttp
import datetime
import os
from python_gitlab import Gitlab

# GitLab setup using predefined CI/CD variables
GITLAB_URL = os.getenv("CI_SERVER_URL", "https://gitlab.com")
GITLAB_TOKEN = os.getenv("CI_JOB_TOKEN")  # Use GitLab CI job token for authentication
GROUP_ID = os.getenv("CI_PROJECT_NAMESPACE")  # Fetch the namespace/group

gitlab = Gitlab(GITLAB_URL, private_token=GITLAB_TOKEN)

async def fetch_merge_requests(session, project_id):
    """Fetch merge requests merged on the current date for a given project."""
    today = datetime.datetime.utcnow().strftime('%Y-%m-%d')
    url = f"{GITLAB_URL}/api/v4/projects/{project_id}/merge_requests?state=merged"

    async with session.get(url, headers={"PRIVATE-TOKEN": GITLAB_TOKEN}) as response:
        data = await response.json()
        return [mr['id'] for mr in data if 'merged_at' in mr and mr['merged_at'].startswith(today)]

async def process_project(session, project):
    """Process each GitLab project asynchronously."""
    merge_request_ids = await fetch_merge_requests(session, project.id)
    if merge_request_ids:
        print(f"Project {project.path_with_namespace}: {merge_request_ids}")

async def main():
    """Main asynchronous workflow to process merge requests."""
    async with aiohttp.ClientSession() as session:
        tasks = []
        group = gitlab.groups.get(GROUP_ID)  # Fetch group using GitLab predefined variable
        for project in group.projects.list(all=True):
            tasks.append(process_project(session, project))

        await asyncio.gather(*tasks)

# Run async event loop
if __name__ == "__main__":
    asyncio.run(main())
