import { CognitoIdentityProviderClient, ResendConfirmationCodeCommand } from "@aws-sdk/client-cognito-identity-provider";
import crypto from 'crypto';

const client = new CognitoIdentityProviderClient({ region: "us-east-1" });

function generateSecretHash(username, clientId, clientSecret) {
    return crypto.createHmac('SHA256', clientSecret)
                 .update(username + clientId)
                 .digest('base64');
}

async function resend_code(event) {
    const { username } = JSON.parse(event.body);
    const clientId = process.env.clientId;
    const clientSecret = process.env.clientSecret;

    const secretHash = generateSecretHash(username, clientId, clientSecret);

    const params = {
        ClientId: clientId,
        SecretHash: secretHash,
        Username: username
    };

    try {
        const command = new ResendConfirmationCodeCommand(params);
        const response = await client.send(command);
        return {
            statusCode: 200,
            headers: {
                    "Access-Control-Allow-Origin" : "*", // Required for CORS support to work
                    "Access-Control-Allow-Credentials" : true, // Required for cookies, authorization headers with HTTPS
                    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
                },
            body: JSON.stringify({ message: response })
        }
    } catch (error) {
        console.error(error);
        return {
            statusCode: 500,
                headers: {
                    "Access-Control-Allow-Origin" : "*", // Required for CORS support to work
                    "Access-Control-Allow-Credentials" : true, // Required for cookies, authorization headers with HTTPS
                    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
                },
                body: JSON.stringify({
                    statusCode: 500,
                    error: 'Internal Server Error',
                    internalError: JSON.stringify({ error: error.message }),
                }),
        }
    }
}

export { resend_code as handler };
