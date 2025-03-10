import os

import google.auth
from google.cloud import secretmanager


def get_secret(secret_id, project_id=None):
    """
    Retrieve the latest version of a secret from Google Cloud Secret Manager.
    If project_id is not provided, try to get it from the environment or default credentials.
    """
    if project_id is None:
        project_id = os.environ.get("GCP_PROJECT")
        if not project_id:
            try:
                _, project_id = google.auth.default()
            except Exception as e:
                raise Exception(
                    "GCP_PROJECT must be set or default credentials must be configured."
                ) from e

    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")
