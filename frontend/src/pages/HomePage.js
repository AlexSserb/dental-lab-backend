import React, { useState, useEffect, useContext } from 'react';
import axios from 'axios';

import AuthContext from '../context/AuthContext';

const HomePage = () => {
  let [operTypes, setOperTypes] = useState([]);
  let { authTokens, logoutUser, user } = useContext(AuthContext);

  useEffect(() => {
    getOperTypes();
  }, [])

  let getOperTypes = async() => {
    if (!authTokens) return;
    await axios.get('/api/operation_types/', {
      headers: {
        'Authorization': 'Bearer ' + String(authTokens.access)
      }
    })
    .then(res => {
      setOperTypes(res.data);
    })
    .catch(err => {
      console.log(err);
      if (err.status === 401) {
        logoutUser();
      }
    });
  }

  return (
    <div>
      { user && <p>Hello {user.username}</p> }
      <table>
        <thead>
          <tr>
            <th>Название</th>
            <th>Время выполнения</th>
          </tr>
        </thead>
        <tbody>
        { operTypes.map(operType => (
          <tr key={operType.id}>
            <td>{ operType.name }</td>
            <td>{ operType.exec_time }</td>
          </tr>
        ))}
        </tbody>
      </table>
    </div>
  )
}

export default HomePage;
