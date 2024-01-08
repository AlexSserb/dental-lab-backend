import './App.css';
import { Routes, Route } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'

import HomePage from './pages/HomePage'
import LoginPage from './pages/LoginPage'
import ResponsiveAppBar from './components/ResponsiveAppBar';
import RegisterPage from './pages/RegisterPage';
import ProfilePage from './pages/ProfilePage';
import OperationTypesPage from './pages/OperationTypesPage';


function App() {
  return (
    <div className="App">
      <AuthProvider>
        <ResponsiveAppBar/>
        <Routes>
          <Route exact path='/' element={<HomePage/>} />
          <Route path='/login' element={<LoginPage/>} />
          <Route path='/registration' element={<RegisterPage/>} />
          <Route path='/profile' element={<ProfilePage/>} />
          <Route path='/operations' element={<OperationTypesPage/>} />
        </Routes>
      </AuthProvider>
    </div>
  );
}

export default App;
