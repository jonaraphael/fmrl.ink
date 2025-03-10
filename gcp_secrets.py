import google.auth
from google.cloud import secretmanager


def get_secret(secret_id, project_id=None):
    """
    Retrieve the latest version of a secret from Google Cloud Secret Manager.
    If project_id is not provided, try to get it from the environment or default credentials.
    """
    _, project_id = google.auth.default()

    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")
