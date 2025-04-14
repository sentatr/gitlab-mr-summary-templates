import gitlab
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import logging

# FastAPI app for webhook listener
app = FastAPI()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# GitLab API configuration
GITLAB_URL = "https://gitlab.com"  # Replace with your GitLab instance URL
GITLAB_TOKEN = "your_private_token"  # Replace with your GitLab personal access token
gl = gitlab.Gitlab(GITLAB_URL, private_token=GITLAB_TOKEN)

@app.post("/webhook")
async def handle_webhook(request: Request):
    try:
        # Parse webhook payload
        event = await request.json()
        if not event:
            logging.error("No JSON payload received")
            raise HTTPException(status_code=400, detail="Invalid payload")

        if event.get('object_kind') != 'merge_request':
            logging.warning("Unsupported event type: %s", event.get('object_kind'))
            return JSONResponse(content={"message": "Event not supported"}, status_code=400)

        # Extract MR details
        project_id = event.get('project', {}).get('id')
        mr_iid = event.get('object_attributes', {}).get('iid')
        if not project_id or not mr_iid:
            logging.error("Missing project_id or mr_iid in payload")
            raise HTTPException(status_code=400, detail="Invalid payload structure")

        mr_title = event['object_attributes'].get('title', 'N/A')
        mr_description = event['object_attributes'].get('description', 'N/A')
        mr_author = event['object_attributes'].get('author_id', 'N/A')
        mr_state = event['object_attributes'].get('state', 'N/A')
        mr_url = event['object_attributes'].get('url', 'N/A')

        # Fetch additional MR details
        try:
            project = gl.projects.get(project_id)
            mr = project.mergerequests.get(mr_iid)
            comments = mr.notes.list()
            reviewers = [user['username'] for user in event.get('reviewers', [])]
        except gitlab.exceptions.GitlabGetError as e:
            logging.error("Error fetching MR details: %s", str(e))
            raise HTTPException(status_code=500, detail="Failed to fetch MR details")

        # Generate Markdown table summary
        markdown_summary = f"""
        ### Merge Request Summary

        | **Field**       | **Details** |
        |-----------------|-------------|
        | **Title**       | {mr_title}  |
        | **Description** | {mr_description} |
        | **Author**      | {mr.author['name']} |
        | **Reviewers**   | {', '.join(reviewers) if reviewers else 'None'} |
        | **State**       | {mr_state}  |
        | **URL**         | [Link to MR]({mr_url}) |

        ### Comments
        """
        for comment in comments:
            markdown_summary += f"- **{comment.author['name']}**: {comment.body}\n"

        # Update MR description or add a comment
        try:
            mr.notes.create({'body': markdown_summary})
        except gitlab.exceptions.GitlabCreateError as e:
            logging.error("Error updating MR: %s", str(e))
            raise HTTPException(status_code=500, detail="Failed to update MR")

        return JSONResponse(content={"message": "Merge Request summary updated"}, status_code=200)

    except Exception as e:
        logging.exception("Unexpected error occurred")
        raise HTTPException(status_code=500, detail="Internal server error")

# Run the application using uvicorn
# Command: uvicorn <filename>:app --host 0.0.0.0 --port 5000
