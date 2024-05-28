const express = require('express');
const multer = require('multer');
const bodyParser = require('body-parser');
const fs = require('fs');
const path = require('path');
const { exec } = require('child_process');

const app = express();
const upload = multer({ dest: 'uploads/' });

app.use(bodyParser.json());
app.use(express.static(path.join(__dirname, 'build')));

app.post('/upload', upload.single('json-file'), (req, res) => {
    const file = req.file;

    validateJSON(file.path, (result) => {
        fs.writeFileSync('major_error_report.json', JSON.stringify(result.major_errors, null, 2));
        fs.writeFileSync('error_report.json', JSON.stringify(result.errors, null, 2));
        fs.writeFileSync('warning_report.json', JSON.stringify(result.warnings, null, 2));

        if (!result.major_errors) {
            fs.writeFileSync('report.txt', result.report);
        }

        res.json(result);
    });
});

app.get('/download', (req, res) => {
    const reportType = req.query.type;
    const reportFiles = {
        'major_errors': 'major_error_report.json',
        'errors': 'error_report.json',
        'warnings': 'warning_report.json',
        'report': 'report.txt'
    };

    const filePath = reportFiles[reportType];
    if (filePath) {
        res.download(filePath);
    } else {
        res.status(400).json({ error: 'Invalid report type' });
    }
});

function validateJSON(filepath, callback) {
    exec(`python3 json_validation.py ${filepath}`, (error, stdout, stderr) => {
        if (error) {
            console.error(`exec error: ${error}`);
            callback({ major_errors: { exec_error: stderr } });
            return;
        }
        const validationResult = JSON.parse(stdout);
        callback(validationResult);
    });
}

app.get('*', (req, res) => {
    res.sendFile(path.join(__dirname, 'build', 'index.html'));
});

const port = process.env.PORT || 5000;
app.listen(port, () => {
    console.log(`Server running on port ${port}`);
});
