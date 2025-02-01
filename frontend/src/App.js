import React from 'react';
import { HashRouter as Router, Route, Routes } from 'react-router-dom';
import {createTheme, ThemeProvider} from '@mui/material';
import About from './pages/About';
import JSONUpload from './pages/JSONUpload';
import LandingPage from './pages/LandingPage';
import ImageBar from './pages/ImageBar';
import TopBar from './components/TopBar';
import './styles.css';

const theme = createTheme({
    palette: {
        primary: {
            main: '#0D47A1',
        },
        secondary: {
            main: '#FFC107',
        },
        text: {
            primary: '#000000',
        },
    },
    typography: {
        fontFamily: '"Roboto", sans-serif',
    },
});

function App() {
    return (
        <Router>
            <ThemeProvider theme={theme}>
                <div>
                    <TopBar/>

                    <div style={{paddingTop: '5rem'}}>
                        <Routes>
                            <Route path="/json-upload" element={<JSONUpload/>}/>
                            <Route
                                path="/"
                                element={
                                    <div>
                                        <LandingPage/>
                                        <section id="about" style={{
                                            padding: '100px 20px',
                                            marginBottom: '10px'
                                        }}>
                                            <About/>
                                        </section>
                                        <ImageBar/>
                                    </div>
                                }
                            />
                        </Routes>
                    </div>
                </div>
            </ThemeProvider>
        </Router>
    );
}

export default App;
