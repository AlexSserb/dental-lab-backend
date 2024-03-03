import React, { useState, useContext } from 'react';

import AuthContext from '../context/AuthContext';
import PhysicianOrderList from '../components/PhysicianOrderList';
import AssignedOperations from '../components/AssignedOperations';

const HomePage = () => {
  let { userGroupToString, user } = useContext(AuthContext);
  const [ userGroup, setUserGroup ] = useState(userGroupToString(user.group));

  return (
    <div>
      { userGroup === "Врач" ? (
        <PhysicianOrderList />
      ) : (
        <AssignedOperations />
      )}
    </div>
  )
}

export default HomePage;
