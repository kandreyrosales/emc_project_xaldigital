import { CognitoIdentityProviderClient, GetUserCommand } from "@aws-sdk/client-cognito-identity-provider"; // ES Modules import
// const { CognitoIdentityProviderClient, GetUserCommand } = require("@aws-sdk/client-cognito-identity-provider"); // CommonJS import
const client = new CognitoIdentityProviderClient({ region: "us-east-1" });

async function getUserInfo(event) {
    const { access_token } = JSON.parse(event.body);
    const input = { // GetUserRequest
        AccessToken: access_token, // required
    };
    try {
        const command = new GetUserCommand(input);
        const response = await client.send(command);
        console.log(response);
        return {
            statusCode: 200,
            headers: {
                    "Access-Control-Allow-Origin" : "*", // Required for CORS support to work
                    "Access-Control-Allow-Credentials" : true // Required for cookies, authorization headers with HTTPS
                },
            body: JSON.stringify(response)
        }
    } catch (error) {
        console.error(error);
        return {
            statusCode: 500,
                headers: {
                    "Access-Control-Allow-Origin" : "*", // Required for CORS support to work
                    "Access-Control-Allow-Credentials" : true // Required for cookies, authorization headers with HTTPS
                },
                body: JSON.stringify({
                    statusCode: 500,
                    error: 'Internal Server Error',
                    internalError: JSON.stringify({ error: error.message }),
                }),
        }
    }
}

export { getUserInfo as handler };


