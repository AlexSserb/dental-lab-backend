import React from 'react';
import { Route, useNavigate } from 'react-router-dom';
import { useContext } from 'react';
import AuthContext from '../context/AuthContext';

const PrivateRoute = ({children, ...rest}) => {
  let { user } = useContext(AuthContext);
  let navigate = useNavigate();

  if (!user) {
    navigate('/');
  }
  return (
    <Route {...rest}>{children}</Route>
  )
}

export default PrivateRoute
