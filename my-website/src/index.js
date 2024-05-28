import React from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';
import './styles.css';

// Find the root element
const container = document.getElementById('root');

// Create a root
const root = createRoot(container);

// Initial render
root.render(
  <React.StrictMode>
    <link rel="stylesheet" href="https://fonts.googleapis.com/css?family=Roboto:300,400,500,700&display=swap" />
    <App />
  </React.StrictMode>
);