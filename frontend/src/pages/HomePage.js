import React, { useState, useContext } from 'react';

import AuthContext from '../context/AuthContext';
import PhysicianOrderList from '../components/PhysicianOrderList';
import AssignedOperations from '../components/AssignedOperations';
import OrderList from '../components/OrderList';

const HomePage = () => {
  let {userGroupToString, user} = useContext(AuthContext);
  const [userGroup, setUserGroup] = useState(userGroupToString(user?.group));
  
  if (userGroup === 'Врач') {
    return (
      <PhysicianOrderList />
    )
  }
  else if (userGroup.search(/^Техник/) !== -1) {
    return (
      <AssignedOperations />
    )
  }
  
  return (
    <OrderList />
  );
}

export default HomePage;
