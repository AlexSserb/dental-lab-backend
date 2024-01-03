import './App.css';
import { Routes, Route } from 'react-router-dom'
import PrivateRoute from './utils/PrivateRoute.js'
import { AuthProvider } from './context/AuthContext'

import HomePage from './pages/HomePage'
import LoginPage from './pages/LoginPage'
import Header from './components/Header';

function App() {
  return (
    <div className="App">
      <AuthProvider>
        <Header/>
        <Routes>
          <Route exact path='/' element={<HomePage/>} />
          <Route path='/login' element={<LoginPage/>} />
        </Routes>
      </AuthProvider>
    </div>
  );
}

export default App;
