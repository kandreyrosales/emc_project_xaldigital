import { CognitoIdentityProviderClient, SignUpCommand } from "@aws-sdk/client-cognito-identity-provider";
import crypto from 'crypto';

const client = new CognitoIdentityProviderClient({ region: "us-east-1" });

function generateSecretHash(username, clientId, clientSecret) {
    return crypto.createHmac('SHA256', clientSecret)
                 .update(username + clientId)
                 .digest('base64');
}
async function signUp(event) {
    const body = JSON.parse(event.body);

    const { email, password, fullname, medical_specialty, professional_id, residence_age, hospital, doctor_name } = body;
    const clientId = process.env.clientId;
    const clientSecret = process.env.clientSecret;

    const secretHash = generateSecretHash(email, clientId, clientSecret);

    const params = {
        ClientId: clientId,
        SecretHash: secretHash,
        Username: email,
        Password: password,
        UserAttributes: [
            {
                Name: "email",
                Value: email
            },
            {
                Name: "fullname",
                Value: fullname
            },
            {
                Name: "medical_specialty",
                Value: medical_specialty
            },
            {
                Name: "professional_id",
                Value: professional_id
            },
            {
                Name: "residence_age",
                Value: residence_age
            },
            {
                Name: "hospital",
                Value: hospital
            },
            {
                Name: "doctor_name",
                Value: doctor_name
            },
        ]
    };

    const command = new SignUpCommand(params);

    try {
        const data = await client.send(command);
        console.log(data);
        return { status: 'SUCCESS', data: data };
    } catch (error) {
        console.error(error);
        return { status: 'ERROR', error: error };
    }
}

export { signUp as handler };