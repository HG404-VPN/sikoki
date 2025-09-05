
import builtins
builtins.input = lambda prompt='': ''

from flask import Flask, request, jsonify
from werkzeug.exceptions import HTTPException

from .api_request import (
    validate_contact, get_otp, submit_otp, get_new_token, get_profile,
    get_balance, get_family, get_families, get_package, get_addons,
    send_payment_request, extend_session
)
from .purchase_api import (
    get_payment_methods, show_multipayment, settlement_multipayment,
    show_qris_payment, get_qris_code, settlement_qris, settlement_bounty
)

app = Flask(__name__)

def api_key_from_request(req):
    data = {}
    if req.is_json:
        data = req.get_json(silent=True) or {}
    return req.headers.get("X-Api-Key") or data.get("api_key")

def require_fields(data, fields):
    missing = [f for f in fields if f not in data or data[f] in (None, "", [])]
    if missing:
        return False, {"error": "missing_fields", "fields": missing}
    return True, None

@app.errorhandler(Exception)
def handle_exception(e):
    if isinstance(e, HTTPException):
        return jsonify(error=e.name, detail=e.description), e.code
    return jsonify(error="internal_error", detail=str(e)), 500

@app.get("/")
def root():
    return jsonify(
        name="myxl-flask-api",
        ok=True,
        endpoints=[
            "POST /api/otp/request",
            "POST /api/otp/submit",
            "POST /api/token/refresh",
            "POST /api/profile",
            "POST /api/balance",
            "POST /api/family",
            "POST /api/families",
            "POST /api/package/details",
            "POST /api/package/addons",
            "POST /api/purchase/multipayment",
            "POST /api/purchase/qris"
        ]
    )

@app.post("/api/otp/request")
def api_otp_request():
    data = request.get_json(force=True, silent=True) or {}
    contact = str(data.get("contact","")).strip()
    if not contact:
        return jsonify({"error":"missing_fields","fields":["contact"]}), 400
    if not validate_contact(contact):
        return jsonify({"error":"invalid_contact"}), 400
    res = get_otp(contact)
    return jsonify({"ok": True, "contact": contact, "result": res})

@app.post("/api/otp/submit")
def api_otp_submit():
    data = request.get_json(force=True, silent=True) or {}
    contact = str(data.get("contact","")).strip()
    code = str(data.get("code","")).strip()
    if not contact or not code:
        return jsonify({"error":"missing_fields","fields":["contact","code"]}), 400
    api_key = api_key_from_request(request)
    if not api_key:
        return jsonify({"error":"missing_api_key","hint":"Set header X-Api-Key atau api_key di body"}), 400
    res = submit_otp(api_key, contact, code)
    return jsonify({"ok": True, "result": res})

@app.post("/api/token/refresh")
def api_token_refresh():
    data = request.get_json(force=True, silent=True) or {}
    refresh = data.get("refresh_token")
    if not refresh:
        return jsonify({"error":"missing_fields","fields":["refresh_token"]}), 400
    res = get_new_token(refresh)
    return jsonify({"ok": True, "result": res})

@app.post("/api/profile")
def api_profile():
    data = request.get_json(force=True, silent=True) or {}
    api_key = api_key_from_request(request)
    tokens = data.get("tokens") or {}
    if not api_key or not tokens:
        return jsonify({"error":"missing_fields","fields":["tokens","X-Api-Key"]}), 400
    res = get_profile(api_key, tokens.get("access_token"), tokens.get("id_token"))
    return jsonify({"ok": True, "result": res})

@app.post("/api/balance")
def api_balance():
    data = request.get_json(force=True, silent=True) or {}
    api_key = api_key_from_request(request)
    tokens = data.get("tokens") or {}
    if not api_key or not tokens:
        return jsonify({"error":"missing_fields","fields":["tokens","X-Api-Key"]}), 400
    res = get_balance(api_key, tokens.get("id_token"))
    return jsonify({"ok": True, "result": res})

@app.post("/api/family")
def api_family():
    data = request.get_json(force=True, silent=True) or {}
    api_key = api_key_from_request(request)
    tokens = data.get("tokens") or {}
    family_code = data.get("family_code")
    if not api_key or not tokens or not family_code:
        return jsonify({"error":"missing_fields","fields":["tokens","family_code","X-Api-Key"]}), 400
    res = get_family(api_key, tokens, family_code)
    return jsonify({"ok": True, "result": res})

@app.post("/api/families")
def api_families():
    data = request.get_json(force=True, silent=True) or {}
    api_key = api_key_from_request(request)
    tokens = data.get("tokens") or {}
    cat = data.get("package_category_code")
    if not api_key or not tokens or not cat:
        return jsonify({"error":"missing_fields","fields":["tokens","package_category_code","X-Api-Key"]}), 400
    res = get_families(api_key, tokens, cat)
    return jsonify({"ok": True, "result": res})

@app.post("/api/package/details")
def api_package_details():
    data = request.get_json(force=True, silent=True) or {}
    api_key = api_key_from_request(request)
    tokens = data.get("tokens") or {}
    code = data.get("package_option_code")
    if not api_key or not tokens or not code:
        return jsonify({"error":"missing_fields","fields":["tokens","package_option_code","X-Api-Key"]}), 400
    res = get_package(api_key, tokens, code)
    return jsonify({"ok": True, "result": res})

@app.post("/api/package/addons")
def api_package_addons():
    data = request.get_json(force=True, silent=True) or {}
    api_key = api_key_from_request(request)
    tokens = data.get("tokens") or {}
    code = data.get("package_option_code")
    if not api_key or not tokens or not code:
        return jsonify({"error":"missing_fields","fields":["tokens","package_option_code","X-Api-Key"]}), 400
    res = get_addons(api_key, tokens, code)
    return jsonify({"ok": True, "result": res})

@app.post("/api/payment/multipayment")
def multipayment():
    data = request.json
    result = show_multipayment(
        api_key=data.get("api_key"),
        tokens=data.get("tokens"),
        package_option_code=data.get("package_option_code"),
        token_confirmation=data.get("token_confirmation"),
        price=data.get("price"),
        payment_method=data.get("payment_method"),
        wallet_number=data.get("wallet_number", ""),
        item_name=data.get("item_name", "")
    )
    return jsonify(result)

@app.post("/api/purchase/multipayment")
def api_purchase_multipayment():
    data = request.json
    result = show_multipayment(
        api_key=api_key_from_request(request),
        tokens=data.get("tokens"),
        package_option_code=data.get("package_option_code"),
        token_confirmation=data.get("token_confirmation"),
        price=data.get("price"),
        item_name=data.get("item_name", ""),
        payment_method=data.get("payment_method"),
        wallet_number=data.get("wallet_number", "")
    )
    return jsonify(result)

@app.post("/api/purchase/qris")
def api_purchase_qris():
    data = request.get_json(force=True, silent=True) or {}
    api_key = api_key_from_request(request)
    tokens = data.get("tokens") or {}
    poc = data.get("package_option_code")
    conf = data.get("token_confirmation")
    price = data.get("price")
    item = data.get("item_name")
    if not api_key or not tokens or not poc or conf is None or price is None or not item:
        return jsonify({"error":"missing_fields","fields":["tokens","package_option_code","token_confirmation","price","item_name","X-Api-Key"]}), 400
    res = show_qris_payment(api_key, tokens, poc, conf, int(price), item)
    return jsonify({"ok": True, "result": res})
