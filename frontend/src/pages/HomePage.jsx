import React, { useContext } from 'react';

import AuthContext from '../context/AuthContext';
import PhysicianOrderList from '../components/PhysicianOrderList';
import AssignedOperations from '../components/AssignedOperations';
import OrderList from '../components/OrderList';
import { isPhysician, isRegularTech } from '../utils/Permissions';

const HomePage = () => {
  const { user } = useContext(AuthContext);
  
  if (isPhysician(user)) {
    return <PhysicianOrderList />;
  }
  if (isRegularTech(user)) {
    return <AssignedOperations />;
  }
  
  return <OrderList />;
}

export default HomePage;
