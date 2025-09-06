from .api_request import get_package, send_api_request
from .auth_helper import AuthInstance

# Fetch my packages (backend version)
def fetch_my_packages():
    api_key = AuthInstance.api_key
    tokens = AuthInstance.get_active_tokens()
    if not tokens:
        return {"error": "no_active_tokens"}

    id_token = tokens.get("id_token")

    path = "api/v8/packages/quota-details"
    payload = {
        "is_enterprise": False,
        "lang": "en",
        "family_member_id": ""
    }

    res = send_api_request(api_key, path, payload, id_token, "POST")
    if res.get("status") != "SUCCESS":
        return {"error": "failed_fetch", "response": res}

    quotas = res["data"].get("quotas", [])
    results = []

    for quota in quotas:
        quota_code = quota.get("quota_code")
        group_code = quota.get("group_code")
        name = quota.get("name")
        family_code = None

        package_details = get_package(api_key, tokens, quota_code)
        if package_details:
            family_code = package_details.get("package_family", {}).get("package_family_code")

        results.append({
            "name": name,
            "quota_code": quota_code,
            "family_code": family_code,
            "group_code": group_code
        })

    return {"packages": results}
