// Postman Post-response Script to set access token after login
// Put this script in the Post-response script tab of your Postman request for login

// Check if the response was successful
if (pm.response.code === 200) {
    // Parse the response body to JSON
    const responseJson = pm.response.json();

    // Extract the access token and expiration time
    const accessToken = responseJson.access_token;
    const expiresIn = responseJson.expires_in; // Assuming expires_in is in seconds

    // Calculate the expiration time
    const now = new Date();
    const expiryDate = new Date(now.getTime() + expiresIn * 1000);

    // Set the environment variables
    pm.environment.set("access_token", accessToken);
    pm.environment.set("tokenExpiry", expiryDate.toISOString());

    console.log("Access token set successfully");
} else {
    console.error("Login failed with status code:", pm.response.code);
}
