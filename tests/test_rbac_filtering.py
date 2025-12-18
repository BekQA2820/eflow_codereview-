import os
import time

MANIFEST_PATH = "/api/v1/manifest"


def test_rbac_widget_filtering(s3_client, api_client, token_valid, token_other_user, auth_header):

    bucket = os.getenv("S3_BUCKET")
    key = "widgets.yaml"


    yaml_content = b"""
widgets:
  - id: admin_only_widget
    mfe: https://cdn.example.com/admin_widget/remoteEntry.js
    position:
      row: 0
      col: 0
      width: 2
    size:
      h: 2
      w: 2
    visible: true
    requiredRoles: ["admin"]
"""

    s3_client.put_object(Bucket=bucket, Key=key, Body=yaml_content)


    time.sleep(1.5)


    headers_user = {"Authorization": f"Bearer {token_valid}"} if token_valid else {}
    r_user = api_client.get(MANIFEST_PATH, headers=headers_user)
    assert r_user.status_code == 200
    body_user = r_user.json()
    assert all(w.get("id") != "admin_only_widget" for w in body_user.get("widgets", []))


    headers_admin = {"Authorization": f"Bearer {token_other_user}"} if token_other_user else {}
    r_admin = api_client.get(MANIFEST_PATH, headers=headers_admin)
    assert r_admin.status_code == 200
    body_admin = r_admin.json()
    assert any(w.get("id") == "admin_only_widget" for w in body_admin.get("widgets", []))
