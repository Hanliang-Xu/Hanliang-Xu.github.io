import React, {useState} from 'react';
import {Box, Button, Typography} from '@mui/material';

const API_BASE_URL = 'https://asl-parameters-generator-a94b4af439d2.herokuapp.com/';

function JSONUpload() {
    const [majorErrorReport, setMajorErrorReport] = useState(null);
    const [majorErrorReportConcise, setMajorErrorReportConcise] = useState(null);
    const [errorReport, setErrorReport] = useState(null);
    const [errorReportConcise, setErrorReportConcise] = useState(null);
    const [warningReport, setWarningReport] = useState(null);
    const [warningReportConcise, setWarningReportConcise] = useState(null);
    const [report, setReport] = useState(null);
    const [uploadError, setUploadError] = useState(null);

    const [showMajorConcise, setShowMajorConcise] = useState(true);
    const [showErrorConcise, setShowErrorConcise] = useState(true);
    const [showWarningConcise, setShowWarningConcise] = useState(true);

    const handleDirectoryUpload = async (event) => {
        const files = event.target.files;
        const jsonFiles = [];

        const findJSONFiles = (items) => {
            for (const item of items) {
                const relativePath = item.webkitRelativePath || item.relativePath;
                const pathParts = relativePath.split('/');

                if (pathParts.length === 5 && pathParts[pathParts.length - 2] === 'perf' &&
                    (item.name.endsWith('asl.json'))) {
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
        jsonFiles.forEach(file => {
            formData.append('json-files', file);
            formData.append('filenames', file.name);
        });

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
            setMajorErrorReportConcise(Object.keys(result.major_errors_concise).length ? result.major_errors_concise : null);
            setErrorReport(Object.keys(result.errors).length ? result.errors : null);
            setErrorReportConcise(Object.keys(result.errors_concise).length ? result.errors_concise : null);
            setWarningReport(Object.keys(result.warnings).length ? result.warnings : null);
            setWarningReportConcise(Object.keys(result.warnings_concise).length ? result.warnings_concise : null);
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

    const renderReportSection = (title, fullReport, conciseReport, showConcise, setShowConcise, type) => (
        <Box mt={2} sx={{
            border: `1px solid ${type === 'major_errors' ? 'darkred' : type === 'errors' ? 'red' : 'orange'}`,
            padding: '10px',
            borderRadius: '8px',
            backgroundColor: type === 'major_errors' ? '#ffe6e6' : type === 'errors' ? '#ffe6e6' : '#fff4e6'
        }}>
            <Typography variant="h6"
                        sx={{color: type === 'major_errors' ? 'darkred' : type === 'errors' ? 'red' : 'orange'}}>{title}:</Typography>
            <pre style={{
                whiteSpace: 'pre-wrap',
                wordWrap: 'break-word'
            }}>{showConcise ? JSON.stringify(conciseReport, null, 2) : JSON.stringify(fullReport, null, 2)}</pre>
            {type !== 'warnings' && (
                <Button variant="contained" color="error"
                        onClick={() => handleDownloadReport(type)}>
                    Download {title} Report
                </Button>
            )}
            <Button variant="contained" color="secondary"
                    onClick={() => setShowConcise(!showConcise)}>
                {showConcise ? "Show Full Report" : "Show Concise Report"}
            </Button>
        </Box>
    );

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
            {majorErrorReport && renderReportSection(
                "MAJOR ERRORS (you cannot report a sequence protocol without these)",
                majorErrorReport,
                majorErrorReportConcise,
                showMajorConcise,
                setShowMajorConcise,
                'major_errors'
            )}
            {errorReport && renderReportSection(
                "ERRORS (these are major shortcomings, you need to provide those)",
                errorReport,
                errorReportConcise,
                showErrorConcise,
                setShowErrorConcise,
                'errors'
            )}
            {!majorErrorReport && warningReport && renderReportSection(
                "WARNINGS",
                warningReport,
                warningReportConcise,
                showWarningConcise,
                setShowWarningConcise,
                'warnings'
            )}
            {report && (
                <Box mt={2} sx={{
                    border: '1px solid blue',
                    padding: '10px',
                    borderRadius: '8px',
                    backgroundColor: '#e6f7ff',
                    maxHeight: '400px',
                    overflowY: 'auto'
                }}>
                    <Typography variant="h6" sx={{color: 'blue'}}>Generated Report:</Typography>
                    <pre style={{whiteSpace: 'pre-wrap', wordWrap: 'break-word'}}>{report}</pre>
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
