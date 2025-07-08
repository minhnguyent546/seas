// Postman Pre-request Script to handle authentication token retrieval
// Put this script in the Pre-request script tab of your Postman request

const tokenRequest = {
    url: pm.environment.get("TOKEN_URL"),
    method: "POST",
    header: {
        "Content-Type": "application/x-www-form-urlencoded"
    },
    body: {
        mode: "urlencoded",
        urlencoded: [
            { key: "username", value: pm.environment.get("USERNAME") },
            { key: "password", value: pm.environment.get("PASSWORD") },
            // FastAPI's OAuth2PasswordRequestForm also accepts optional grant_type and scope
            { key: "grant_type", value: "password" },
            { key: "scope", value: pm.environment.get("SCOPE") || "" }
        ]
    }
};

const tokenExpiry = pm.environment.get("tokenExpiry");
    // Check if the token is expired
    if (!tokenExpiry || new Date() > new Date(tokenExpiry)) {
    // Token is expired or missing, make a login request to get a new token
    pm.sendRequest(tokenRequest, (err, res) => {
        if (err || res.code !== 200) {
            console.error("Token request failed", err || res.status);
            return;
        }
        const json = res.json();
        pm.environment.set("access_token", json.access_token);
        pm.environment.set("tokenExpiry", new Date(new Date().getTime() + json.expires_in * 1000));
    })
}
