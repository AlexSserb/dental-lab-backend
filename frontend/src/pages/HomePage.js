import React, { useState, useEffect, useContext } from 'react';

import AuthContext from '../context/AuthContext';
import OrdersLayoutForDoctor from '../components/OrdersLayoutForDoctor';

const HomePage = () => {
  let { user, authTokens, userGroupToString } = useContext(AuthContext);
  const [ userGroup, setUserGroup ] = useState(userGroupToString());


  return (
    <div>
      { userGroup === "Врач" ? (
        <OrdersLayoutForDoctor />
      ) : (
        <></>
      )}
    </div>
  )
}

export default HomePage;
