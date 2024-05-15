import { CognitoIdentityProviderClient, InitiateAuthCommand } from "@aws-sdk/client-cognito-identity-provider";
import crypto from 'crypto';

const client = new CognitoIdentityProviderClient({ region: "us-east-1" });

function generateSecretHash(email, clientId, clientSecret) {
    return crypto.createHmac('SHA256', clientSecret)
                 .update(email + clientId)
                 .digest('base64');
}

async function signIn(event) {
    const { email, password } = JSON.parse(event.body);
    const clientId = process.env.CLIENT_ID;
    const clientSecret = process.env.CLIENT_SECRET;
    const secretHash = generateSecretHash(email, clientId, clientSecret);

    const params = {
        AuthFlow: "USER_PASSWORD_AUTH",
        ClientId: clientId,
        AuthParameters: {
            USERNAME: email,
            PASSWORD: password,
            SECRET_HASH: secretHash
        },
    };

    try {
        const command = new InitiateAuthCommand(params);
        const response = await client.send(command);
        console.log(response);
        return {
            statusCode: 200,
            body: JSON.stringify(response.AuthenticationResult)
        };
    } catch (error) {
        console.error(error);
        return {
            statusCode: 500,
            body: JSON.stringify({ error: error.message })
        };
    }
}

export { signIn as handler };
