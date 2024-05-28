const {exec} = require('child_process');
const fs = require('fs');
const path = require('path');
const Busboy = require('busboy');

exports.handler = async (event, context) => {
    if (event.httpMethod !== 'POST') {
        return {
            statusCode: 405,
            body: 'Method Not Allowed',
        };
    }

    const busboy = new Busboy({headers: event.headers});
    const uploadDir = '/tmp/uploads';

    if (!fs.existsSync(uploadDir)) {
        fs.mkdirSync(uploadDir);
    }

    const filePath = path.join(uploadDir, 'upload.json');
    const fileStream = fs.createWriteStream(filePath);

    return new Promise((resolve, reject) => {
        busboy.on('file', (fieldname, file, filename, encoding, mimetype) => {
            file.pipe(fileStream);
        });

        busboy.on('finish', () => {
            exec(`python3 server.py ${filePath}`, (error, stdout, stderr) => {
                if (error) {
                    console.error(`exec error: ${error}`);
                    reject({
                        statusCode: 500,
                        body: JSON.stringify({error: stderr}),
                    });
                    return;
                }

                try {
                    const result = JSON.parse(stdout);
                    resolve({
                        statusCode: 200,
                        body: JSON.stringify(result),
                    });
                } catch (parseError) {
                    console.error(`parse error: ${parseError}`);
                    reject({
                        statusCode: 500,
                        body: JSON.stringify({error: 'Failed to parse Python script output'}),
                    });
                }
            });
        });

        busboy.on('error', (error) => {
            console.error(`busboy error: ${error}`);
            reject({
                statusCode: 500,
                body: JSON.stringify({error: 'Failed to process file upload'}),
            });
        });

        busboy.end(Buffer.from(event.body, event.isBase64Encoded ? 'base64' : 'utf8'));
    });
};
