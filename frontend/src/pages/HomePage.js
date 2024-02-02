import React, { useState, useContext } from 'react';

import AuthContext from '../context/AuthContext';
import PhysicianOrderList from '../components/PhysicianOrderList';

const HomePage = () => {
  let { user, authTokens, userGroupToString } = useContext(AuthContext);
  const [ userGroup, setUserGroup ] = useState(userGroupToString());


  return (
    <div>
      { userGroup === "Врач" ? (
        <PhysicianOrderList />
      ) : (
        <></>
      )}
    </div>
  )
}

export default HomePage;
