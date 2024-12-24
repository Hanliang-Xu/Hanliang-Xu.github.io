import React, {useState} from 'react';
import {Box, Button, Typography} from '@mui/material';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableRow from '@mui/material/TableRow';
import Paper from '@mui/material/Paper';

//const API_BASE_URL = 'https://asl-parameters-generator-a94b4af439d2.herokuapp.com/';
//const API_BASE_URL = 'http://127.0.0.1:8000';

const API_BASE_URL = 'https://rock-sublime-428805-r3.uc.r.appspot.com';

function JSONUpload() {
    const [majorErrorReport, setMajorErrorReport] = useState(null);
    const [majorErrorReportConcise, setMajorErrorReportConcise] = useState(null);
    const [majorErrorReportConciseText, setMajorErrorReportConciseText] = useState(null);
    const [errorReport, setErrorReport] = useState(null);
    const [errorReportConcise, setErrorReportConcise] = useState(null);
    const [errorReportConciseText, setErrorReportConciseText] = useState(null);
    const [warningReport, setWarningReport] = useState(null);
    const [warningReportConcise, setWarningReportConcise] = useState(null);
    const [warningReportConciseText, setWarningReportConciseText] = useState(null);
    const [report, setReport] = useState(null);
    const [extendedReport, setExtendedReport] = useState(null);

    const [uploadError, setUploadError] = useState(null);
    const [inconsistencies, setInconsistencies] = useState(null);
    const [majorInconsistencies, setMajorInconsistencies] = useState(null);
    const [warningInconsistencies, setWarningInconsistencies] = useState(null);
    const [m0ConciseError, setM0ConciseError] = useState(null);
    const [m0ConciseWarning, setM0ConciseWarning] = useState(null);

    const [aslParameters, setAslParameters] = useState(null);
    const [m0Parameters, setM0Parameters] = useState(null);
    const [extendedParameters, setExtendedParameters] = useState(null);

    const [showMajorConcise, setShowMajorConcise] = useState(true);
    const [showErrorConcise, setShowErrorConcise] = useState(true);
    const [showWarningConcise, setShowWarningConcise] = useState(true);
    const [copySuccess, setCopySuccess] = useState('');


    const handleDirectoryUpload = async (event) => {
        const files = Array.from(event.target.files);


        // Function to find relevant JSON and TSV files
        const findRelevantFiles = (items) => {
            const relevantFiles = [];

            // Helper function to find file by name in the given folder
            const findFileInFolder = (folderItems, fileName) => {
                return folderItems.find(item => item.name.endsWith(fileName));
            };

            for (const item of items) {
                const relativePath = item.webkitRelativePath || item.relativePath;
                const pathParts = relativePath.split('/');
                const parentFolder = pathParts[pathParts.length - 2];

                if (parentFolder === 'perf' && item.name.endsWith('asl.json')) {
                    relevantFiles.push(item);
                    // Extract the base name before '_asl.json'
                    const baseName = item.name.replace('_asl.json', '');

                    // Find related files in the same folder
                    const folderItems = items.filter(i => i.webkitRelativePath.startsWith(relativePath.replace(/[^/]+$/, '')));

                    // Check if the base name matches the '_run-*' pattern
                    const runPatternMatch = baseName.match(/_run-\d+$/);

                    if (runPatternMatch) {
                        const m0scanFile = findFileInFolder(folderItems, `${baseName}_m0scan.json`);
                        const aslcontextFile = findFileInFolder(folderItems, `${baseName}_aslcontext.tsv`);

                        if (m0scanFile) {
                            relevantFiles.push(m0scanFile); // Push _run-*_m0scan.json if it exists
                        }
                        if (aslcontextFile) {
                            relevantFiles.push(aslcontextFile); // Push _run-*_aslcontext.tsv if it exists
                        }

                    } else {
                        const m0scanFile = findFileInFolder(folderItems, 'm0scan.json');
                        const aslcontextFile = findFileInFolder(folderItems, 'aslcontext.tsv');

                        if (m0scanFile) {
                            relevantFiles.push(m0scanFile); // Push m0scan.json if it exists
                        }
                        if (aslcontextFile) {
                            relevantFiles.push(aslcontextFile); // Push aslcontext.tsv if it exists
                        }
                    }
                }
            }

            return relevantFiles;
        };

        // Function to find the .nii or .nii.gz file in the perf folder
        const findNiiFile = (items) => {
            for (const item of items) {
                const relativePath = item.webkitRelativePath || item.relativePath;
                const pathParts = relativePath.split('/');
                const parentFolder = pathParts[pathParts.length - 2];

                if (parentFolder === 'perf' &&
                    (item.name.endsWith('asl.nii.gz') || item.name.endsWith('asl.nii'))) {
                    return item; // Return the first found .nii.gz or .nii file
                }
            }
            return null;
        };

        // Main logic
        const niiFile = findNiiFile(files);

        const relevantFiles = findRelevantFiles(files);
        const formData = new FormData();
        formData.append('nii-file', niiFile);

        // Append all relevant files to formData
        files.forEach(file => {
            if (file.name.endsWith('.dcm')) {
                formData.append('dcm-files', file);
            }
        });

        relevantFiles.forEach(file => {
            formData.append('files', file);
            formData.append('filenames', file.name);
        })


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
            setMajorErrorReportConciseText(result.major_errors_concise_text || null);
            setErrorReport(Object.keys(result.errors).length ? result.errors : null);
            setErrorReportConcise(Object.keys(result.errors_concise).length ? result.errors_concise : null);
            setErrorReportConciseText(result.errors_concise_text || null);
            setWarningReport(Object.keys(result.warnings).length ? result.warnings : null);
            setWarningReportConcise(Object.keys(result.warnings_concise).length ? result.warnings_concise : null);
            setWarningReportConciseText(result.warnings_concise_text || null);
            setReport(result.basic_report || null);
            setExtendedReport(result.extended_report || null);
            setInconsistencies(result.inconsistencies || null);
            setMajorInconsistencies(result.major_inconsistencies || null);
            setWarningInconsistencies(result.warning_inconsistencies || null);
            setM0ConciseError(result.m0_concise_error || null);
            setM0ConciseWarning(result.m0_concise_warning || null);
            setAslParameters(result.asl_parameters || null)
            setM0Parameters(result.m0_parameters || null)
            setExtendedParameters(result.extended_parameters || null)

            setUploadError(null);
        } catch (error) {
            console.error('Error:', error);
            setUploadError(error.message);
        }
    };

    const handleDownloadReport = (type) => {
        window.location.href = `${API_BASE_URL}/download?type=${type}`;
    };


    const renderCombinedParameterTable = (aslParameters = [], m0Parameters = [], extendedParameters = []) => {
        if (!extendedReport) {
            return null; // Don't render the table if conditions aren't met
        }

        const combinedParameters = [
            ...(Array.isArray(aslParameters) ? aslParameters : []),
            ...(Array.isArray(m0Parameters) ? m0Parameters : []),
            ...(Array.isArray(extendedParameters) ? extendedParameters : [])
        ];

        return (
            <TableContainer
                component={Paper}
                sx={{
                    mt: 4,
                    width: '95%',
                    marginLeft: '18px',  // Left margin
                    marginRight: '18px'  // Right margin
                }}
            >
                <Typography variant="h6" sx={{ mt: 2, mb: 1, ml: 3 }}>Combined Parameters</Typography>
                <Table aria-label="combined parameter table">
                    <TableBody>
                        {combinedParameters.map((row, index) => (
                            <TableRow key={index}>
                                <TableCell
                                    component="th"
                                    scope="row"
                                    sx={{
                                        borderBottom: '1px solid rgba(224, 224, 224, 1)',
                                        padding: '8px 16px',  // Padding to add space between text and cell border
                                        whiteSpace: 'nowrap', // Prevents text from wrapping
                                        verticalAlign: 'top',  // Aligns text to the top
                                        paddingLeft: '48px'
                                    }}
                                >
                                    {row[0]}
                                </TableCell>
                                <TableCell
                                    align="left"
                                    sx={{
                                        borderBottom: '1px solid rgba(224, 224, 224, 1)',
                                        padding: '8px 16px',  // Padding to add space between text and cell border
                                        width: '100%' // Ensures the column stretches across the remaining width
                                    }}
                                >
                                    {row[1]}
                                </TableCell>
                            </TableRow>
                        ))}
                    </TableBody>
                </Table>
            </TableContainer>
        );
    };

    const renderReportSection = (
        title,
        fullReport,
        conciseReport,
        conciseText,
        showConcise,
        setShowConcise,
        type,
        m0Concise = null
    ) => (

        <Box mt={2} sx={{
            border: `1px solid ${type === 'major_errors' ? 'darkred' : type === 'errors' ? 'red' : 'orange'}`,
            padding: '10px',
            borderRadius: '8px',
            backgroundColor: type === 'major_errors' ? '#ffe6e6' : type === 'errors' ? '#ffe6e6' : '#fff4e6'
        }}>
            <Typography variant="h6"
                        sx={{color: type === 'major_errors' ? 'darkred' : type === 'errors' ? 'red' : 'orange'}}>{title}:</Typography>
            {showConcise && (
                <Box mt={2}>
                    <pre style={{whiteSpace: 'pre-wrap', wordWrap: 'break-word'}}>
                        {type === 'major_errors' ? majorInconsistencies :
                            type === 'errors' ? inconsistencies :
                                type === 'warnings' ? warningInconsistencies : ''}
                    </pre>
                </Box>
            )}

            <pre style={{whiteSpace: 'pre-wrap', wordWrap: 'break-word'}}>
                {showConcise ? (
                    conciseText || conciseReport || m0Concise ? (
                        <>
                            {conciseText ? conciseText : (conciseReport ? JSON.stringify(conciseReport, null, 2) : "")}
                            {conciseText || conciseReport ? (m0Concise && `\n${m0Concise}`) : m0Concise}
                        </>
                    ) : ""
                ) : fullReport ? (
                    JSON.stringify(fullReport, null, 2)
                ) : ""}
            </pre>
            <Button variant="contained" color="error"
                    onClick={() => handleDownloadReport(type)}>
                Download {type.replace('_', ' ')} Report
            </Button>
            <Button variant="contained" color="secondary"
                    onClick={() => setShowConcise(!showConcise)}>
                {showConcise ? "Show Full Report" : "Show Concise Report"}
            </Button>
        </Box>
    );


    const copyToClipboard = () => {
        navigator.clipboard.writeText(report)
            .then(() => {
                setCopySuccess('Report copied to clipboard!');
                setTimeout(() => setCopySuccess(''), 2000);  // Clear the success message after 2 seconds
            })
            .catch(err => {
                setCopySuccess('Failed to copy!');
                console.error('Failed to copy: ', err);
            });
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
                OSIPI ASL Reporting Tool
            </Typography>

            <Box mt={4} p={2}
                 sx={{border: '1px solid #ccc', borderRadius: '8px', backgroundColor: '#f1f1f1'}}>
                <Typography variant="h5">User Manual</Typography>
                <Typography variant="body1" mt={2}>
                    This application allows you to generate an ASL parameter report to be copied
                    into the Methods section of paper. The program will validate the ASL datasets by
                    checking for inconsistencies, invalid values, and providing warnings for slight
                    variations. Please ensure that your dataset is organized according to the BIDS
                    standard before uploading. Here are some sample folders for you to download and
                    test:
                    https://drive.google.com/drive/folders/1NuG_ofLbaLYswNlBN2aRDkxLOucYFQfg?usp=sharing
                </Typography>
                <Typography variant="body1" mt={2}>
                    <strong>Steps:</strong>
                </Typography>
                <Typography variant="body1" mt={1}>
                    1. Click the "Choose Folder" button and select the BIDS folder containing your
                    ASL data.
                </Typography>
                <Typography variant="body1" mt={1}>
                    2. The application will process your files (including xxx_asl.json and
                    xxx_asl.nii or
                    xxx_asl.nii.gz) and display the results below.
                </Typography>
                <Typography variant="body1" mt={1}>
                    <strong>Note:</strong> The following specific checks and summaries will
                    be reported:
                </Typography>
                <Typography variant="body2" mt={1}>
                    - <strong>Inconsistency Check:</strong> Discrepancies between values across
                    different sessions, such as variations in PLD, labeling duration, echo time, and
                    voxel sizes.
                </Typography>
                <Typography variant="body2" mt={1}>
                    - <strong>Invalid Values Check:</strong> Identifying values that do not meet
                    predefined criteria, such as incorrect numeric ranges, boolean values, and
                    string values.
                </Typography>
                <Typography variant="body2" mt={1}>
                    - <strong>Slight Variation Warning:</strong> Highlighting values that might not
                    constitute a major error but are worth noting.
                </Typography>
                <Typography variant="body2" mt={1}>
                    - <strong>Generated Report:</strong> The software generates an ASL parameter
                    report to be included in the Methods section of paper. A suggested statement for
                    inclusion in the cover letter explaining that the relevant part of the Methods
                    section has been constructed according to standard format is also provided
                    (TODO).
                </Typography>

                <Typography variant="body1" mt={3}>
                    <strong>Acknowledgments</strong>
                </Typography>
                <Typography variant="body1" mt={1}>
                    This project has been developed under the mentorship and supervision of Jan Petr, David Thomas, and the OSIPI TF 4.1 ASL Lexicon. Their guidance and support have been invaluable throughout the development process.
                </Typography>
            </Box>

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
                majorErrorReportConciseText,
                showMajorConcise,
                setShowMajorConcise,
                'major_errors'
            )}
            {errorReport && renderReportSection(
                "ERRORS (major shortcomings which need to be addressed/acknowledged)",
                errorReport,
                errorReportConcise,
                errorReportConciseText,
                showErrorConcise,
                setShowErrorConcise,
                'errors',
                m0ConciseError,
            )}
            {warningReport && renderReportSection(
                "WARNINGS",
                warningReport,
                warningReportConcise,
                warningReportConciseText,
                showWarningConcise,
                setShowWarningConcise,
                'warnings',
                m0ConciseWarning
            )}
            {report && (
                <Box mt={2} sx={{
                    border: '1px solid blue',
                    padding: '10px',
                    borderRadius: '8px',
                    backgroundColor: '#e6f7ff',
                    maxHeight: '400px',
                    overflowY: 'auto',
                    position: 'relative'  // Add relative positioning for positioning the copy feedback
                }}>
                    <Typography variant="h6" sx={{color: 'blue'}}>Generated Report:</Typography>
                    <pre style={{whiteSpace: 'pre-wrap', wordWrap: 'break-word'}}>{report}</pre>
                    <Button variant="contained" color="primary"
                            onClick={() => handleDownloadReport('report')}>
                        Download Report
                    </Button>
                    <Button variant="contained" color="secondary" onClick={copyToClipboard}
                            sx={{ml: 2}}>
                        Copy Report
                    </Button>
                    {copySuccess && (
                        <Typography variant="subtitle1" sx={{
                            color: 'green',
                            position: 'absolute',  // Position the feedback message absolutely
                            top: 0,
                            right: 0,
                            mt: 1,
                            mr: 1,
                            backgroundColor: 'rgba(255, 255, 255, 0.8)',
                            padding: '5px',
                            borderRadius: '4px'
                        }}>
                            {copySuccess}
                        </Typography>
                    )}
                </Box>
            )}
            {extendedReport && (
                <Box mt={2} sx={{
                    border: '1px solid green',
                    padding: '10px',
                    borderRadius: '8px',
                    backgroundColor: '#e6ffe6',
                    maxHeight: '400px',
                    overflowY: 'auto',
                    position: 'relative'  // Add relative positioning for positioning the copy feedback
                }}>
                    <Typography variant="h6" sx={{color: 'green'}}>Extended Report:</Typography>
                    <pre style={{
                        whiteSpace: 'pre-wrap',
                        wordWrap: 'break-word'
                    }}>{extendedReport}</pre>
                    <Button variant="contained" color="primary"
                            onClick={() => handleDownloadReport('extended_report')}>
                        Download Extended Report
                    </Button>
                </Box>
            )}
            {renderCombinedParameterTable(aslParameters, m0Parameters, extendedParameters)}
        </Box>
    );
}

export default JSONUpload;