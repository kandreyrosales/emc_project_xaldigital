import { CognitoIdentityProviderClient, ConfirmForgotPasswordCommand } from "@aws-sdk/client-cognito-identity-provider";
import crypto from 'crypto';

const client = new CognitoIdentityProviderClient({ region: "us-east-1" });

function generateSecretHash(username, clientId, clientSecret) {
    return crypto.createHmac('SHA256', clientSecret)
                 .update(username + clientId)
                 .digest('base64');
}

async function forgotPassword(event) {
    const parsedData = JSON.parse(event.body);
    const username = parsedData.username;
    const confirmation_code = parsedData.confirmation_code;
    const password = parsedData.password;

    const clientId = process.env.clientId;
    const clientSecret = process.env.clientSecret;

    const secretHash = generateSecretHash(username, clientId, clientSecret);

    const params = {
        ClientId: clientId,
        SecretHash: secretHash,
        Username: username,
        ConfirmationCode: confirmation_code,
        Password: password
    };

    try {
        const command = new ConfirmForgotPasswordCommand(params);
        const response = await client.send(command);
        return {
            statusCode: 200,
            body: JSON.stringify({ message: response })
        };
    } catch (error) {
        console.error(error);
        return {
            statusCode: 500,
            body: JSON.stringify({ error: error.message })
        };
    }
}

export { forgotPassword as handler };
