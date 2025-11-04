"""
Minimal Flask app to serve JWKS for Epic verification
Deploy this to Dockploy at health-analytics.duckdev.me
"""

from flask import Flask, jsonify
import json

app = Flask(__name__)

# Your JWKS content
JWKS = {
  "keys": [
    {
      "kty": "RSA",
      "kid": "epic-backend-key",
      "use": "sig",
      "alg": "RS384",
      "n": "ljZu5kNEmi1ED3_Ceaqh5hT8Ude8HIaA6XFYesu_SNnvbFaBfa_Hua_8ypdCRmAgqzzjzlAyaCmmDrsKyKySiieBVaDJYBUSroPAQCcSOe4a_UjLbgqAZutqjr72PszlcwFyFHKSRT-261ZuFCGOkmYnv8D3XKiY0cnVd4LjWI1OXQ21pEEXDb2EXyxZhZtgpt4oWlb-BRGa5cRPpDB-yAzNm21ZJadZB_171XlzMtVb3-vx3mllTuIYyCKGkvXIgZlX_MHdOEezHGbtsMo3YKNhNHsc-fpstSshIf51Emaeuh3NwSArFNGvSdEeozQA9AvBJEF7AnDtiRhU2T2PEDsDA6KxUR3jhXytjRsvZW083R4C-2okuHTGLBfomw_ru-euubHgkvTN2U18kv-ZNXB3AdTxG5Ava9IOxGaUzu9SDGVzVg3o0EF2zbYepcceN378HtuzBkB8FpLjC1zGDMAfx73w5dN7FRtH0BClpPAbTzfaG93-T2d7qTo0fhkZLZXxDOHwn3ekJ5WRF0VOfkFrmtw4h-73ivzIhqnwg1wiDBLZO4uUvHo1E4S4pZLhL-6BQFedmDAmm-S89g4j7uOIczS4XxqTloYE-8SQ9U2LCn6DSQWT5o08iMWric5xQJZYNl_djgze_BuwAX3hWEHUuif3iNmpCFD2Y4aACXc",
      "e": "AQAB"
    }
  ]
}

@app.route('/api/backend/.well-known/jwks.json', methods=['GET'])
def get_jwks():
    """Serve JWKS for Epic to verify"""
    return jsonify(JWKS), 200, {'Content-Type': 'application/json'}

@app.route('/', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "ok",
        "message": "JWKS endpoint active",
        "jwks_url": "/api/backend/.well-known/jwks.json"
    }), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
