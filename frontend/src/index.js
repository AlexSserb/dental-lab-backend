import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';
import reportWebVitals from './reportWebVitals';
import { BrowserRouter } from 'react-router-dom';
import axios from 'axios';

import "bootstrap/dist/css/bootstrap.min.css";

axios.defaults.baseURL = process.env.REACT_APP_BASE_URL;

axios.interceptors.request.use((config) => {
  const authTokens = JSON.parse(localStorage.getItem('authTokens'));
  
  if (authTokens) {
    config.headers['Authorization'] = 'Bearer ' + String(authTokens?.access);
  }
  
  return config;
});


const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <BrowserRouter>
    <App />
  </BrowserRouter>
);

reportWebVitals();
