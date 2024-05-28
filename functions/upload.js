const { exec } = require('child_process');
const fs = require('fs');
const path = require('path');
const Busboy = require('busboy');

exports.handler = (event, context, callback) => {
    if (event.httpMethod !== 'POST') {
        return {
            statusCode: 405,
            body: 'Method Not Allowed',
        };
    }

    const busboy = new Busboy({ headers: event.headers });
    const uploadDir = '/tmp/uploads';

    if (!fs.existsSync(uploadDir)){
        fs.mkdirSync(uploadDir);
    }

    const filePath = path.join(uploadDir, 'upload.json');
    const fileStream = fs.createWriteStream(filePath);

    busboy.on('file', (fieldname, file, filename, encoding, mimetype) => {
        file.pipe(fileStream);
    });

    busboy.on('finish', () => {
        // Execute your Python script here
        exec(`python3 server.py ${filePath}`, (error, stdout, stderr) => {
            if (error) {
                console.error(`exec error: ${error}`);
                return callback(null, {
                    statusCode: 500,
                    body: JSON.stringify({ error: stderr }),
                });
            }

            const result = JSON.parse(stdout);
            return callback(null, {
                statusCode: 200,
                body: JSON.stringify(result),
            });
        });
    });

    busboy.write(event.body, event.isBase64Encoded ? 'base64' : 'binary');
    busboy.end();
};