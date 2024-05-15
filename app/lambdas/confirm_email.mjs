import { CognitoIdentityProviderClient, ConfirmSignUpCommand } from "@aws-sdk/client-cognito-identity-provider";
import crypto from 'crypto';

function generateSecretHash(username, clientId, clientSecret) {
    return crypto.createHmac('SHA256', clientSecret)
                 .update(username + clientId)
                 .digest('base64');
}

const client = new CognitoIdentityProviderClient({ region: "us-east-1" });

async function confirmSignUp(event) {
    const { username, confirmationCode } = JSON.parse(event.body);
    const clientId = process.env.clientId;
    const clientSecret = process.env.clientSecret;

    const secretHash = generateSecretHash(username, clientId, clientSecret);

    const params = {
        ClientId: clientId,
        SecretHash: secretHash,
        Username: username,
        ConfirmationCode: confirmationCode
    };

    try {
        const command = new ConfirmSignUpCommand(params);
        await client.send(command);
        return {
            statusCode: 200,
            body: JSON.stringify({ message: "Signup confirmed successfully." })
        };
    } catch (error) {
        console.error(error);
        return {
            statusCode: 500,
            body: JSON.stringify({ error: error.message })
        };
    }
}

export { confirmSignUp as handler };
