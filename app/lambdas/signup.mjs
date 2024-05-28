import { CognitoIdentityProviderClient, SignUpCommand } from "@aws-sdk/client-cognito-identity-provider";
import crypto from 'crypto';

const client = new CognitoIdentityProviderClient({ region: "us-east-1" });

function generateSecretHash(username, clientId, clientSecret) {
    return crypto.createHmac('SHA256', clientSecret)
                 .update(username + clientId)
                 .digest('base64');
}
async function signUp(event) {
    const parsedData = JSON.parse(event.body);

    const email = parsedData.email;
    const password = parsedData.password;
    const fullname = parsedData.fullname;
    const medical_specialty = parsedData.medical_specialty;
    const professional_id = parsedData.professional_id;
    const residence_age = parsedData.residence_age;
    const hospital = parsedData.hospital;
    const doctor_name = parsedData.doctor_name;

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
                Name: "custom:fullname",
                Value: fullname
            },
            {
                Name: "custom:medical_specialty",
                Value: medical_specialty
            },
            {
                Name: "custom:professional_id",
                Value: professional_id
            },
            {
                Name: "custom:residence_age",
                Value: residence_age
            },
            {
                Name: "custom:hospital",
                Value: hospital
            },
            {
                Name: "custom:doctor_name",
                Value: doctor_name
            }
        ]
    };

    const command = new SignUpCommand(params);

    try {
        const data = await client.send(command);
        console.log(data);
        return {
            statusCode: 200,
            headers: {
                    "Access-Control-Allow-Origin" : "*", // Required for CORS support to work
                    "Access-Control-Allow-Credentials" : true, // Required for cookies, authorization headers with HTTPS
                    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
                },
            body: JSON.stringify(data)
        }
    } catch (error) {
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
                    internalError: JSON.stringify(error),
                }),
        }
    }
}

export { signUp as handler };