import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';
import reportWebVitals from './reportWebVitals';
import { BrowserRouter } from 'react-router-dom';
import axios from 'axios';
import { ThemeProvider, createTheme } from "@mui/material/styles";

import "bootstrap/dist/css/bootstrap.min.css";

axios.defaults.baseURL = process.env.REACT_APP_BASE_URL;

axios.interceptors.request.use((config) => {
  const authTokens = JSON.parse(localStorage.getItem('authTokens'));

  if (authTokens) {
    config.headers['Authorization'] = 'Bearer ' + String(authTokens?.access);
  }

  return config;
});

// const theme = createTheme({
//   palette: {
//     primary: {
//       main: "#000000"
//     },
//     secondary: {
//       main: "#000000"
//     },
//     success: {
//       main: "#000000"
//     },
//     info: {
//       main: "#000000"
//     },
//   }
// });

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <BrowserRouter>
    <App />
  </BrowserRouter>
);

// const root = ReactDOM.createRoot(document.getElementById('root'));
// root.render(
//   <ThemeProvider theme={theme}>
//     <BrowserRouter>
//       <App />
//     </BrowserRouter>
//   </ThemeProvider>
// );

reportWebVitals();
