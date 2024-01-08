import React, { useState, useEffect, useContext } from 'react';
import axios from 'axios';

import AuthContext from '../context/AuthContext';

const HomePage = () => {
  let { user } = useContext(AuthContext);

  return (
    <div>
      { user && <p>Your email is {user.email}</p> }
    </div>
  )
}

export default HomePage;
