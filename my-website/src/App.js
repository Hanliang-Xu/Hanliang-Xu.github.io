import React from 'react';
import { BrowserRouter as Router, Route, Link, Routes } from 'react-router-dom';
import Home from './pages/Home';
import Projects from './pages/Projects';
import Experience from './pages/Experience';
import Awards from './pages/Awards';
import { AppBar, Tabs, Tab } from '@mui/material';

function App() {
  return (
    <Router>
      <div>
        <AppBar position="static">
          <Tabs>
            <Tab label="Home" component={Link} to="/" />
            <Tab label="Projects" component={Link} to="/projects" />
            <Tab label="Experience" component={Link} to="/experience" />
            <Tab label="Awards" component={Link} to="/awards" />
          </Tabs>
        </AppBar>

        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/projects" element={<Projects />} />
          <Route path="/experience" element={<Experience />} />
          <Route path="/awards" element={<Awards />} />
        </Routes>
        
      </div>
    </Router>
  );
}

export default App;