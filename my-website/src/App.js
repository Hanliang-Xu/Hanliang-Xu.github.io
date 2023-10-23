import React from 'react';
import { BrowserRouter as Router, Route, Link, Routes } from 'react-router-dom';
import Home from './pages/Home';
import Projects from './pages/Projects';
import Experience from './pages/Experience';
import Awards from './pages/Awards';
import { AppBar, Tabs, Tab, ThemeProvider, createTheme } from '@mui/material';
import './styles.css';

const theme = createTheme({
  palette: {
    primary: {
      main: '#0D47A1',
    },
    secondary: {
      main: '#FFC107',
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
          <AppBar
            position="static"
            sx={{
              backgroundColor: theme.palette.primary.main,
              height: '5rem'
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'flex-end', alignItems: 'center', width: '100%', height: '100%' }}>
              <Tabs 
                sx={{ 
                  '& .MuiTab-root': {
                    fontSize: '2rem',
                    fontFamily: theme.typography.fontFamily,
                    minWidth: 'auto',
                    padding: '0 1rem',
                    color: theme.palette.secondary.main,
                    '&:hover': {
                      color: theme.palette.secondary.dark,
                    },
                    '&.Mui-selected': {
                      color: theme.palette.primary.main,
                    }
                  } 
                }}
              >
                <Tab label="Home" component={Link} to="/" />
                <Tab label="Experience" component={Link} to="/experience" />
                <Tab label="Projects" component={Link} to="/projects" />
                <Tab label="Awards" component={Link} to="/awards" />
              </Tabs>
            </div>
          </AppBar>

          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/projects" element={<Projects />} />
            <Route path="/experience" element={<Experience />} />
            <Route path="/awards" element={<Awards />} />
          </Routes>
        </div>
      </ThemeProvider>
    </Router>
  );
}

export default App;