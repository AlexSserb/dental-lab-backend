import React, { useContext, useEffect, useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom';

import AuthContext from "../context/AuthContext";
import profileService from "../servicies/ProfileService";

const ProfilePage = () => {
  const [ userData, setUserData ] = useState({});
  const { authTokens, userGroupToString } = useContext(AuthContext);
  const navigate = useNavigate();
  const { state } = useLocation();

  useEffect(() => {
    if (!authTokens || !authTokens.access) {
      navigate('/login');
      return;
    }
    profileService.getProfileData(state?.email)
      .then(res => {
        setUserData({
            email: res.data.email,
            firstName: res.data.first_name,
            lastName: res.data.last_name,
            group: userGroupToString(res.data.group),
            createdAt: res.data.created_at
        });
      })
      .catch(err => {
        console.log(err);
      });
  }, [authTokens, setUserData, navigate, userGroupToString])


  return (
    <div className="card card-container col-md-7 col-sm-60 mx-auto p-0 mt-5">
      <h3 className="text-success text-uppercase text-center mt-4">
        Профиль
      </h3>
      <div className='m-4'>
        <p>Фамилия: { userData.lastName }</p><hr/>
        <p>Имя: { userData.firstName }</p><hr/>
        <p>Почтовый адрес: { userData.email }</p><hr/>
        <p>Должность: { userData.group }</p><hr/>
        <p>Дата регистрации: { userData.createdAt }</p>
      </div>
    </div>
  )
}

export default ProfilePage;

