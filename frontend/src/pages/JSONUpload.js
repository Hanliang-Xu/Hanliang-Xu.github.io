import React, {useState} from 'react';
import {Box, Button, Typography} from '@mui/material';

const API_BASE_URL = 'https://asl-parameters-generator-a94b4af439d2.herokuapp.com';

function JSONUpload() {
    const [majorErrorReport, setMajorErrorReport] = useState(null);
    const [errorReport, setErrorReport] = useState(null);
    const [warningReport, setWarningReport] = useState(null);
    const [report, setReport] = useState(null);
    const [uploadError, setUploadError] = useState(null);

    const handleDirectoryUpload = async (event) => {
        const files = event.target.files;
        const jsonFiles = [];

        // Recursively find all .json files directly under /perf/ and ending with "asl.json"
        const findJSONFiles = (items) => {
            for (const item of items) {
                const relativePath = item.webkitRelativePath || item.relativePath;
                const pathParts = relativePath.split('/');
                console.log(pathParts)

                // Check if the file is directly in the perf folder and ends with "asl.json"
                if (pathParts.length === 5 && pathParts[pathParts.length - 2] === 'perf' && item.name.endsWith('asl.json')) {
                    console.log("I GOT HERE")
                    jsonFiles.push(item);
                }
            }
        };

        findJSONFiles(files);

        if (jsonFiles.length === 0) {
            setUploadError("No JSON files found in the selected folder directly under the /perf/ directory ending with 'asl.json'.");
            return;
        }

        const formData = new FormData();
        jsonFiles.forEach(file => formData.append('json-files', file));

        try {
            const response = await fetch(`${API_BASE_URL}/upload`, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`Server error: ${response.status} - ${errorText}`);
            }

            const result = await response.json();
            setMajorErrorReport(Object.keys(result.major_errors).length ? result.major_errors : null);
            setErrorReport(Object.keys(result.errors).length ? result.errors : null);
            setWarningReport(Object.keys(result.warnings).length ? result.warnings : null);
            setReport(result.report || null);
            setUploadError(null);
        } catch (error) {
            console.error('Error:', error);
            setUploadError(error.message);
        }
    };

    const handleDownloadReport = (type) => {
        window.location.href = `${API_BASE_URL}/download?type=${type}`;
    };

    return (
        <Box
            my={4}
            sx={{
                width: '80%',
                margin: '0 auto',
                padding: '20px',
                border: '1px solid #ccc',
                borderRadius: '8px',
                backgroundColor: '#f9f9f9',
                marginTop: '40px'
            }}
        >
            <Typography variant="h4" gutterBottom>
                Select a BIDS folder to validate
            </Typography>
            <input
                type="file"
                webkitdirectory="true"
                onChange={handleDirectoryUpload}
                style={{margin: '20px 0'}}
            />
            {uploadError && (
                <Box mt={2} sx={{color: 'red'}}>
                    <Typography variant="h6">Upload Error:</Typography>
                    <pre>{uploadError}</pre>
                </Box>
            )}
            {majorErrorReport && (
                <Box mt={2} sx={{
                    border: '1px solid darkred',
                    padding: '10px',
                    borderRadius: '8px',
                    backgroundColor: '#ffe6e6'
                }}>
                    <Typography variant="h6" sx={{color: 'darkred'}}>MAJOR ERRORS (you cannot report
                        a sequence protocol without these):</Typography>
                    <pre>{JSON.stringify(majorErrorReport, null, 2)}</pre>
                    <Button variant="contained" color="error"
                            onClick={() => handleDownloadReport('major_errors')}>
                        Download Major Error Report
                    </Button>
                </Box>
            )}
            {errorReport && (
                <Box mt={2} sx={{
                    border: '1px solid red',
                    padding: '10px',
                    borderRadius: '8px',
                    backgroundColor: '#ffe6e6'
                }}>
                    <Typography variant="h6" sx={{color: 'red'}}>ERRORS (these are major
                        shortcomings, you need to provide those):</Typography>
                    <pre>{JSON.stringify(errorReport, null, 2)}</pre>
                    <Button variant="contained" color="error"
                            onClick={() => handleDownloadReport('errors')}>
                        Download Error Report
                    </Button>
                </Box>
            )}
            {!majorErrorReport && warningReport && (
                <Box mt={2} sx={{
                    border: '1px solid orange',
                    padding: '10px',
                    borderRadius: '8px',
                    backgroundColor: '#fff4e6'
                }}>
                    <Typography variant="h6" sx={{color: 'orange'}}>WARNINGS:</Typography>
                    <pre>{JSON.stringify(warningReport, null, 2)}</pre>
                    <Button variant="contained" color="warning"
                            onClick={() => handleDownloadReport('warnings')}>
                        Download Warning Report
                    </Button>
                </Box>
            )}
            {report && (
                <Box mt={2} sx={{
                    border: '1px solid blue',
                    padding: '10px',
                    borderRadius: '8px',
                    backgroundColor: '#e6f7ff'
                }}>
                    <Typography variant="h6" sx={{color: 'blue'}}>Generated Report:</Typography>
                    <pre>{report}</pre>
                    <Button variant="contained" color="primary"
                            onClick={() => handleDownloadReport('report')}>
                        Download Generated Report
                    </Button>
                </Box>
            )}
        </Box>
    );
}

export default JSONUpload;
