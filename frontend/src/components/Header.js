import React, { useContext } from 'react'
import { Link } from 'react-router-dom'
import AuthContext from '../context/AuthContext'

const Header = () => {
  let { user, logoutUser } = useContext(AuthContext);
  return (
    <div>
      <Link to="/">Home</Link>
      <span> | </span>
      { user ? (
        <Link onClick={logoutUser} to="/login">Logout</Link>
      ) : (
        <Link to="/login">Login</Link>
      )}

      { user && <p>Hello {user.username}</p> }
    </div>
  )
}

export default Header
