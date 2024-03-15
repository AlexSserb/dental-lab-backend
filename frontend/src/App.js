import './App.css';
import { Routes, Route } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'

import HomePage from './pages/HomePage'
import LoginPage from './pages/LoginPage'
import ResponsiveAppBar from './components/ResponsiveAppBar';
import RegisterPage from './pages/RegisterPage';
import ProfilePage from './pages/ProfilePage';
import CreateOrderForm from './components/CreateOrderForm';
import OperationsForProduct from './components/OperationsForProduct';

function App() {
  return (
    <div>
      <AuthProvider>
        <ResponsiveAppBar/>
        <Routes>
          <Route exact path='/' element={<HomePage/>} />
          <Route path='/login' element={<LoginPage/>} />
          <Route path='/registration' element={<RegisterPage/>} />
          <Route path='/profile' element={<ProfilePage/>} />
          <Route path='/create_order' element={<CreateOrderForm/>} />
          <Route path='/operations_for_product' element={<OperationsForProduct/>} />
        </Routes>
      </AuthProvider>
    </div>
  );
}

export default App;
